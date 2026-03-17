import type { ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { MappingWorkbenchStoreSnapshot, MappingStatusFilter, ReviewStatusFilter } from "./mappingWorkbenchStore";

const VALID_RESOURCE_CATEGORIES = new Set<ResourceCategoryId>([
  "all",
  "technology",
  "infrastructure_institutional",
  "talent",
]);

const VALID_MAPPING_STATUSES = new Set<MappingStatusFilter>(["all", "mapped", "unmapped"]);
const VALID_REVIEW_STATUSES = new Set<ReviewStatusFilter>(["all", "reviewed", "needs_review"]);

export function readMappingUrlState(): Partial<MappingWorkbenchStoreSnapshot> {
  const params = new URLSearchParams(window.location.search);
  const resource = params.get("resource");
  const mapping = params.get("mapping");
  const review = params.get("review");

  return {
    search: params.get("q") ?? "",
    policyFilterId: params.get("policyFilter") ?? "all",
    resourceCategoryId:
      resource && VALID_RESOURCE_CATEGORIES.has(resource as ResourceCategoryId)
        ? (resource as ResourceCategoryId)
        : "all",
    strategyTermId: params.get("strategy") ?? "all",
    techDomainFilterId: params.get("tech") ?? "all",
    mappingStatus:
      mapping && VALID_MAPPING_STATUSES.has(mapping as MappingStatusFilter)
        ? (mapping as MappingStatusFilter)
        : "all",
    reviewStatus:
      review && VALID_REVIEW_STATUSES.has(review as ReviewStatusFilter)
        ? (review as ReviewStatusFilter)
        : "all",
    inspectorPolicyId: params.get("inspectPolicy"),
    inspectorTechDomainId: params.get("inspectDomain"),
    activeContentId: params.get("content"),
  };
}

export function writeMappingUrlState(state: MappingWorkbenchStoreSnapshot) {
  const params = new URLSearchParams();

  if (state.search) params.set("q", state.search);
  if (state.policyFilterId !== "all") params.set("policyFilter", state.policyFilterId);
  if (state.resourceCategoryId !== "all") params.set("resource", state.resourceCategoryId);
  if (state.strategyTermId !== "all") params.set("strategy", state.strategyTermId);
  if (state.techDomainFilterId !== "all") params.set("tech", state.techDomainFilterId);
  if (state.mappingStatus !== "all") params.set("mapping", state.mappingStatus);
  if (state.reviewStatus !== "all") params.set("review", state.reviewStatus);
  if (state.inspectorPolicyId) params.set("inspectPolicy", state.inspectorPolicyId);
  if (state.inspectorTechDomainId) params.set("inspectDomain", state.inspectorTechDomainId);
  if (state.activeContentId) params.set("content", state.activeContentId);

  const next = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;
  window.history.replaceState({}, "", next);
}
