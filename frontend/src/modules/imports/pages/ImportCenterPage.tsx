import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { createCatalogProduct } from "../../catalog/api/catalogApi";
import {
  listCategories,
  listProducts,
  listUnitsOfMeasure,
  listVatRates,
} from "../../masterData/api/masterDataApi";
import type { Category, Product, UnitOfMeasure, VatRate } from "../../masterData/types/masterData";
import { ImportBatchCardsSection, ImportBatchLegacyTable } from "../components/ImportBatchPanels";
import { ImportHeaderControls } from "../components/ImportHeaderControls";
import { ImportUploadPanel } from "../components/ImportUploadPanel";
import {
  buildQuickProductForm,
  classifyGourmandFile,
  hasReadyGourmandPackage,
  summarizeBatches,
  type QuickProductForm,
  type SelectedImportFile,
} from "../components/importCenterView";
import {
  PosAliasReviewPanel,
  PosMappingReadinessPanel,
  PosMissingRecipePanel,
  PosQuickProductCreatePanel,
} from "../components/PosAliasPanels";
import { useImportBatches } from "../hooks/useImportBatches";
import { routes } from "../../../shared/constants/routes";
import {
  approvePosProductAliasMapping,
  bulkApprovePosProductAliasMappings,
  getPosMappingReadiness,
  listPosProductAliases,
  listPosProductsMissingRecipes,
} from "../../posIngestion/api/posIngestionApi";
import type {
  PosMappingReadiness,
  PosMissingRecipeProduct,
  PosProductAlias,
} from "../../posIngestion/types/posIngestion";
import type { ImportBatch } from "../types/imports";

