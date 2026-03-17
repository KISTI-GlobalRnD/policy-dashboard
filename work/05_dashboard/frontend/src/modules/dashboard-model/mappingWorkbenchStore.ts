import { create } from "zustand";
import type { ResourceCategoryId, ReviewStatus } from "../dashboard-data/dashboard.types";

export type MappingStatusFilter = "all" | "mapped" | "unmapped";
export type ReviewStatusFilter = "all" | ReviewStatus;

export type MappingWorkbenchStoreState = {
  search: string;
  policyFilterId: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainFilterId: string;
  mappingStatus: MappingStatusFilter;
  reviewStatus: ReviewStatusFilter;
  inspectorPolicyId: string | null;
  inspectorTechDomainId: string | null;
  activeContentId: string | null;
  initializedFromUrl: boolean;
  setSearch: (value: string) => void;
  setPolicyFilterId: (value: string) => void;
  setResourceCategoryId: (value: ResourceCategoryId) => void;
  setStrategyTermId: (value: string) => void;
  setTechDomainFilterId: (value: string) => void;
  setMappingStatus: (value: MappingStatusFilter) => void;
  setReviewStatus: (value: ReviewStatusFilter) => void;
  setInspectorPolicyId: (value: string | null) => void;
  setInspectorTechDomainId: (value: string | null) => void;
  selectCell: (policyId: string, techDomainId: string) => void;
  selectContent: (contentId: string | null) => void;
  resetFilters: () => void;
  clearInspector: () => void;
  hydrateFromUrl: (value: Partial<MappingWorkbenchStoreSnapshot>) => void;
  markUrlInitialized: () => void;
};

export type MappingWorkbenchStoreSnapshot = Pick<
  MappingWorkbenchStoreState,
  | "search"
  | "policyFilterId"
  | "resourceCategoryId"
  | "strategyTermId"
  | "techDomainFilterId"
  | "mappingStatus"
  | "reviewStatus"
  | "inspectorPolicyId"
  | "inspectorTechDomainId"
  | "activeContentId"
>;

const INITIAL_FILTER_STATE = {
  search: "",
  policyFilterId: "all",
  resourceCategoryId: "all" as ResourceCategoryId,
  strategyTermId: "all",
  techDomainFilterId: "all",
  mappingStatus: "all" as MappingStatusFilter,
  reviewStatus: "all" as ReviewStatusFilter,
};

export const useMappingWorkbenchStore = create<MappingWorkbenchStoreState>((set) => ({
  ...INITIAL_FILTER_STATE,
  inspectorPolicyId: null,
  inspectorTechDomainId: null,
  activeContentId: null,
  initializedFromUrl: false,
  setSearch: (value) => set({ search: value }),
  setPolicyFilterId: (value) => set({ policyFilterId: value }),
  setResourceCategoryId: (value) => set({ resourceCategoryId: value }),
  setStrategyTermId: (value) => set({ strategyTermId: value }),
  setTechDomainFilterId: (value) => set({ techDomainFilterId: value }),
  setMappingStatus: (value) => set({ mappingStatus: value }),
  setReviewStatus: (value) => set({ reviewStatus: value }),
  setInspectorPolicyId: (value) => set({ inspectorPolicyId: value, activeContentId: null }),
  setInspectorTechDomainId: (value) => set({ inspectorTechDomainId: value, activeContentId: null }),
  selectCell: (policyId, techDomainId) =>
    set({
      inspectorPolicyId: policyId,
      inspectorTechDomainId: techDomainId,
      activeContentId: null,
    }),
  selectContent: (contentId) => set({ activeContentId: contentId }),
  resetFilters: () =>
    set({
      ...INITIAL_FILTER_STATE,
      inspectorPolicyId: null,
      inspectorTechDomainId: null,
      activeContentId: null,
    }),
  clearInspector: () =>
    set({
      inspectorPolicyId: null,
      inspectorTechDomainId: null,
      activeContentId: null,
    }),
  hydrateFromUrl: (value) =>
    set((current) => ({
      ...current,
      ...value,
    })),
  markUrlInitialized: () => set({ initializedFromUrl: true }),
}));
