import { useEffect, useState } from "react";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { useDashboard } from "../hooks/useDashboard";
import {
  DashboardHeaderControls,
  type DashboardViewMode,
} from "../components/DashboardHeaderControls";
import { DashboardKpiGrid } from "../components/DashboardKpiGrid";
import {
  DashboardFlowConsumptionControl,
  DashboardFlowFinancialEventImpact,
  DashboardFlowForecastEvent,
} from "../components/DashboardFlowCards";
import { DashboardRiskOverview } from "../components/DashboardRiskOverview";
import {
  DashboardTopProducts,
  DashboardTrafficHeatmap,
} from "../components/DashboardSalesCards";
import { DashboardTrendOverview } from "../components/DashboardTrendOverview";
import { DashboardBasketAnalysis } from "../components/DashboardBasketAnalysis";
import {
  DashboardBusinessFocus,
  DashboardBusinessSpecificAnalytics,
  DashboardMappingReadinessCard,
  DashboardVatReadinessCard,
} from "../components/DashboardBusinessCards";
import {
  DashboardCategoryMix,
  type MixMetric,
} from "../components/DashboardCategoryMix";
import {
  DashboardDailyForecast,
  DashboardWeatherImpact,
} from "../components/DashboardWeatherForecastCards";
import { DashboardStatisticsQuality } from "../components/DashboardStatisticsQuality";
import {
  DashboardExpenseBreakdown,
  DashboardExpenseDrilldown,
} from "../components/DashboardExpenseCards";
import { exportDashboardData } from "../components/dashboardView";

