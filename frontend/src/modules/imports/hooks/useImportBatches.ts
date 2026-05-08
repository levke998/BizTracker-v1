import { useEffect, useMemo, useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import {
  ensureImportBatchWeatherCoverage,
  getImportBatchWeatherRecommendation,
  getImportErrors,
  getImportRows,
  listImportBatches,
  mapImportBatchToFinancialTransactions,
  parseImportBatch,
  uploadImportFile,
} from "../api/importsApi";
import type {
  ImportBatch,
  ImportBatchWeatherRecommendation,
  ImportErrorPreview,
  ImportRowPreview,
  UploadImportFilePayload,
} from "../types/imports";
import type { BusinessUnit } from "../../masterData/types/masterData";

const DEFAULT_IMPORT_TYPES = [
  "pos_sales",
  "gourmand_pos_sales",
  "flow_pos_sales",
  "supplier_invoice",
  "ticket_sales",
  "bar_sales",
];

type BatchDetails = {
  rows: ImportRowPreview[];
  errors: ImportErrorPreview[];
};

type ImportCenterState = {
  businessUnits: BusinessUnit[];
  importTypes: string[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedImportType: string;
  setSelectedImportType: (value: string) => void;
  batches: ImportBatch[];
  isLoading: boolean;
  isUploading: boolean;
  parsingBatchId: string;
  mappingBatchId: string;
  weatherBackfillBatchId: string;
  expandedBatchIds: Record<string, boolean>;
  detailsByBatchId: Record<string, BatchDetails | undefined>;
  weatherByBatchId: Record<string, ImportBatchWeatherRecommendation | undefined>;
  detailLoadingByBatchId: Record<string, boolean>;
  detailErrorByBatchId: Record<string, string>;
  errorMessage: string;
  successMessage: string;
  uploadFile: (files: File[]) => Promise<void>;
  parseBatch: (batchId: string) => Promise<void>;
  mapBatch: (batchId: string) => Promise<void>;
  prepareWeatherForBatch: (batchId: string) => Promise<void>;
  toggleBatchDetails: (batchId: string) => Promise<void>;
  refresh: () => Promise<void>;
};

export function useImportBatches(): ImportCenterState {
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedImportType, setSelectedImportType] = useState(DEFAULT_IMPORT_TYPES[0]);
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [parsingBatchId, setParsingBatchId] = useState("");
  const [mappingBatchId, setMappingBatchId] = useState("");
  const [weatherBackfillBatchId, setWeatherBackfillBatchId] = useState("");
  const [expandedBatchIds, setExpandedBatchIds] = useState<Record<string, boolean>>({});
  const [detailsByBatchId, setDetailsByBatchId] = useState<
    Record<string, BatchDetails | undefined>
  >({});
  const [weatherByBatchId, setWeatherByBatchId] = useState<
    Record<string, ImportBatchWeatherRecommendation | undefined>
  >({});
  const [detailLoadingByBatchId, setDetailLoadingByBatchId] = useState<
    Record<string, boolean>
  >({});
  const [detailErrorByBatchId, setDetailErrorByBatchId] = useState<
    Record<string, string>
  >({});
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const importTypes = useMemo(() => DEFAULT_IMPORT_TYPES, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const items = await listBusinessUnits();
        if (cancelled) {
          return;
        }

        setBusinessUnits(items);
        setSelectedBusinessUnitId((current) => current || items[0]?.id || "");
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Nem sikerült betölteni a vállalkozásokat.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  async function refresh() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const items = await listImportBatches(selectedBusinessUnitId || undefined);
      setBatches(items);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült betölteni az import csomagokat.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function loadBatchDetails(batchId: string) {
    setDetailLoadingByBatchId((current) => ({ ...current, [batchId]: true }));
    setDetailErrorByBatchId((current) => ({ ...current, [batchId]: "" }));

    try {
      const [rows, errors, weather] = await Promise.all([
        getImportRows(batchId),
        getImportErrors(batchId),
        getImportBatchWeatherRecommendation(batchId),
      ]);

      setDetailsByBatchId((current) => ({
        ...current,
        [batchId]: { rows, errors },
      }));
      setWeatherByBatchId((current) => ({
        ...current,
        [batchId]: weather,
      }));
    } catch (error) {
      setDetailErrorByBatchId((current) => ({
        ...current,
        [batchId]:
          error instanceof Error
            ? error.message
            : "Nem sikerült betölteni az import részleteit.",
      }));
    } finally {
      setDetailLoadingByBatchId((current) => ({ ...current, [batchId]: false }));
    }
  }

  useEffect(() => {
    void refresh();
  }, [selectedBusinessUnitId]);

  async function uploadFile(files: File[]) {
    setSuccessMessage("");

    if (!selectedBusinessUnitId) {
      setErrorMessage("Először válassz vállalkozást.");
      return;
    }

    if (files.length === 0) {
      setErrorMessage("Válassz feltöltendő fájlt.");
      return;
    }

    if (
      ["gourmand_pos_sales", "flow_pos_sales"].includes(selectedImportType) &&
      files.length < 2
    ) {
      setErrorMessage(
        "A POS CSV csomaghoz töltsd fel együtt az összesítő és legalább egy tételes CSV fájlt.",
      );
      return;
    }

    setIsUploading(true);
    setErrorMessage("");

    try {
      const payload: UploadImportFilePayload = {
        businessUnitId: selectedBusinessUnitId,
        importType: selectedImportType,
        files,
      };
      await uploadImportFile(payload);
      setSuccessMessage(
        files.length > 1 ? "A fájlok feltöltése sikeres." : "A fájl feltöltése sikeres.",
      );
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült feltölteni az import fájlt.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function parseBatch(batchId: string) {
    setSuccessMessage("");
    setErrorMessage("");
    setParsingBatchId(batchId);

    try {
      await parseImportBatch(batchId);
      let automaticWeatherMessage = "";
      setSuccessMessage("Az import feldolgozása sikeres.");
      setDetailsByBatchId((current) => ({ ...current, [batchId]: undefined }));
      setWeatherByBatchId((current) => ({ ...current, [batchId]: undefined }));
      setDetailErrorByBatchId((current) => ({ ...current, [batchId]: "" }));
      try {
        const result = await ensureImportBatchWeatherCoverage(batchId);
        if (result.status === "backfilled" && result.created_count > 0) {
          automaticWeatherMessage = ` ${result.created_count} órányi időjárásadat automatikusan előkészítve.`;
        } else if (result.status === "covered") {
          automaticWeatherMessage = " Az import időjárásadatai már elő voltak készítve.";
        } else if (result.status === "skipped" && result.reason) {
          automaticWeatherMessage = ` Időjárás-előkészítés kihagyva: ${result.reason}`;
        }
        const updatedWeather = await getImportBatchWeatherRecommendation(batchId);
        setWeatherByBatchId((current) => ({
          ...current,
          [batchId]: updatedWeather,
        }));
      } catch {
        automaticWeatherMessage =
          " Az időjárás-előkészítés most nem futott le automatikusan, később újraindítható.";
      }
      setSuccessMessage(`Az import feldolgozása sikeres.${automaticWeatherMessage}`);
      await refresh();

      if (expandedBatchIds[batchId]) {
        await loadBatchDetails(batchId);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült feldolgozni az import csomagot.",
      );
    } finally {
      setParsingBatchId("");
    }
  }

  async function mapBatch(batchId: string) {
    setSuccessMessage("");
    setErrorMessage("");
    setMappingBatchId(batchId);

    try {
      const result = await mapImportBatchToFinancialTransactions(batchId);
      setSuccessMessage(
        result.created_transactions > 0
          ? `${result.created_transactions} pénzügyi tranzakció rögzítve.`
          : "Nem jött létre új pénzügyi tranzakció, a sorok már szerepeltek az adatbázisban.",
      );
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Nem sikerült pénzügyi tranzakciókat rögzíteni az importból.",
      );
    } finally {
      setMappingBatchId("");
    }
  }

  async function prepareWeatherForBatch(batchId: string) {
    setSuccessMessage("");
    setErrorMessage("");
    setWeatherBackfillBatchId(batchId);

    try {
      const result = await ensureImportBatchWeatherCoverage(batchId);
      setSuccessMessage(
        result.status === "backfilled" && result.created_count > 0
          ? `${result.created_count} órányi időjárási adat előkészítve.`
          : result.status === "covered"
            ? "Az import időszakához tartozó időjárási adatok már elő voltak készítve."
            : result.reason ?? "Ehhez az importhoz most nincs időjárás-előkészítés.",
      );
      const weather = await getImportBatchWeatherRecommendation(batchId);
      setWeatherByBatchId((current) => ({
        ...current,
        [batchId]: weather,
      }));
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Nem sikerült előkészíteni az időjárási adatokat.",
      );
    } finally {
      setWeatherBackfillBatchId("");
    }
  }

  async function toggleBatchDetails(batchId: string) {
    const isExpanded = expandedBatchIds[batchId] ?? false;
    if (isExpanded) {
      setExpandedBatchIds((current) => ({ ...current, [batchId]: false }));
      return;
    }

    setExpandedBatchIds((current) => ({ ...current, [batchId]: true }));

    if (!detailsByBatchId[batchId] && !detailLoadingByBatchId[batchId]) {
      await loadBatchDetails(batchId);
    }
  }

  return {
    businessUnits,
    importTypes,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedImportType,
    setSelectedImportType,
    batches,
    isLoading,
    isUploading,
    parsingBatchId,
    mappingBatchId,
    weatherBackfillBatchId,
    expandedBatchIds,
    detailsByBatchId,
    weatherByBatchId,
    detailLoadingByBatchId,
    detailErrorByBatchId,
    errorMessage,
    successMessage,
    uploadFile,
    parseBatch,
    mapBatch,
    prepareWeatherForBatch,
    toggleBatchDetails,
    refresh,
  };
}
