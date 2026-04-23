import { useEffect, useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import { listFinancialTransactions } from "../api/financeApi";
import type { FinancialTransaction } from "../types/finance";

type TransactionsState = {
  businessUnits: BusinessUnit[];
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  transactions: FinancialTransaction[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedTransactionType: string;
  setSelectedTransactionType: (value: string) => void;
  selectedSourceType: string;
  setSelectedSourceType: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
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

export function useTransactions(): TransactionsState {
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedTransactionType, setSelectedTransactionType] = useState("");
  const [selectedSourceType, setSelectedSourceType] = useState("");
  const [limit, setLimit] = useState(50);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadBusinessUnits() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const items = sortBusinessUnits(await listBusinessUnits());
        if (cancelled) {
          return;
        }

        setBusinessUnits(items);
        const primaryBusinessUnit = items.find(
          (item) => !TECHNICAL_BUSINESS_UNIT_CODES.has(item.code),
        );
        setSelectedBusinessUnitId(
          (current) => current || primaryBusinessUnit?.id || items[0]?.id || "",
        );
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Failed to load business units.",
          );
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

    async function loadTransactions() {
      if (!selectedBusinessUnitId) {
        setTransactions([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setErrorMessage("");

      try {
        const items = await listFinancialTransactions({
          business_unit_id: selectedBusinessUnitId,
          transaction_type: selectedTransactionType,
          source_type: selectedSourceType,
          limit,
        });

        if (cancelled) {
          return;
        }

        setTransactions(items);
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Failed to load transactions.",
          );
          setTransactions([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadTransactions();

    return () => {
      cancelled = true;
    };
  }, [selectedBusinessUnitId, selectedTransactionType, selectedSourceType, limit]);

  const { primary: primaryBusinessUnits, technical: technicalBusinessUnits } =
    splitBusinessUnits(businessUnits);

  return {
    businessUnits,
    primaryBusinessUnits,
    technicalBusinessUnits,
    transactions,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedTransactionType,
    setSelectedTransactionType,
    selectedSourceType,
    setSelectedSourceType,
    limit,
    setLimit,
    isLoading,
    errorMessage,
  };
}
