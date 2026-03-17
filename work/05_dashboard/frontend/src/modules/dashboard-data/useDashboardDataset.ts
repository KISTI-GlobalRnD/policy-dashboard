import { useEffect, useState } from "react";
import type { DashboardDataset } from "./dashboard.types";
import { fetchDashboardDataset } from "./fetchDashboardDataset";

type DashboardDatasetState = {
  data: DashboardDataset | null;
  error: Error | null;
  isLoading: boolean;
};

export function useDashboardDataset() {
  const [state, setState] = useState<DashboardDatasetState>({
    data: null,
    error: null,
    isLoading: true,
  });

  useEffect(() => {
    let cancelled = false;

    fetchDashboardDataset()
      .then((data) => {
        if (cancelled) {
          return;
        }

        setState({
          data,
          error: null,
          isLoading: false,
        });
      })
      .catch((error: Error) => {
        if (cancelled) {
          return;
        }

        setState({
          data: null,
          error,
          isLoading: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