export function DashboardPage() {
  const { setControls } = useTopbarControls();
  const [categoryMixMetric, setCategoryMixMetric] = useState<MixMetric>("revenue");
  const [viewMode, setViewMode] = useState<DashboardViewMode>("overview");
  const isProfessional = viewMode === "professional";
  const {
    dashboard,
    mappingReadiness,
    basketPairs,
    basketReceipts,
    flowEvents,
    flowEventPerformances,
    topProducts,
    productDetails,
    productSourceRows,
    expenseDetails,
    expenseSource,
    drilldown,
    setDrilldown,
    selectedProduct,
    setSelectedProduct,
    selectedExpense,
    setSelectedExpense,
    selectedBasketPair,
    setSelectedBasketPair,
    scope,
    setScope,
    period,
    setPeriod,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    topProductCategory,
    setTopProductCategory,
    isLoading,
    isDrilldownLoading,
    isTopProductsLoading,
    isBasketReceiptsLoading,
    isFlowEventsLoading,
    errorMessage,
  } = useDashboard();

  useEffect(() => {
    setControls(
      <DashboardHeaderControls
        scope={scope}
        setScope={setScope}
        period={period}
        setPeriod={setPeriod}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        onExport={() => exportDashboardData(dashboard)}
        canExport={Boolean(dashboard)}
        viewMode={viewMode}
        setViewMode={setViewMode}
      />,
    );

    return () => setControls(null);
  }, [
    dashboard,
    endDate,
    period,
    scope,
    setControls,
    setEndDate,
    setPeriod,
    setScope,
    setStartDate,
    startDate,
    viewMode,
  ]);

  return (
    <section className="page-section">
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Dashboard betöltése...</p> : null}

      {dashboard ? (
        <>
          <DashboardKpiGrid kpis={dashboard.kpis} />

          <div className="dashboard-main dashboard-main-compact">
            <div className="dashboard-stack dashboard-stack-primary">
              <section className="dashboard-section dashboard-section-primary">
                <div className="dashboard-section-heading">
                  <span>Üzleti pulzus</span>
                  <strong>Bevétel, trend és döntési jelzés</strong>
                </div>

                <DashboardTrendOverview
                  startDate={dashboard.period.start_date}
                  endDate={dashboard.period.end_date}
                  grain={dashboard.period.grain}
                  points={dashboard.revenue_trend}
                  forecastRows={dashboard.forecast_impact_insights}
                />

                <DashboardStatisticsQuality
                  statistics={dashboard.statistics_quality}
                  viewMode={viewMode}
                />

                <DashboardBusinessFocus dashboard={dashboard} />
                <DashboardBusinessSpecificAnalytics dashboard={dashboard} />

                {dashboard.scope === "flow" ? (
                  <>
                    <DashboardFlowConsumptionControl dashboard={dashboard} />
                    <DashboardFlowFinancialEventImpact
                      events={flowEvents}
                      performances={flowEventPerformances}
                      isLoading={isFlowEventsLoading}
                    />
                    {isProfessional ? (
                      <DashboardFlowForecastEvent
                        rows={dashboard.flow_forecast_event_insights}
                      />
                    ) : null}
                  </>
                ) : null}

                {isProfessional ? (
                  <>
                    <DashboardVatReadinessCard readiness={dashboard.vat_readiness} />
                    {mappingReadiness ? (
                      <DashboardMappingReadinessCard readiness={mappingReadiness} />
                    ) : null}

                    <DashboardCategoryMix
                      categories={dashboard.category_breakdown}
                      activeCategory={
                        drilldown?.type === "category" ? drilldown.label : null
                      }
                      productDetails={productDetails}
                      selectedProduct={selectedProduct}
                      productSourceRows={productSourceRows}
                      isLoading={
                        drilldown?.type === "category" && isDrilldownLoading
                      }
                      metric={categoryMixMetric}
                      setMetric={setCategoryMixMetric}
                      openCategory={(category) => {
                        setSelectedProduct(null);
                        setDrilldown({ type: "category", label: category });
                      }}
                      closeCategory={() => {
                        setSelectedProduct(null);
                        setDrilldown(null);
                      }}
                      selectProduct={setSelectedProduct}
                    />

                    <DashboardTrafficHeatmap
                      cells={dashboard.traffic_heatmap}
                      scope={scope}
                      basketRows={dashboard.basket_value_distribution}
                    />

                    {dashboard.scope !== "flow" ? (
                      <>
                        <DashboardWeatherImpact
                          temperatureRows={dashboard.temperature_band_insights}
                          conditionRows={dashboard.weather_condition_insights}
                          categoryRows={dashboard.weather_category_insights}
                          forecastRows={dashboard.forecast_impact_insights}
                        />
                        <DashboardDailyForecast
                          categoryRows={dashboard.forecast_category_demand_insights}
                          productRows={dashboard.forecast_product_demand_insights}
                          peakRows={dashboard.forecast_peak_time_insights}
                        />
                      </>
                    ) : null}
                  </>
                ) : null}
              </section>
            </div>

            <div className="dashboard-stack">
              <section className="dashboard-section">
                <div className="dashboard-section-heading">
                  <span>Termék és készlet figyelő</span>
                  <strong>Top teljesítmény és kockázatok</strong>
                </div>

                <DashboardTopProducts
                  rows={topProducts}
                  categories={dashboard.category_breakdown}
                  selectedCategory={topProductCategory}
                  setSelectedCategory={setTopProductCategory}
                  isLoading={isTopProductsLoading}
                  scope={scope}
                />

                <DashboardRiskOverview
                  productRows={dashboard.product_risks}
                  stockRows={dashboard.stock_risks}
                />
              </section>

              {isProfessional ? (
                <section className="dashboard-section">
                  <div className="dashboard-section-heading">
                    <span>Kosár és költség mélyítés</span>
                    <strong>Együttvásárlás és kiadáskontroll</strong>
                  </div>

                  <DashboardBasketAnalysis
                    pairs={basketPairs}
                    selectedPair={selectedBasketPair}
                    setSelectedPair={setSelectedBasketPair}
                    receipts={basketReceipts}
                    isLoading={isBasketReceiptsLoading}
                  />

                  <DashboardExpenseBreakdown
                    rows={dashboard.expense_breakdown}
                    activeType={
                      drilldown?.type === "expense" ? drilldown.label : null
                    }
                    openExpenseType={(type) => {
                      setSelectedExpense(null);
                      setDrilldown({ type: "expense", label: type });
                    }}
                  />
                </section>
              ) : null}
            </div>
          </div>

          {drilldown?.type === "expense" ? (
            <DashboardExpenseDrilldown
              type={drilldown.label}
              rows={expenseDetails}
              selectedExpense={selectedExpense}
              setSelectedExpense={setSelectedExpense}
              source={expenseSource}
              isLoading={isDrilldownLoading}
              close={() => {
                setSelectedProduct(null);
                setSelectedExpense(null);
                setSelectedBasketPair(null);
                setDrilldown(null);
              }}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
