import { useEffect, useMemo, useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import {
  listImportBatches,
  parseImportBatch,
  uploadImportFile,
} from "../api/importsApi";
import type { ImportBatch, UploadImportFilePayload } from "../types/imports";
import type { BusinessUnit } from "../../masterData/types/masterData";

const DEFAULT_IMPORT_TYPES = [
  "pos_sales",
  "supplier_invoice",
  "ticket_sales",
  "bar_sales",
];

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
  errorMessage: string;
  successMessage: string;
  uploadFile: (file: File | null) => Promise<void>;
  parseBatch: (batchId: string) => Promise<void>;
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
            error instanceof Error ? error.message : "Failed to load business units.",
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
        error instanceof Error ? error.message : "Failed to load import batches.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, [selectedBusinessUnitId]);

  async function uploadFile(file: File | null) {
    setSuccessMessage("");

    if (!selectedBusinessUnitId) {
      setErrorMessage("Please select a business unit first.");
      return;
    }

    if (!file) {
      setErrorMessage("Please choose a file to upload.");
      return;
    }

    setIsUploading(true);
    setErrorMessage("");

    try {
      const payload: UploadImportFilePayload = {
        businessUnitId: selectedBusinessUnitId,
        importType: selectedImportType,
        file,
      };
      await uploadImportFile(payload);
      setSuccessMessage("File uploaded successfully.");
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to upload import file.",
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
      setSuccessMessage("Batch parsed successfully.");
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to parse import batch.",
      );
    } finally {
      setParsingBatchId("");
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
    errorMessage,
    successMessage,
    uploadFile,
    parseBatch,
    refresh,
  };
}
