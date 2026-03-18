import type { ProjectionFilterId, ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { DashboardStoreSnapshot } from "./dashboardStore";
import { buildAppUrl } from "../../shared/lib/route";

const VALID_RESOURCE_CATEGORIES = new Set<ResourceCategoryId>([
  "all",
  "technology",
  "infrastructure_institutional",
  "talent",
]);
const VALID_PROJECTION_FILTERS = new Set<ProjectionFilterId>(["all", "curated", "provisional"]);

function parseNumber(value: string | null, fallback: number) {
  if (!value) {
    return fallback;
  }

  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

export function readDashboardUrlState(): Partial<DashboardStoreSnapshot> {
  const params = new URLSearchParams(window.location.search);
  const category = params.get("category");
  const projection = params.get("projection");

  return {
    search: params.get("q") ?? "",
    resourceCategoryId:
      category && VALID_RESOURCE_CATEGORIES.has(category as ResourceCategoryId)
        ? (category as ResourceCategoryId)
        : "all",
    strategyTermId: params.get("strategy") ?? "all",
    techDomainId: params.get("tech") ?? "all",
    projectionStatus:
      projection && VALID_PROJECTION_FILTERS.has(projection as ProjectionFilterId)
        ? (projection as ProjectionFilterId)
        : "all",
    rowLimit: parseNumber(params.get("limit"), 12),
    activePolicyId: params.get("policy"),
    activeContentId: params.get("content"),
  };
}

export function writeDashboardUrlState(state: DashboardStoreSnapshot) {
  const params = new URLSearchParams(window.location.search);

  ["q", "category", "strategy", "tech", "projection", "limit", "policy", "content"].forEach((key) =>
    params.delete(key),
  );

  if (state.search) params.set("q", state.search);
  if (state.resourceCategoryId !== "all") params.set("category", state.resourceCategoryId);
  if (state.strategyTermId !== "all") params.set("strategy", state.strategyTermId);
  if (state.techDomainId !== "all") params.set("tech", state.techDomainId);
  if (state.projectionStatus !== "all") params.set("projection", state.projectionStatus);
  if (state.rowLimit !== 12) params.set("limit", String(state.rowLimit));
  if (state.activePolicyId) params.set("policy", state.activePolicyId);
  if (state.activeContentId) params.set("content", state.activeContentId);

  const next = buildAppUrl(params);
  window.history.replaceState({}, "", next);
}
