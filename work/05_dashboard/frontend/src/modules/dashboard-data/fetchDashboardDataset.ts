import curatedContentSamplePackJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_pack.json";
import curatedContentSampleSummaryJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_summary.json";
import { adaptDashboardDataset } from "./dashboard.adapter";
import { dashboardDatasetSchema, dashboardSummarySchema, mappingSupportSchema } from "./dashboard.schema";

const RUNTIME_PACK_URL = "/data/mapping-workbench-pack.json";
const RUNTIME_SUMMARY_URL = "/data/mapping-workbench-summary.json";
const RUNTIME_SUPPORT_URL = "/data/mapping-workbench-support.json";

const EMPTY_MAPPING_SUPPORT = mappingSupportSchema.parse({
  content_review_status_by_id: {},
  group_review_status_by_id: {},
  group_tech_review_status_by_key: {},
});

export async function fetchDashboardDataset() {
  try {
    const [packResponse, summaryResponse, supportResponse] = await Promise.all([
      fetch(RUNTIME_PACK_URL),
      fetch(RUNTIME_SUMMARY_URL),
      fetch(RUNTIME_SUPPORT_URL),
    ]);

    if (packResponse.ok && summaryResponse.ok && supportResponse.ok) {
      const parsedPack = dashboardDatasetSchema.parse(await packResponse.json());
      const parsedSummary = dashboardSummarySchema.parse(await summaryResponse.json());
      const parsedSupport = mappingSupportSchema.parse(await supportResponse.json());

      return adaptDashboardDataset(parsedPack, parsedSummary, parsedSupport);
    }
  } catch {
    // Fall back to the curated in-repo sample when the generated runtime pack is unavailable.
  }

  const parsedPack = dashboardDatasetSchema.parse(curatedContentSamplePackJson);
  const parsedSummary = dashboardSummarySchema.parse(curatedContentSampleSummaryJson);

  try {
    const response = await fetch("/data/mapping-support.json");
    if (response.ok) {
      return adaptDashboardDataset(parsedPack, parsedSummary, mappingSupportSchema.parse(await response.json()));
    }
  } catch {
    return adaptDashboardDataset(parsedPack, parsedSummary, EMPTY_MAPPING_SUPPORT);
  }

  return adaptDashboardDataset(parsedPack, parsedSummary, EMPTY_MAPPING_SUPPORT);
}
