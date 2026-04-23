import { useEffect, useState } from "react";

import {
  listBusinessUnits,
  listCategories,
  listLocations,
  listProducts,
} from "../api/masterDataApi";
import type {
  BusinessUnit,
  Category,
  Location,
  Product,
} from "../types/masterData";

type MasterDataState = {
  businessUnits: BusinessUnit[];
  locations: Location[];
  categories: Category[];
  products: Product[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  isLoading: boolean;
  errorMessage: string;
};

export function useMasterDataViewer(): MasterDataState {
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadBusinessUnits() {
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
          setErrorMessage(error instanceof Error ? error.message : "Failed to load business units.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadBusinessUnits();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadDependentData() {
      if (!selectedBusinessUnitId) {
        setLocations([]);
        setCategories([]);
        setProducts([]);
        return;
      }

      setIsLoading(true);
      setErrorMessage("");

      try {
        const [locationItems, categoryItems, productItems] = await Promise.all([
          listLocations(selectedBusinessUnitId),
          listCategories(selectedBusinessUnitId),
          listProducts(selectedBusinessUnitId),
        ]);

        if (cancelled) {
          return;
        }

        setLocations(locationItems);
        setCategories(categoryItems);
        setProducts(productItems);
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load master data.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDependentData();

    return () => {
      cancelled = true;
    };
  }, [selectedBusinessUnitId]);

  return {
    businessUnits,
    locations,
    categories,
    products,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    isLoading,
    errorMessage,
  };
}
