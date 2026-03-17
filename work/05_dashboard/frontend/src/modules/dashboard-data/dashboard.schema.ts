import { z } from "zod";

export const dashboardSummarySchema = z.object({
  policy_count: z.number(),
  group_count: z.number(),
  content_count: z.number(),
  group_member_count: z.number(),
  content_evidence_count: z.number(),
  group_taxonomy_count: z.number(),
  display_text_count: z.number(),
  policies: z.array(
    z.object({
      policy_id: z.string(),
      policy_name: z.string(),
      bucket_count: z.number(),
    }),
  ),
});

export const sampleScopeSchema = z.object({
  pack_id: z.string(),
  generated_from: z.string(),
  purpose: z.string(),
  policy_count: z.number(),
  group_count: z.number(),
  content_count: z.number(),
});

export const taxonomySchema = z.object({
  taxonomy_type: z.string(),
  term_id: z.string(),
  label: z.string(),
  is_primary: z.boolean(),
});

export const reviewStatusSchema = z.enum(["reviewed", "needs_review"]).catch("needs_review");

export const memberItemSchema = z.object({
  policy_item_id: z.string(),
  item_label: z.string(),
  item_statement: z.string(),
  member_role: z.string(),
  is_representative: z.boolean(),
  derived_representation_id: z.string(),
});

export const sourceAssetSchema = z.object({
  derived_representation_id: z.string(),
  source_asset_id: z.string(),
  asset_type: z.string(),
  asset_path_or_url: z.string(),
  page_no: z.string().nullable().catch(""),
  section_id: z.string().nullable().catch(""),
});

export const contentEvidenceSchema = z.object({
  source_policy_item_id: z.string(),
  source_policy_item_label: z.string(),
  derived_representation_id: z.string(),
  source_object_type: z.string().catch(""),
  source_object_id: z.string().catch(""),
  representation_type: z.string(),
  document_id: z.string(),
  location_type: z.string().nullable().catch(""),
  location_value: z.string().nullable().catch(""),
  evidence_text: z.string(),
  evidence_label: z.string().catch(""),
  structured_payload_path: z.string().catch(""),
  table_json_path: z.string().catch(""),
  source_assets: z.array(sourceAssetSchema),
});

export const policyItemContentSchema = z.object({
  policy_item_content_id: z.string(),
  content_label: z.string(),
  content_statement: z.string(),
  content_summary: z.string(),
  content_type: z.string(),
  display_order: z.number(),
  evidence: z.array(contentEvidenceSchema),
});

export const policyItemGroupSchema = z.object({
  policy_item_group_id: z.string(),
  group_label: z.string(),
  group_summary: z.string(),
  group_description: z.string(),
  taxonomies: z.array(taxonomySchema),
  member_items: z.array(memberItemSchema),
  contents: z.array(policyItemContentSchema),
});

export const bucketSchema = z.object({
  policy_bucket_id: z.string(),
  resource_category_id: z.string(),
  resource_category_label: z.string(),
  groups: z.array(policyItemGroupSchema),
});

export const policySchema = z.object({
  policy_id: z.string(),
  policy_name: z.string(),
  buckets: z.array(bucketSchema),
});

export const dashboardDatasetSchema = z.object({
  sample_scope: sampleScopeSchema,
  policies: z.array(policySchema),
});

export const mappingSupportSchema = z.object({
  content_review_status_by_id: z.record(reviewStatusSchema),
  group_review_status_by_id: z.record(reviewStatusSchema),
  group_tech_review_status_by_key: z.record(reviewStatusSchema),
});