export function ImportCenterPage() {
  const { setControls } = useTopbarControls();
  const [searchParams, setSearchParams] = useSearchParams();
  const {
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
  } = useImportBatches();
  const genericFileInputRef = useRef<HTMLInputElement | null>(null);
  const summaryFileInputRef = useRef<HTMLInputElement | null>(null);
  const detailFilesInputRef = useRef<HTMLInputElement | null>(null);
  const [genericFiles, setGenericFiles] = useState<File[]>([]);
  const [summaryFile, setSummaryFile] = useState<File | null>(null);
  const [detailFiles, setDetailFiles] = useState<File[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<SelectedImportFile[]>([]);
  const [registeredBatchIds, setRegisteredBatchIds] = useState<Record<string, boolean>>({});
  const [posAliases, setPosAliases] = useState<PosProductAlias[]>([]);
  const [posAliasProducts, setPosAliasProducts] = useState<Product[]>([]);
  const [catalogCategories, setCatalogCategories] = useState<Category[]>([]);
  const [unitsOfMeasure, setUnitsOfMeasure] = useState<UnitOfMeasure[]>([]);
  const [vatRates, setVatRates] = useState<VatRate[]>([]);
  const [posMappingReadiness, setPosMappingReadiness] = useState<PosMappingReadiness | null>(null);
  const [posMissingRecipeProducts, setPosMissingRecipeProducts] = useState<PosMissingRecipeProduct[]>([]);
  const [posAliasSelections, setPosAliasSelections] = useState<Record<string, string>>({});
  const [selectedPosAliasIds, setSelectedPosAliasIds] = useState<string[]>([]);
  const [isLoadingPosAliases, setIsLoadingPosAliases] = useState(false);
  const [approvingAliasId, setApprovingAliasId] = useState("");
  const [isBulkApprovingAliases, setIsBulkApprovingAliases] = useState(false);
  const [quickCreateAlias, setQuickCreateAlias] = useState<PosProductAlias | null>(null);
  const [quickProductForm, setQuickProductForm] = useState<QuickProductForm | null>(null);
  const [isCreatingQuickProduct, setIsCreatingQuickProduct] = useState(false);
  const [posAliasError, setPosAliasError] = useState("");
  const [posAliasSuccess, setPosAliasSuccess] = useState("");
  const requestedBusinessUnitId = searchParams.get("business_unit_id") ?? "";
  const requestedMappingStatus = searchParams.get("mapping_status");
  const mappingStatusFilter: "all" | "pending" | "mapped" =
    requestedMappingStatus === "all" ||
    requestedMappingStatus === "mapped" ||
    requestedMappingStatus === "pending"
      ? requestedMappingStatus
      : "pending";
  const mappingSearchTerm = searchParams.get("mapping_search") ?? "";
  const focusedProductId = searchParams.get("product_id") ?? "";
  const summary = summarizeBatches(batches);
  const isGourmandImport = ["gourmand_pos_sales", "flow_pos_sales"].includes(selectedImportType);
  const isGourmandPackageReady = !isGourmandImport || hasReadyGourmandPackage(selectedFiles);
  const hasSelectedFiles = selectedFiles.length > 0;

  function updateRouteParameter(name: string, value: string) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) {
          next.set(name, value);
        } else {
          next.delete(name);
        }
        return next;
      },
      { replace: true },
    );
  }

  function selectBusinessUnit(value: string) {
    setSelectedBusinessUnitId(value);
    updateRouteParameter("business_unit_id", value);
  }

  useEffect(() => {
    if (
      requestedBusinessUnitId &&
      requestedBusinessUnitId !== selectedBusinessUnitId &&
      businessUnits.some((unit) => unit.id === requestedBusinessUnitId)
    ) {
      setSelectedBusinessUnitId(requestedBusinessUnitId);
    }
  }, [
    businessUnits,
    requestedBusinessUnitId,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
  ]);

  useEffect(() => {
    if (
      selectedBusinessUnitId &&
      !businessUnits.some((unit) => unit.id === requestedBusinessUnitId)
    ) {
      updateRouteParameter("business_unit_id", selectedBusinessUnitId);
    }
  }, [businessUnits, requestedBusinessUnitId, selectedBusinessUnitId]);

  useEffect(() => {
    setControls(
      <ImportHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={selectBusinessUnit}
      />,
    );

    return () => setControls(null);
  }, [businessUnits, selectedBusinessUnitId, setControls]);

  useEffect(() => {
    const selectedUnit = businessUnits.find((unit) => unit.id === selectedBusinessUnitId);
    const nextImportType = selectedUnit?.code.toLocaleLowerCase("hu-HU").includes("flow")
      ? "flow_pos_sales"
      : "gourmand_pos_sales";

    if (importTypes.includes(nextImportType) && selectedImportType !== nextImportType) {
      setSelectedImportType(nextImportType);
    }
  }, [
    businessUnits,
    importTypes,
    selectedBusinessUnitId,
    selectedImportType,
    setSelectedImportType,
  ]);

  useEffect(() => {
    clearSelectedFileState();
    clearFileInputs();
  }, [selectedImportType]);

  useEffect(() => {
    setQuickCreateAlias(null);
    setQuickProductForm(null);
    void refreshPosAliasReview();
  }, [selectedBusinessUnitId]);

  async function refreshPosAliasReview() {
    if (!selectedBusinessUnitId) {
      setPosAliases([]);
      setPosAliasProducts([]);
      setCatalogCategories([]);
      setPosMappingReadiness(null);
      setPosMissingRecipeProducts([]);
      setPosAliasSelections({});
      setSelectedPosAliasIds([]);
      return;
    }

    setIsLoadingPosAliases(true);
    setPosAliasError("");
    try {
      const [
        aliases,
        products,
        categories,
        units,
        availableVatRates,
        missingRecipeProducts,
        mappingReadiness,
      ] = await Promise.all([
        listPosProductAliases(selectedBusinessUnitId),
        listProducts(selectedBusinessUnitId),
        listCategories(selectedBusinessUnitId),
        listUnitsOfMeasure(),
        listVatRates(),
        listPosProductsMissingRecipes(selectedBusinessUnitId),
        getPosMappingReadiness({ business_unit_id: selectedBusinessUnitId }),
      ]);
      setPosAliases(aliases);
      setPosAliasProducts(products);
      setCatalogCategories(categories);
      setUnitsOfMeasure(units);
      setVatRates(availableVatRates);
      setPosMissingRecipeProducts(missingRecipeProducts);
      setPosMappingReadiness(mappingReadiness);
      setPosAliasSelections((current) => {
        const next: Record<string, string> = {};
        aliases.forEach((alias) => {
          next[alias.id] = current[alias.id] ?? alias.product_id ?? "";
        });
        return next;
      });
      setSelectedPosAliasIds((current) => {
        const pendingAliasIds = new Set(
          aliases.filter((alias) => alias.status !== "mapped").map((alias) => alias.id),
        );
        return current.filter((aliasId) => pendingAliasIds.has(aliasId));
      });
    } catch {
      setPosAliases([]);
      setPosAliasProducts([]);
      setCatalogCategories([]);
      setPosMappingReadiness(null);
      setPosMissingRecipeProducts([]);
      setSelectedPosAliasIds([]);
      setPosAliasError("Nem sikerult betolteni a POS mapping listat.");
    } finally {
      setIsLoadingPosAliases(false);
    }
  }

  async function approveAlias(aliasId: string) {
    const productId = posAliasSelections[aliasId];
    if (!productId) {
      return;
    }

    setApprovingAliasId(aliasId);
    setPosAliasError("");
    setPosAliasSuccess("");
    try {
      await approvePosProductAliasMapping(aliasId, { product_id: productId });
      await refreshPosAliasReview();
      setPosAliasSuccess("POS termek mapping jovahagyva.");
    } catch (error) {
      setPosAliasError(
        error instanceof Error ? error.message : "Nem sikerult menteni a POS mappinget.",
      );
    } finally {
      setApprovingAliasId("");
    }
  }

  function startQuickProductCreate(alias: PosProductAlias) {
    setQuickCreateAlias(alias);
    setQuickProductForm(buildQuickProductForm(alias, unitsOfMeasure));
    setPosAliasError("");
    setPosAliasSuccess("");
  }

  function cancelQuickProductCreate() {
    setQuickCreateAlias(null);
    setQuickProductForm(null);
  }

  async function createProductAndApproveAlias() {
    if (!quickCreateAlias || !quickProductForm || !selectedBusinessUnitId || !quickProductForm.name.trim()) {
      return;
    }

    setIsCreatingQuickProduct(true);
    setPosAliasError("");
    setPosAliasSuccess("");
    try {
      const product = await createCatalogProduct({
        business_unit_id: selectedBusinessUnitId,
        category_id: quickProductForm.categoryId || null,
        sales_uom_id: quickProductForm.salesUomId || null,
        default_vat_rate_id: quickProductForm.vatRateId || null,
        sku: quickProductForm.sku.trim() || null,
        name: quickProductForm.name.trim(),
        product_type: quickProductForm.productType,
        sale_price_gross: quickProductForm.salePriceGross || null,
        default_unit_cost: null,
        currency: "HUF",
        is_active: true,
        recipe: null,
      });

      setPosAliasProducts((current) => [
        ...current.filter((item) => item.id !== product.id),
        {
          id: product.id,
          business_unit_id: product.business_unit_id,
          category_id: product.category_id,
          sales_uom_id: product.sales_uom_id,
          default_vat_rate_id: product.default_vat_rate_id,
          sku: product.sku,
          name: product.name,
          product_type: product.product_type,
          sale_price_gross: product.sale_price_gross,
          sale_price_last_seen_at: product.sale_price_last_seen_at,
          sale_price_source: product.sale_price_source,
          default_unit_cost: product.estimated_unit_cost,
          currency: product.currency,
          is_active: product.is_active,
        },
      ]);
      setPosAliasSelections((current) => ({
        ...current,
        [quickCreateAlias.id]: product.id,
      }));

      try {
        await approvePosProductAliasMapping(quickCreateAlias.id, { product_id: product.id });
      } catch (error) {
        setPosAliasError(
          error instanceof Error
            ? `A termek letrejott, de a mapping jovahagyasa sikertelen: ${error.message}`
            : "A termek letrejott, de a mapping jovahagyasa sikertelen.",
        );
        setQuickCreateAlias(null);
        setQuickProductForm(null);
        return;
      }

      setQuickCreateAlias(null);
      setQuickProductForm(null);
      await refreshPosAliasReview();
      setPosAliasSuccess("A belso termek letrejott es a POS mapping jovahagyva.");
    } catch (error) {
      setPosAliasError(
        error instanceof Error ? error.message : "Nem sikerult letrehozni a belso termeket.",
      );
    } finally {
      setIsCreatingQuickProduct(false);
    }
  }

  function toggleAliasSelection(aliasId: string) {
    setSelectedPosAliasIds((current) =>
      current.includes(aliasId)
        ? current.filter((currentAliasId) => currentAliasId !== aliasId)
        : [...current, aliasId],
    );
  }

  function toggleAllPendingAliases(pendingAliasIds: string[]) {
    const selectedAliasIdSet = new Set(selectedPosAliasIds);
    const allPendingSelected =
      pendingAliasIds.length > 0 &&
      pendingAliasIds.every((aliasId) => selectedAliasIdSet.has(aliasId));
    setSelectedPosAliasIds((current) => {
      if (allPendingSelected) {
        const pendingAliasIdSet = new Set(pendingAliasIds);
        return current.filter((aliasId) => !pendingAliasIdSet.has(aliasId));
      }
      return Array.from(new Set([...current, ...pendingAliasIds]));
    });
  }

  async function approveSelectedAliases() {
    const selectedAliasIdSet = new Set(selectedPosAliasIds);
    const mappings = posAliases
      .filter((alias) => alias.status !== "mapped" && selectedAliasIdSet.has(alias.id))
      .map((alias) => ({
        alias_id: alias.id,
        product_id: posAliasSelections[alias.id] ?? alias.product_id ?? "",
      }));

    if (mappings.length === 0 || mappings.some((mapping) => !mapping.product_id)) {
      setPosAliasError("Minden kijelolt POS aliashoz valassz belso termeket.");
      return;
    }

    setIsBulkApprovingAliases(true);
    setPosAliasError("");
    setPosAliasSuccess("");
    try {
      const result = await bulkApprovePosProductAliasMappings({ mappings });
      setSelectedPosAliasIds([]);
      await refreshPosAliasReview();
      setPosAliasSuccess(`${result.updated_count} POS termek mapping jovahagyva.`);
    } catch (error) {
      setPosAliasError(
        error instanceof Error
          ? error.message
          : "Nem sikerult tomegesen menteni a POS mappingeket.",
      );
    } finally {
      setIsBulkApprovingAliases(false);
    }
  }

  function clearSelectedFileState() {
    setGenericFiles([]);
    setSummaryFile(null);
    setDetailFiles([]);
    setSelectedFiles([]);
  }

  function clearFileInputs() {
    for (const inputRef of [genericFileInputRef, summaryFileInputRef, detailFilesInputRef]) {
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  async function registerBatch(batch: ImportBatch) {
    if (registeredBatchIds[batch.id]) {
      return;
    }

    setRegisteredBatchIds((current) => ({ ...current, [batch.id]: true }));
    try {
      if (batch.status === "uploaded") {
        await parseBatch(batch.id);
      }
      if (["uploaded", "parsed"].includes(batch.status)) {
        await mapBatch(batch.id);
      }
      await refreshPosAliasReview();
    } catch {
      setRegisteredBatchIds((current) => ({ ...current, [batch.id]: false }));
    } finally {
      setRegisteredBatchIds((current) => ({ ...current, [batch.id]: false }));
    }
  }

  async function refreshGenericFileSelection() {
    const files = Array.from(genericFileInputRef.current?.files ?? []);
    setGenericFiles(files);
    setSelectedFiles(files.map((file) => ({ name: file.name, kind: "unknown" })));
  }

  async function rebuildGourmandPreview(nextSummaryFile: File | null, nextDetailFiles: File[]) {
    const summaryItems = await Promise.all(
      (nextSummaryFile ? [nextSummaryFile] : []).map(async (file) => ({
        name: file.name,
        kind: classifyGourmandFile(await file.text(), file.name),
      })),
    );
    const detailItems = await Promise.all(
      nextDetailFiles.map(async (file) => ({
        name: file.name,
        kind: classifyGourmandFile(await file.text(), file.name),
      })),
    );
    setSelectedFiles([...summaryItems, ...detailItems]);
  }

  async function refreshSummaryFileSelection() {
    const file = Array.from(summaryFileInputRef.current?.files ?? [])[0] ?? null;
    setSummaryFile(file);
    await rebuildGourmandPreview(file, detailFiles);
  }

  async function appendDetailFileSelection() {
    const incomingFiles = Array.from(detailFilesInputRef.current?.files ?? []);
    const mergedFiles = [...detailFiles];
    for (const file of incomingFiles) {
      const alreadySelected = mergedFiles.some(
        (currentFile) =>
          currentFile.name === file.name &&
          currentFile.size === file.size &&
          currentFile.lastModified === file.lastModified,
      );
      if (!alreadySelected) {
        mergedFiles.push(file);
      }
    }
    setDetailFiles(mergedFiles);
    await rebuildGourmandPreview(summaryFile, mergedFiles);
    if (detailFilesInputRef.current) {
      detailFilesInputRef.current.value = "";
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const files = isGourmandImport
      ? [summaryFile, ...detailFiles].filter((file): file is File => file !== null)
      : genericFiles;
    await uploadFile(files);
    clearFileInputs();
    clearSelectedFileState();
  }

  return (
    <section className="page-section">
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {successMessage ? <p className="success-message">{successMessage}</p> : null}

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Import csomagok</span>
          <strong>{batches.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Feldolgozott sorok</span>
          <strong>
            {summary.parsedRows}/{summary.totalRows}
          </strong>
        </article>
        <article className="finance-summary-card">
          <span>Hibak</span>
          <strong>{summary.errorRows}</strong>
        </article>
      </div>

      {posAliasError ? <p className="error-message">{posAliasError}</p> : null}
      {posAliasSuccess ? <p className="success-message">{posAliasSuccess}</p> : null}

      <PosMappingReadinessPanel readiness={posMappingReadiness} isLoading={isLoadingPosAliases} />

      {quickCreateAlias && quickProductForm ? (
        <PosQuickProductCreatePanel
          alias={quickCreateAlias}
          form={quickProductForm}
          categories={catalogCategories}
          units={unitsOfMeasure}
          vatRates={vatRates}
          isSaving={isCreatingQuickProduct}
          onFormChange={setQuickProductForm}
          onCancel={cancelQuickProductCreate}
          onSubmit={() => void createProductAndApproveAlias()}
        />
      ) : null}

      <PosAliasReviewPanel
        aliases={posAliases}
        products={posAliasProducts}
        businessUnitId={selectedBusinessUnitId}
        isLoading={isLoadingPosAliases}
        approvingAliasId={approvingAliasId}
        isBulkApproving={isBulkApprovingAliases}
        statusFilter={mappingStatusFilter}
        searchTerm={mappingSearchTerm}
        focusedProductId={focusedProductId}
        selectedAliasIds={selectedPosAliasIds}
        selectedProductIds={posAliasSelections}
        onStatusFilterChange={(value) => updateRouteParameter("mapping_status", value)}
        onSearchTermChange={(value) => updateRouteParameter("mapping_search", value)}
        onClearProductFocus={() => updateRouteParameter("product_id", "")}
        onStartCreateProduct={startQuickProductCreate}
        onSelectProduct={(aliasId, productId) =>
          setPosAliasSelections((current) => ({ ...current, [aliasId]: productId }))
        }
        onToggleAlias={toggleAliasSelection}
        onToggleAllPending={toggleAllPendingAliases}
        onApprove={(aliasId) => void approveAlias(aliasId)}
        onApproveSelected={() => void approveSelectedAliases()}
      />

      <PosMissingRecipePanel items={posMissingRecipeProducts} isLoading={isLoadingPosAliases} />

      <ImportUploadPanel
        waitingBatches={summary.waitingBatches}
        isGourmandImport={isGourmandImport}
        isUploading={isUploading}
        selectedFiles={selectedFiles}
        summaryFile={summaryFile}
        detailFiles={detailFiles}
        genericFileInputRef={genericFileInputRef}
        summaryFileInputRef={summaryFileInputRef}
        detailFilesInputRef={detailFilesInputRef}
        hasSelectedFiles={hasSelectedFiles}
        isGourmandPackageReady={isGourmandPackageReady}
        onRefreshGenericFileSelection={() => void refreshGenericFileSelection()}
        onRefreshSummaryFileSelection={() => void refreshSummaryFileSelection()}
        onAppendDetailFileSelection={() => void appendDetailFileSelection()}
        onSubmit={handleSubmit}
      />

      <section className="panel">
        <ImportBatchCardsSection
          batches={batches}
          isLoading={isLoading}
          parsingBatchId={parsingBatchId}
          mappingBatchId={mappingBatchId}
          weatherBackfillBatchId={weatherBackfillBatchId}
          registeredBatchIds={registeredBatchIds}
          expandedBatchIds={expandedBatchIds}
          detailsByBatchId={detailsByBatchId}
          weatherByBatchId={weatherByBatchId}
          detailLoadingByBatchId={detailLoadingByBatchId}
          detailErrorByBatchId={detailErrorByBatchId}
          onRegisterBatch={(batch) => void registerBatch(batch)}
          onToggleBatchDetails={(batchId) => void toggleBatchDetails(batchId)}
          onMapBatch={(batchId) => void mapBatch(batchId)}
          onPrepareWeatherForBatch={(batchId) => void prepareWeatherForBatch(batchId)}
        />

        <ImportBatchLegacyTable
          batches={batches}
          isLoading={isLoading}
          parsingBatchId={parsingBatchId}
          mappingBatchId={mappingBatchId}
          weatherBackfillBatchId={weatherBackfillBatchId}
          registeredBatchIds={registeredBatchIds}
          expandedBatchIds={expandedBatchIds}
          detailsByBatchId={detailsByBatchId}
          weatherByBatchId={weatherByBatchId}
          detailLoadingByBatchId={detailLoadingByBatchId}
          detailErrorByBatchId={detailErrorByBatchId}
          onRegisterBatch={(batch) => void registerBatch(batch)}
          onToggleBatchDetails={(batchId) => void toggleBatchDetails(batchId)}
          onMapBatch={(batchId) => void mapBatch(batchId)}
          onPrepareWeatherForBatch={(batchId) => void prepareWeatherForBatch(batchId)}
        />
      </section>
    </section>
  );
}
