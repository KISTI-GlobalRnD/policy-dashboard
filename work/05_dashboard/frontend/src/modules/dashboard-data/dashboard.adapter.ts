import type {
  ContentContext,
  ContentRow,
  DashboardDataset,
  DashboardDatasetDto,
  DashboardPolicy,
  MappingSupportDto,
  DashboardSummaryDto,
  RepresentationSummary,
  ReviewStatus,
  ResourceCategory,
  StrategyFilter,
  TechDomainFilter,
  TaxonomyDto,
  ProjectionStatus,
} from "./dashboard.types";

const CATEGORY_ORDER: Record<Exclude<DashboardDataset["resource_categories"][number]["resource_category_id"], never>, number> = {
  technology: 1,
  infrastructure_institutional: 2,
  talent: 3,
};

function uniqueLabels(values: string[]) {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right, "ko"));
}

function getStrategyTerms(taxonomies: TaxonomyDto[]) {
  return taxonomies.filter((term) => term.taxonomy_type === "strategy");
}

function getTechTerms(taxonomies: TaxonomyDto[]) {
  return taxonomies.filter((term) => term.taxonomy_type === "tech_domain");
}

function getTechSubdomainTerms(taxonomies: TaxonomyDto[]) {
  return taxonomies.filter((term) => term.taxonomy_type === "tech_subdomain");
}

function getAssetExtension(path: string | undefined) {
  const normalizedPath = String(path ?? "").toLowerCase();
  const match = normalizedPath.match(/\.[a-z0-9]+$/);
  return match?.[0] ?? "";
}

function isPreviewableAsset(path: string | undefined) {
  const extension = getAssetExtension(path);
  return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf"].includes(extension);
}

function pickPreferredSourceAsset(content: DashboardDatasetDto["policies"][number]["buckets"][number]["groups"][number]["contents"][number]) {
  const sourceAssets = content.evidence.flatMap((evidence) => evidence.source_assets);

  const preferredFigureAsset = sourceAssets.find((asset) => asset.asset_type === "figure_image" && isPreviewableAsset(asset.asset_path_or_url));
  if (preferredFigureAsset) {
    return preferredFigureAsset;
  }

  const preferredPreviewAsset = sourceAssets.find((asset) => isPreviewableAsset(asset.asset_path_or_url));
  if (preferredPreviewAsset) {
    return preferredPreviewAsset;
  }

  return sourceAssets[0] ?? null;
}

function buildResourceCategories(input: DashboardDatasetDto): ResourceCategory[] {
  const categoryMap = new Map<ResourceCategory["resource_category_id"], ResourceCategory>();

  for (const policy of input.policies) {
    for (const bucket of policy.buckets) {
      const resourceCategoryId = bucket.resource_category_id as ResourceCategory["resource_category_id"];
      if (!categoryMap.has(resourceCategoryId)) {
        categoryMap.set(resourceCategoryId, {
          resource_category_id: resourceCategoryId,
          display_label: bucket.resource_category_label,
          display_order: CATEGORY_ORDER[resourceCategoryId] ?? 99,
        });
      }
    }
  }

  return [...categoryMap.values()].sort((left, right) => left.display_order - right.display_order);
}

function getContentReviewStatus(contentId: string, support: MappingSupportDto): ReviewStatus {
  return support.content_review_status_by_id[contentId] ?? "needs_review";
}

function getGroupReviewStatus(groupId: string, support: MappingSupportDto): ReviewStatus {
  return support.group_review_status_by_id[groupId] ?? "needs_review";
}

function getMappingReviewStatus(groupId: string, techTerms: TaxonomyDto[], support: MappingSupportDto): ReviewStatus {
  if (techTerms.length === 0) {
    return "needs_review";
  }

  return techTerms.every((term) => support.group_tech_review_status_by_key[`${groupId}::${term.term_id}`] === "reviewed")
    ? "reviewed"
    : "needs_review";
}

function getProjectionStatus(groupReviewStatus: ReviewStatus, contentReviewStatus: ReviewStatus): ProjectionStatus {
  return groupReviewStatus === "reviewed" && contentReviewStatus === "reviewed" ? "curated" : "provisional";
}

