import { useEffect, useState } from "react";
import type { TechnologyLensProjection } from "./dashboard.types";
import { fetchOntologyNetworkDataset } from "./fetchOntologyNetworkDataset";

type OntologyNetworkDatasetState = {
  data: TechnologyLensProjection | null;
  error: Error | null;
  isLoading: boolean;
};

export function useOntologyNetworkDataset() {
  const [state, setState] = useState<OntologyNetworkDatasetState>({
    data: null,
    error: null,
    isLoading: true,
  });

  useEffect(() => {
    let active = true;

    fetchOntologyNetworkDataset()
      .then((data) => {
        if (!active) {
          return;
        }

        setState({
          data,
          error: null,
          isLoading: false,
        });
      })
      .catch((error) => {
        if (!active) {
          return;
        }

        setState({
          data: null,
          error: error instanceof Error ? error : new Error("Failed to load technology lens projection"),
          isLoading: false,
        });
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}

