import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import { getRecipeReadinessOverview, listProductionRecipes } from "../api/productionApi";
import type { RecipeCostSummary, RecipeReadinessOverview } from "../types/production";

type RecipesState = {
  businessUnits: BusinessUnit[];
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  recipes: RecipeCostSummary[];
  overview: RecipeReadinessOverview | null;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  activeOnly: boolean;
  setActiveOnly: (value: boolean) => void;
  isLoading: boolean;
  errorMessage: string;
};

const TECHNICAL_BUSINESS_UNIT_CODES = new Set(["test-integration"]);

function sortBusinessUnits(items: BusinessUnit[]) {
  return [...items].sort((left, right) => {
    const leftIsTechnical = TECHNICAL_BUSINESS_UNIT_CODES.has(left.code);
    const rightIsTechnical = TECHNICAL_BUSINESS_UNIT_CODES.has(right.code);

    if (leftIsTechnical !== rightIsTechnical) {
      return leftIsTechnical ? 1 : -1;
    }

    return left.name.localeCompare(right.name);
  });
}

function splitBusinessUnits(items: BusinessUnit[]) {
  return {
    primary: items.filter((item) => !TECHNICAL_BUSINESS_UNIT_CODES.has(item.code)),
    technical: items.filter((item) => TECHNICAL_BUSINESS_UNIT_CODES.has(item.code)),
  };
}

export function useRecipes(): RecipesState {
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: async () => sortBusinessUnits(await listBusinessUnits()),
  });

  const businessUnits = businessUnitsQuery.data ?? [];
  const { primary: primaryBusinessUnits, technical: technicalBusinessUnits } =
    splitBusinessUnits(businessUnits);

  const effectiveBusinessUnitId =
    selectedBusinessUnitId ||
    primaryBusinessUnits[0]?.id ||
    businessUnits[0]?.id ||
    "";

  const recipesQuery = useQuery({
    queryKey: ["production-recipes", effectiveBusinessUnitId, activeOnly],
    queryFn: () =>
      listProductionRecipes({
        business_unit_id: effectiveBusinessUnitId,
        active_only: activeOnly,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const overviewQuery = useQuery({
    queryKey: ["production-recipes-readiness-overview", effectiveBusinessUnitId, activeOnly],
    queryFn: () =>
      getRecipeReadinessOverview({
        business_unit_id: effectiveBusinessUnitId,
        active_only: activeOnly,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  return {
    businessUnits,
    primaryBusinessUnits,
    technicalBusinessUnits,
    recipes: recipesQuery.data ?? [],
    overview: overviewQuery.data ?? null,
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    activeOnly,
    setActiveOnly,
    isLoading:
      businessUnitsQuery.isLoading || recipesQuery.isLoading || overviewQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (recipesQuery.error instanceof Error && recipesQuery.error.message) ||
      (overviewQuery.error instanceof Error && overviewQuery.error.message) ||
      "",
  };
}
