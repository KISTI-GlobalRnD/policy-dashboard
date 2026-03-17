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

export const technologyLensProjectionTaxonomySchema = z.object({
  term_id: z.string().catch(""),
  label: z.string().catch(""),
  is_primary: z.boolean().catch(false),
  confidence: z.string().catch(""),
  review_status: z.string().catch(""),
});

export const technologyLensProjectionEvidenceSchema = z.object({
  derived_representation_id: z.string(),
  representation_type: z.string(),
  source_tier: z.string().catch("supplementary"),
  is_primary: z.boolean().catch(false),
  evidence_count: z.number().catch(0),
  evidence_strength: z.string().catch(""),
  location_type: z.string().catch(""),
  location_value: z.string().catch(""),
  quality_status: z.string().catch(""),
  review_status: z.string().catch(""),
}).passthrough();

export const technologyLensProjectionContentSchema = z.object({
  policy_item_content_id: z.string(),
  content_label: z.string(),
  content_statement: z.string().catch(""),
  content_summary: z.string().catch(""),
  content_type: z.string().catch(""),
  content_status: z.string().catch(""),
  display_order: z.number().catch(999),
  evidence_count: z.number().catch(0),
  primary_policy_evidence: technologyLensProjectionEvidenceSchema,
  evidence: z.array(technologyLensProjectionEvidenceSchema).default([]),
  projection_source: z.string().catch(""),
  source_policy_item_id: z.string().catch(""),
  display: z
    .object({
      title_text: z.string().catch(""),
      summary_text: z.string().catch(""),
      description_text: z.string().catch(""),
    })
    .catch({
      title_text: "",
      summary_text: "",
      description_text: "",
    }),
}).passthrough();

export const technologyLensProjectionGroupSchema = z.object({
  policy_item_group_id: z.string(),
  group_label: z.string(),
  group_summary: z.string().catch(""),
  group_description: z.string().catch(""),
  group_status: z.string().catch("sample_curated"),
  source_basis_type: z.string().catch(""),
  display_order: z.number().catch(999),
  content_count: z.number().catch(0),
  member_item_count: z.number().catch(0),
  projection_source: z.string().catch(""),
  policy: z.object({
    policy_id: z.string(),
    policy_name: z.string(),
    policy_order: z.number().catch(999),
  }),
  bucket: z.object({
    policy_bucket_id: z.string(),
    resource_category_id: z.string(),
    resource_category_label: z.string(),
    bucket_display_order: z.number().catch(999),
  }),
  taxonomy: z
    .object({
      primary_tech_domain: technologyLensProjectionTaxonomySchema.nullable(),
      secondary_tech_domains: z.array(technologyLensProjectionTaxonomySchema).default([]),
      primary_tech_subdomain: technologyLensProjectionTaxonomySchema.nullable(),
      secondary_tech_subdomains: z.array(technologyLensProjectionTaxonomySchema).default([]),
      strategies: z.array(technologyLensProjectionTaxonomySchema).default([]),
    })
    .catch({
      primary_tech_domain: null,
      secondary_tech_domains: [],
      primary_tech_subdomain: null,
      secondary_tech_subdomains: [],
      strategies: [],
    }),
  contents: z.array(technologyLensProjectionContentSchema).default([]),
  members: z.array(z.unknown()).default([]),
  member_items: z.array(z.unknown()).default([]),
}).passthrough();

export const technologyLensProjectionDomainSchema = z.object({
  tech_domain_id: z.string(),
  tech_domain_label: z.string(),
  display_order: z.number().catch(999),
  group_count: z.number().catch(0),
  content_count: z.number().catch(0),
  policy_count: z.number().catch(0),
  resource_category_counts: z.record(z.number()).catch({}),
  strategies: z.array(technologyLensProjectionTaxonomySchema).default([]),
  subdomains: z.array(technologyLensProjectionTaxonomySchema).default([]),
  groups: z.array(technologyLensProjectionGroupSchema).default([]),
}).passthrough();

export const technologyLensProjectionSchema = z.object({
  meta: z
    .object({
      projection_name: z.string().catch("technology lens projection"),
      projection_version: z.string().catch(""),
      generated_at: z.string().catch(""),
      source_db_path: z.string().catch(""),
      group_scope: z.string().catch(""),
      stats: z.record(z.number()),
    })
    .catch({
      projection_name: "technology lens projection",
      projection_version: "",
      generated_at: "",
      source_db_path: "",
      group_scope: "",
      stats: {},
    }),
  tech_domain_filters: z.array(z.unknown()).default([]),
  tech_domains: z.array(technologyLensProjectionDomainSchema).default([]),
  unassigned_groups: z.array(technologyLensProjectionGroupSchema).default([]),
});