export function adaptDashboardDataset(
  input: DashboardDatasetDto,
  summary: DashboardSummaryDto,
  support: MappingSupportDto,
): DashboardDataset {
  const resource_categories = buildResourceCategories(input);
  const strategyAccumulator = new Map<string, StrategyFilter>();
  const techAccumulator = new Map<string, TechDomainFilter>();
  const representationAccumulator = new Map<string, RepresentationSummary>();
  const content_rows: ContentRow[] = [];
  const contentContextMap = new Map<string, ContentContext>();

  const policies: DashboardPolicy[] = input.policies.map((policy, index) => {
    let total_group_count = 0;
    let total_content_count = 0;
    let total_member_count = 0;
    let total_evidence_count = 0;
    const strategyLabels: string[] = [];
    const techLabels: string[] = [];

    for (const bucket of policy.buckets) {
      total_group_count += bucket.groups.length;

      for (const group of bucket.groups) {
        total_content_count += group.contents.length;
        total_member_count += group.member_items.length;
        total_evidence_count += group.contents.reduce((sum, content) => sum + content.evidence.length, 0);

        const strategyTerms = getStrategyTerms(group.taxonomies);
        const techTerms = getTechTerms(group.taxonomies);
        const techSubterms = getTechSubdomainTerms(group.taxonomies);
        const primaryStrategy = strategyTerms.find((term) => term.is_primary) ?? strategyTerms[0] ?? null;
        const group_review_status = getGroupReviewStatus(group.policy_item_group_id, support);
        const mapping_review_status = getMappingReviewStatus(group.policy_item_group_id, techTerms, support);
        const representative_member =
          group.member_items.find((member) => member.is_representative) ?? group.member_items[0] ?? null;

        strategyLabels.push(...strategyTerms.map((term) => term.label));
        techLabels.push(...techTerms.map((term) => term.label));

        for (const strategy of strategyTerms) {
          const current = strategyAccumulator.get(strategy.term_id) ?? {
            term_id: strategy.term_id,
            label: strategy.label,
            group_count: 0,
            content_count: 0,
          };
          current.group_count += 1;
          current.content_count += group.contents.length;
          strategyAccumulator.set(strategy.term_id, current);
        }

        for (const tech of techTerms) {
          const current = techAccumulator.get(tech.term_id) ?? {
            term_id: tech.term_id,
            label: tech.label,
            group_count: 0,
            content_count: 0,
          };
          current.group_count += 1;
          current.content_count += group.contents.length;
          techAccumulator.set(tech.term_id, current);
        }

        for (const content of [...group.contents].sort((left, right) => left.display_order - right.display_order)) {
          const primary_source_asset = content.evidence[0]?.source_assets[0] ?? null;
          const preferred_source_asset = pickPreferredSourceAsset(content);
          const content_review_status = getContentReviewStatus(content.policy_item_content_id, support);
          const projection_status = getProjectionStatus(group_review_status, content_review_status);
          const source_asset_count = new Set(
            content.evidence.flatMap((evidence) => evidence.source_assets.map((sourceAsset) => sourceAsset.source_asset_id)),
          ).size;
          const representation_types = [...new Set(content.evidence.map((evidence) => evidence.representation_type))];
          const figure_evidence_count = content.evidence.filter((evidence) => evidence.representation_type === "figure_or_diagram").length;
          const location_labels = uniqueLabels(
            content.evidence
              .map((evidence) => evidence.location_value)
              .filter((value): value is string => Boolean(value)),
          );

          for (const representationType of representation_types) {
            const current = representationAccumulator.get(representationType) ?? {
              representation_type: representationType,
              evidence_count: 0,
              content_count: 0,
            };

            current.evidence_count += content.evidence.filter((evidence) => evidence.representation_type === representationType).length;
            current.content_count += 1;
            representationAccumulator.set(representationType, current);
          }

          const search_text = [
            policy.policy_name,
            bucket.resource_category_label,
            group.group_label,
            group.group_summary,
            group.group_description,
            content.content_label,
            content.content_statement,
            content.content_summary,
            content.content_type,
            ...strategyTerms.map((term) => term.label),
            ...techTerms.map((term) => term.label),
            ...techSubterms.map((term) => term.label),
            ...representation_types,
            ...group.member_items.flatMap((member) => [member.item_label, member.item_statement]),
            ...content.evidence.flatMap((evidence) => [evidence.source_policy_item_label, evidence.evidence_text, evidence.location_value]),
          ]
            .join(" ")
            .toLowerCase();

          content_rows.push({
            policy_id: policy.policy_id,
            policy_name: policy.policy_name,
            policy_order: index + 1,
            policy_bucket_id: bucket.policy_bucket_id,
            resource_category_id: bucket.resource_category_id as ContentRow["resource_category_id"],
            resource_category_label: bucket.resource_category_label,
            policy_item_group_id: group.policy_item_group_id,
            group_label: group.group_label,
            group_summary: group.group_summary,
            group_description: group.group_description,
            policy_item_content_id: content.policy_item_content_id,
            content_label: content.content_label,
            content_statement: content.content_statement,
            content_summary: content.content_summary,
            content_type: content.content_type,
            display_order: content.display_order,
            member_count: group.member_items.length,
            evidence_count: content.evidence.length,
            source_asset_count,
            figure_evidence_count,
            primary_strategy: primaryStrategy,
            strategy_terms: strategyTerms,
            tech_terms: techTerms,
            tech_subterms: techSubterms,
            representation_types,
            representative_member,
            primary_source_asset,
            preferred_source_asset,
            location_labels,
            content_review_status,
            group_review_status,
            mapping_review_status,
            projection_status,
            search_text,
          });
        }
      }
    }

    return {
      ...policy,
      policy_order: index + 1,
      total_group_count,
      total_content_count,
      total_member_count,
      total_evidence_count,
      strategy_labels: uniqueLabels(strategyLabels),
      tech_labels: uniqueLabels(techLabels),
    };
  });

  const policyMap = new Map(policies.map((policy) => [policy.policy_id, policy]));
  const sortedContentRows = content_rows.sort((left, right) => {
    if (left.policy_order !== right.policy_order) {
      return left.policy_order - right.policy_order;
    }

    if (left.resource_category_id !== right.resource_category_id) {
      return (CATEGORY_ORDER[left.resource_category_id] ?? 99) - (CATEGORY_ORDER[right.resource_category_id] ?? 99);
    }

    if (left.group_label !== right.group_label) {
      return left.group_label.localeCompare(right.group_label, "ko");
    }

    return left.display_order - right.display_order;
  });

  for (const policy of policies) {
    for (const bucket of policy.buckets) {
      for (const group of bucket.groups) {
        const strategy_terms = getStrategyTerms(group.taxonomies);
        const tech_terms = getTechTerms(group.taxonomies);
        const tech_subterms = getTechSubdomainTerms(group.taxonomies);
        const primary_strategy = strategy_terms.find((term) => term.is_primary) ?? strategy_terms[0] ?? null;
        const group_review_status = getGroupReviewStatus(group.policy_item_group_id, support);
        const mapping_review_status = getMappingReviewStatus(group.policy_item_group_id, tech_terms, support);
        const representative_member =
          group.member_items.find((member) => member.is_representative) ?? group.member_items[0] ?? null;

        for (const content of group.contents) {
          const primary_source_asset = content.evidence[0]?.source_assets[0] ?? null;
          const preferred_source_asset = pickPreferredSourceAsset(content);
          const content_review_status = getContentReviewStatus(content.policy_item_content_id, support);
          const projection_status = getProjectionStatus(group_review_status, content_review_status);
          const location_labels = uniqueLabels(
            content.evidence
              .map((evidence) => evidence.location_value)
              .filter((value): value is string => Boolean(value)),
          );

          contentContextMap.set(content.policy_item_content_id, {
            policy,
            bucket,
            group,
            content,
            strategy_terms,
            tech_terms,
            tech_subterms,
            primary_strategy,
            representative_member,
            primary_source_asset,
            preferred_source_asset,
            location_labels,
            content_review_status,
            group_review_status,
            mapping_review_status,
            projection_status,
          });
        }
      }
    }
  }

  const strategy_filters = [...strategyAccumulator.values()].sort((left, right) =>
    right.content_count === left.content_count
      ? left.label.localeCompare(right.label, "ko")
      : right.content_count - left.content_count,
  );
  const tech_domain_filters = [...techAccumulator.values()].sort((left, right) =>
    right.content_count === left.content_count
      ? left.label.localeCompare(right.label, "ko")
      : right.content_count - left.content_count,
  );
  const representation_summaries = [...representationAccumulator.values()].sort((left, right) =>
    right.evidence_count === left.evidence_count
      ? left.representation_type.localeCompare(right.representation_type, "en")
      : right.evidence_count - left.evidence_count,
  );

  return {
    sample_scope: input.sample_scope,
    stats: {
      policy_count: summary.policy_count,
      group_count: summary.group_count,
      content_count: summary.content_count,
      group_member_count: summary.group_member_count,
      content_evidence_count: summary.content_evidence_count,
      group_taxonomy_count: summary.group_taxonomy_count,
      display_text_count: summary.display_text_count,
    },
    policies,
    resource_categories,
    strategy_filters,
    tech_domain_filters,
    representation_summaries,
    content_rows: sortedContentRows,
    policyMap,
    strategyFilterMap: new Map(strategy_filters.map((entry) => [entry.term_id, entry])),
    techDomainFilterMap: new Map(tech_domain_filters.map((entry) => [entry.term_id, entry])),
    contentContextMap,
  };
}
