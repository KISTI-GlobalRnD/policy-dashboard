import curatedContentSamplePackJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_pack.json";
import curatedContentSampleSummaryJson from "../../../../../04_ontology/sample_build/curated_content_sample/curated_content_sample_summary.json";
import { adaptDashboardDataset } from "./dashboard.adapter";
import { dashboardDatasetSchema, dashboardSummarySchema, mappingSupportSchema } from "./dashboard.schema";

const RUNTIME_PACK_PATH = "./data/mapping-workbench-pack.json";
const RUNTIME_SUMMARY_PATH = "./data/mapping-workbench-summary.json";
const RUNTIME_SUPPORT_PATH = "./data/mapping-workbench-support.json";
const FALLBACK_SUPPORT_PATH = "./data/mapping-support.json";

const EMPTY_MAPPING_SUPPORT = mappingSupportSchema.parse({
  content_review_status_by_id: {},
  group_review_status_by_id: {},
  group_tech_review_status_by_key: {},
});

const buildDataUrl = (path: string) => new URL(path, window.location.href).toString();

export async function fetchDashboardDataset() {
  try {
    const RUNTIME_PACK_URL = buildDataUrl(RUNTIME_PACK_PATH);
    const RUNTIME_SUMMARY_URL = buildDataUrl(RUNTIME_SUMMARY_PATH);
    const RUNTIME_SUPPORT_URL = buildDataUrl(RUNTIME_SUPPORT_PATH);
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
    const FALLBACK_SUPPORT_URL = buildDataUrl(FALLBACK_SUPPORT_PATH);
    const response = await fetch(FALLBACK_SUPPORT_URL);
    if (response.ok) {
      return adaptDashboardDataset(parsedPack, parsedSummary, mappingSupportSchema.parse(await response.json()));
    }
  } catch {
    return adaptDashboardDataset(parsedPack, parsedSummary, EMPTY_MAPPING_SUPPORT);
  }

  return adaptDashboardDataset(parsedPack, parsedSummary, EMPTY_MAPPING_SUPPORT);
}
