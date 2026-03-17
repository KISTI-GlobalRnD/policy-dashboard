import { create } from "zustand";
import type { ProjectionFilterId, ResourceCategoryId } from "../dashboard-data/dashboard.types";

export type DashboardStoreState = {
  search: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainId: string;
  projectionStatus: ProjectionFilterId;
  rowLimit: number;
  activePolicyId: string | null;
  activeContentId: string | null;
  initializedFromUrl: boolean;
  setSearch: (value: string) => void;
  setResourceCategoryId: (value: ResourceCategoryId) => void;
  setStrategyTermId: (value: string) => void;
  setTechDomainId: (value: string) => void;
  setProjectionStatus: (value: ProjectionFilterId) => void;
  setRowLimit: (value: number) => void;
  setActivePolicyId: (value: string | null) => void;
  setActiveContentId: (value: string | null) => void;
  resetFilters: () => void;
  hydrateFromUrl: (value: Partial<DashboardStoreSnapshot>) => void;
  markUrlInitialized: () => void;
};

export type DashboardStoreSnapshot = Pick<
  DashboardStoreState,
  | "search"
  | "resourceCategoryId"
  | "strategyTermId"
  | "techDomainId"
  | "projectionStatus"
  | "rowLimit"
  | "activePolicyId"
  | "activeContentId"
>;

const INITIAL_FILTER_STATE = {
  search: "",
  resourceCategoryId: "all" as ResourceCategoryId,
  strategyTermId: "all",
  techDomainId: "all",
  projectionStatus: "all" as ProjectionFilterId,
  rowLimit: 12,
};

export const useDashboardStore = create<DashboardStoreState>((set) => ({
  ...INITIAL_FILTER_STATE,
  activePolicyId: null,
  activeContentId: null,
  initializedFromUrl: false,
  setSearch: (value) => set({ search: value, activeContentId: null }),
  setResourceCategoryId: (value) => set({ resourceCategoryId: value, activeContentId: null }),
  setStrategyTermId: (value) => set({ strategyTermId: value, activeContentId: null }),
  setTechDomainId: (value) => set({ techDomainId: value, activeContentId: null }),
  setProjectionStatus: (value) => set({ projectionStatus: value, activeContentId: null }),
  setRowLimit: (value) => set({ rowLimit: value, activeContentId: null }),
  setActivePolicyId: (value) => set({ activePolicyId: value, activeContentId: null }),
  setActiveContentId: (value) => set({ activeContentId: value }),
  resetFilters: () =>
    set((current) => ({
      ...current,
      ...INITIAL_FILTER_STATE,
      activeContentId: null,
    })),
  hydrateFromUrl: (value) =>
    set((current) => ({
      ...current,
      ...value,
    })),
  markUrlInitialized: () => set({ initializedFromUrl: true }),
}));
