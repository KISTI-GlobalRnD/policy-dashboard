import type { z } from "zod";
import {
  bucketSchema,
  contentEvidenceSchema,
  dashboardDatasetSchema,
  dashboardSummarySchema,
  mappingSupportSchema,
  memberItemSchema,
  policyItemContentSchema,
  policyItemGroupSchema,
  policySchema,
  reviewStatusSchema,
  sampleScopeSchema,
  sourceAssetSchema,
  taxonomySchema,
} from "./dashboard.schema";

export type DashboardDatasetDto = z.infer<typeof dashboardDatasetSchema>;
export type DashboardSummaryDto = z.infer<typeof dashboardSummarySchema>;
export type SampleScopeDto = z.infer<typeof sampleScopeSchema>;
export type PolicyDto = z.infer<typeof policySchema>;
export type BucketDto = z.infer<typeof bucketSchema>;
export type PolicyItemGroupDto = z.infer<typeof policyItemGroupSchema>;
export type PolicyItemContentDto = z.infer<typeof policyItemContentSchema>;
export type ContentEvidenceDto = z.infer<typeof contentEvidenceSchema>;
export type MemberItemDto = z.infer<typeof memberItemSchema>;
export type SourceAssetDto = z.infer<typeof sourceAssetSchema>;
export type TaxonomyDto = z.infer<typeof taxonomySchema>;
export type ReviewStatus = z.infer<typeof reviewStatusSchema>;
export type MappingSupportDto = z.infer<typeof mappingSupportSchema>;

export type ResourceCategoryId = "all" | "technology" | "infrastructure_institutional" | "talent";
export type ProjectionStatus = "curated" | "provisional";
export type ProjectionFilterId = "all" | ProjectionStatus;

export type DashboardPolicy = PolicyDto & {
  policy_order: number;
  total_group_count: number;
  total_content_count: number;
  total_member_count: number;
  total_evidence_count: number;
  strategy_labels: string[];
  tech_labels: string[];
};

export type ResourceCategory = {
  resource_category_id: Exclude<ResourceCategoryId, "all">;
  display_label: string;
  display_order: number;
};

export type StrategyFilter = {
  term_id: string;
  label: string;
  group_count: number;
  content_count: number;
};

export type TechDomainFilter = {
  term_id: string;
  label: string;
  group_count: number;
  content_count: number;
};

export type RepresentationSummary = {
  representation_type: string;
  evidence_count: number;
  content_count: number;
};

export type DashboardStats = {
  policy_count: number;
  group_count: number;
  content_count: number;
  group_member_count: number;
  content_evidence_count: number;
  group_taxonomy_count: number;
  display_text_count: number;
};

export type ContentRow = {
  policy_id: string;
  policy_name: string;
  policy_order: number;
  policy_bucket_id: string;
  resource_category_id: Exclude<ResourceCategoryId, "all">;
  resource_category_label: string;
  policy_item_group_id: string;
  group_label: string;
  group_summary: string;
  group_description: string;
  policy_item_content_id: string;
  content_label: string;
  content_statement: string;
  content_summary: string;
  content_type: string;
  display_order: number;
  member_count: number;
  evidence_count: number;
  source_asset_count: number;
  figure_evidence_count: number;
  primary_strategy: TaxonomyDto | null;
  strategy_terms: TaxonomyDto[];
  tech_terms: TaxonomyDto[];
  tech_subterms: TaxonomyDto[];
  representation_types: string[];
  representative_member: MemberItemDto | null;
  primary_source_asset: SourceAssetDto | null;
  preferred_source_asset: SourceAssetDto | null;
  location_labels: string[];
  content_review_status: ReviewStatus;
  group_review_status: ReviewStatus;
  mapping_review_status: ReviewStatus;
  projection_status: ProjectionStatus;
  search_text: string;
};

export type ContentContext = {
  policy: DashboardPolicy;
  bucket: BucketDto;
  group: PolicyItemGroupDto;
  content: PolicyItemContentDto;
  strategy_terms: TaxonomyDto[];
  tech_terms: TaxonomyDto[];
  tech_subterms: TaxonomyDto[];
  primary_strategy: TaxonomyDto | null;
  representative_member: MemberItemDto | null;
  primary_source_asset: SourceAssetDto | null;
  preferred_source_asset: SourceAssetDto | null;
  location_labels: string[];
  content_review_status: ReviewStatus;
  group_review_status: ReviewStatus;
  mapping_review_status: ReviewStatus;
  projection_status: ProjectionStatus;
};

export type DashboardDataset = {
  sample_scope: SampleScopeDto;
  stats: DashboardStats;
  policies: DashboardPolicy[];
  resource_categories: ResourceCategory[];
  strategy_filters: StrategyFilter[];
  tech_domain_filters: TechDomainFilter[];
  representation_summaries: RepresentationSummary[];
  content_rows: ContentRow[];
  policyMap: Map<string, DashboardPolicy>;
  strategyFilterMap: Map<string, StrategyFilter>;
  techDomainFilterMap: Map<string, TechDomainFilter>;
  contentContextMap: Map<string, ContentContext>;
};
