import curatedContentSamplePackJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_pack.json";
import curatedContentSampleSummaryJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_summary.json";
import runtimePackJson from "../../../public/data/mapping-workbench-pack.json";
import runtimeSummaryJson from "../../../public/data/mapping-workbench-summary.json";
import runtimeSupportJson from "../../../public/data/mapping-workbench-support.json";
import fallbackSupportJson from "../../../public/data/mapping-support.json";
import { adaptDashboardDataset } from "./dashboard.adapter";
import { dashboardDatasetSchema, dashboardSummarySchema, mappingSupportSchema } from "./dashboard.schema";

const EMPTY_MAPPING_SUPPORT = mappingSupportSchema.parse({
  content_review_status_by_id: {},
  group_review_status_by_id: {},
  group_tech_review_status_by_key: {},
});

const STATIC_DASHBOARD_DATA = (() => {
  try {
    const parsedPack = dashboardDatasetSchema.parse(runtimePackJson);
    const parsedSummary = dashboardSummarySchema.parse(runtimeSummaryJson);
    const parsedSupport = mappingSupportSchema.parse(runtimeSupportJson);
    return adaptDashboardDataset(parsedPack, parsedSummary, parsedSupport);
  } catch {
    return null;
  }
})();

const EMPTY_SUPPORT = mappingSupportSchema.safeParse(fallbackSupportJson).data ?? EMPTY_MAPPING_SUPPORT;

export async function fetchDashboardDataset() {
  if (STATIC_DASHBOARD_DATA) {
    return STATIC_DASHBOARD_DATA;
  }

  const parsedPack = dashboardDatasetSchema.parse(curatedContentSamplePackJson);
  const parsedSummary = dashboardSummarySchema.parse(curatedContentSampleSummaryJson);

  return adaptDashboardDataset(parsedPack, parsedSummary, EMPTY_SUPPORT);
}
