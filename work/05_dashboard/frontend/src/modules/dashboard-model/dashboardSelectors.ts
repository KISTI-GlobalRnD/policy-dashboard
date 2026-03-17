import type {
  ContentContext,
  ContentRow,
  DashboardDataset,
  DashboardPolicy,
  ProjectionFilterId,
  ProjectionStatus,
  ResourceCategoryId,
  StrategyFilter,
  TechDomainFilter,
} from "../dashboard-data/dashboard.types";

export const CATEGORY_META = {
  technology: {
    label: "기술",
    shortLabel: "TECH",
    description: "R&D, 성능 고도화, 실증과 공통기반 지원 영역",
  },
  infrastructure_institutional: {
    label: "인프라·제도",
    shortLabel: "INFRA",
    description: "플랫폼, 거버넌스, 규제·운영 체계를 포함하는 영역",
  },
  talent: {
    label: "인재",
    shortLabel: "TALENT",
    description: "융합 교육, 전문인력 양성, 재교육을 다루는 영역",
  },
} as const;

type CategoryKey = Exclude<ResourceCategoryId, "all">;

export type PolicyBucketSignal = {
  policy_bucket_id: string;
  resource_category_id: CategoryKey;
  label: string;
  group_count: number;
  content_count: number;
  matched_group_count: number;
  matched_content_count: number;
};

export type PolicyView = {
  policy: DashboardPolicy;
  matchedRows: ContentRow[];
  visibleRows: ContentRow[];
  matchedGroupCount: number;
  matchedContentCount: number;
  visibleContentCount: number;
  curatedContentCount: number;
  provisionalContentCount: number;
  projectionStatus: "curated" | "provisional" | "mixed";
  primaryStrategyLabel: string;
  bucketSignals: PolicyBucketSignal[];
};

export type ActiveTrace = {
  row: ContentRow;
  context: ContentContext;
};

export type OverviewCategoryView = {
  resourceCategoryId: CategoryKey;
  label: string;
  shortLabel: string;
  description: string;
  totalGroupCount: number;
  totalContentCount: number;
  filteredGroupCount: number;
  filteredContentCount: number;
  filteredPolicyCount: number;
  ratio: number;
  isFocused: boolean;
};

export type FacetOption = {
  termId: string;
  label: string;
  groupCount: number;
  contentCount: number;
  isSelected: boolean;
};

export type DashboardViewModel = {
  filteredRows: ContentRow[];
  policyViews: PolicyView[];
  activePolicyView: PolicyView | null;
  activeRows: ContentRow[];
  activeTrace: ActiveTrace | null;
  overviewByCategory: OverviewCategoryView[];
  availableStrategyOptions: FacetOption[];
  availableTechDomainOptions: FacetOption[];
  strategyScopeContentCount: number;
  techDomainScopeContentCount: number;
  projectionScopeContentCount: number;
  curatedProjectionContentCount: number;
  provisionalProjectionContentCount: number;
  suggestedResourceCategoryId: ResourceCategoryId;
  suggestedStrategyTermId: string;
  suggestedTechDomainId: string;
  suggestedProjectionStatus: ProjectionFilterId;
  suggestedActivePolicyId: string | null;
  suggestedActiveContentId: string | null;
  visiblePolicyCount: number;
  matchedContentCount: number;
  visibleContentCount: number;
};

type BuildViewModelOptions = {
  search: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainId: string;
  projectionStatus: ProjectionFilterId;
  rowLimit: number;
  activePolicyId: string | null;
  activeContentId: string | null;
};

function normalizeText(value: string | undefined) {
  return String(value ?? "").trim().toLowerCase();
}

function uniqueCount(values: string[]) {
  return new Set(values).size;
}

function rowMatchesSearch(row: ContentRow, query: string) {
  if (!query) {
    return true;
  }

  return row.search_text.includes(query);
}

function rowMatchesStrategy(row: ContentRow, strategyTermId: string) {
  if (strategyTermId === "all") {
    return true;
  }

  return row.strategy_terms.some((term) => term.term_id === strategyTermId);
}

function rowMatchesTechDomain(row: ContentRow, techDomainId: string) {
  if (techDomainId === "all") {
    return true;
  }

  return row.tech_terms.some((term) => term.term_id === techDomainId);
}

function rowMatchesProjection(row: ContentRow, projectionStatus: ProjectionFilterId) {
  if (projectionStatus === "all") {
    return true;
  }

  return row.projection_status === projectionStatus;
}

function buildPolicyView(policy: DashboardPolicy, matchedRows: ContentRow[], rowLimit: number): PolicyView {
  const visibleRows = rowLimit >= 9999 ? matchedRows : matchedRows.slice(0, rowLimit);
  const primaryStrategyLabel = policy.strategy_labels[0] ?? "전략 미지정";
  const curatedContentCount = matchedRows.filter((row) => row.projection_status === "curated").length;
  const provisionalContentCount = matchedRows.length - curatedContentCount;
  const projectionStatus =
    curatedContentCount === 0 ? "provisional" : provisionalContentCount === 0 ? "curated" : "mixed";
  const bucketSignals = policy.buckets.map((bucket) => {
    const bucketRows = matchedRows.filter((row) => row.policy_bucket_id === bucket.policy_bucket_id);
    const totalContentCount = bucket.groups.reduce((sum, group) => sum + group.contents.length, 0);

    return {
      policy_bucket_id: bucket.policy_bucket_id,
      resource_category_id: bucket.resource_category_id as CategoryKey,
      label: bucket.resource_category_label,
      group_count: bucket.groups.length,
      content_count: totalContentCount,
      matched_group_count: uniqueCount(bucketRows.map((row) => row.policy_item_group_id)),
      matched_content_count: bucketRows.length,
    };
  });

  return {
    policy,
    matchedRows,
    visibleRows,
    matchedGroupCount: uniqueCount(matchedRows.map((row) => row.policy_item_group_id)),
    matchedContentCount: matchedRows.length,
    visibleContentCount: visibleRows.length,
    curatedContentCount,
    provisionalContentCount,
    projectionStatus,
    primaryStrategyLabel,
    bucketSignals,
  };
}

function buildOverviewByCategory(
  dataset: DashboardDataset,
  filteredRows: ContentRow[],
  resourceCategoryId: ResourceCategoryId,
): OverviewCategoryView[] {
  return dataset.resource_categories.map((category) => {
    const meta = CATEGORY_META[category.resource_category_id];
    const categoryRows = dataset.content_rows.filter((row) => row.resource_category_id === category.resource_category_id);
    const filteredCategoryRows = filteredRows.filter((row) => row.resource_category_id === category.resource_category_id);

    return {
      resourceCategoryId: category.resource_category_id,
      label: category.display_label,
      shortLabel: meta?.shortLabel ?? category.display_label,
      description: meta?.description ?? "분류 설명 없음",
      totalGroupCount: uniqueCount(categoryRows.map((row) => row.policy_item_group_id)),
      totalContentCount: categoryRows.length,
      filteredGroupCount: uniqueCount(filteredCategoryRows.map((row) => row.policy_item_group_id)),
      filteredContentCount: filteredCategoryRows.length,
      filteredPolicyCount: uniqueCount(filteredCategoryRows.map((row) => row.policy_id)),
      ratio:
        categoryRows.length === 0 ? 0 : Math.round((filteredCategoryRows.length / categoryRows.length) * 100),
      isFocused: resourceCategoryId === category.resource_category_id,
    };
  });
}

function buildFacetOptions(
  filters: StrategyFilter[] | TechDomainFilter[],
  rows: ContentRow[],
  selectedId: string,
  pickTerms: (row: ContentRow) => { term_id: string; label: string }[],
): FacetOption[] {
  const accumulator = new Map<
    string,
    {
      label: string;
      groupIds: Set<string>;
      contentCount: number;
    }
  >();

  for (const row of rows) {
    for (const term of pickTerms(row)) {
      const current = accumulator.get(term.term_id) ?? {
        label: term.label,
        groupIds: new Set<string>(),
        contentCount: 0,
      };

      current.groupIds.add(row.policy_item_group_id);
      current.contentCount += 1;
      accumulator.set(term.term_id, current);
    }
  }

  return filters.flatMap((filter) => {
    const entry = accumulator.get(filter.term_id);
    const contentCount = entry?.contentCount ?? 0;

    if (contentCount === 0 && selectedId !== filter.term_id) {
      return [];
    }

    return [
      {
        termId: filter.term_id,
        label: filter.label,
        groupCount: entry?.groupIds.size ?? 0,
        contentCount,
        isSelected: selectedId === filter.term_id,
      },
    ];
  });
}

export function buildDashboardViewModel(
  dataset: DashboardDataset,
  options: BuildViewModelOptions,
): DashboardViewModel {
  const query = normalizeText(options.search);
  const suggestedStrategyTermId =
    options.strategyTermId === "all" || dataset.strategyFilterMap.has(options.strategyTermId)
      ? options.strategyTermId
      : "all";
  const suggestedTechDomainId =
    options.techDomainId === "all" || dataset.techDomainFilterMap.has(options.techDomainId) ? options.techDomainId : "all";
  const suggestedProjectionStatus =
    options.projectionStatus === "curated" || options.projectionStatus === "provisional" ? options.projectionStatus : "all";

  const strategyScopedRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesTechDomain(row, suggestedTechDomainId) &&
      rowMatchesProjection(row, suggestedProjectionStatus),
  );
  const techDomainScopedRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesStrategy(row, suggestedStrategyTermId) &&
      rowMatchesProjection(row, suggestedProjectionStatus),
  );
  const projectionScopedRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesStrategy(row, suggestedStrategyTermId) &&
      rowMatchesTechDomain(row, suggestedTechDomainId),
  );
  const filteredRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesStrategy(row, suggestedStrategyTermId) &&
      rowMatchesTechDomain(row, suggestedTechDomainId) &&
      rowMatchesProjection(row, suggestedProjectionStatus),
  );
  const hasFilter =
    Boolean(query) ||
    suggestedStrategyTermId !== "all" ||
    suggestedTechDomainId !== "all" ||
    suggestedProjectionStatus !== "all";

  const policyViews = dataset.policies
    .map((policy) => {
      const matchedRows = filteredRows.filter((row) => row.policy_id === policy.policy_id);
      if (hasFilter && matchedRows.length === 0) {
        return null;
      }

      return buildPolicyView(policy, matchedRows, options.rowLimit);
    })
    .filter((entry): entry is PolicyView => entry !== null);

  const suggestedActivePolicyId =
    policyViews.find((entry) => entry.policy.policy_id === options.activePolicyId)?.policy.policy_id ??
    policyViews[0]?.policy.policy_id ??
    null;

  const activePolicyView = policyViews.find((entry) => entry.policy.policy_id === suggestedActivePolicyId) ?? null;
  const suggestedResourceCategoryId =
    options.resourceCategoryId !== "all" &&
    activePolicyView?.matchedRows.some((row) => row.resource_category_id === options.resourceCategoryId)
      ? options.resourceCategoryId
      : "all";

  const categoryScopedRows =
    activePolicyView?.matchedRows.filter(
      (row) => suggestedResourceCategoryId === "all" || row.resource_category_id === suggestedResourceCategoryId,
    ) ?? [];
  const activeRows = options.rowLimit >= 9999 ? categoryScopedRows : categoryScopedRows.slice(0, options.rowLimit);

  const suggestedActiveContentId =
    activeRows.find((row) => row.policy_item_content_id === options.activeContentId)?.policy_item_content_id ??
    activeRows[0]?.policy_item_content_id ??
    null;

  const activeRow = activePolicyView?.matchedRows.find((row) => row.policy_item_content_id === suggestedActiveContentId) ?? null;
  const activeContext = activeRow ? dataset.contentContextMap.get(activeRow.policy_item_content_id) ?? null : null;

  return {
    filteredRows,
    policyViews,
    activePolicyView,
    activeRows,
    activeTrace: activeRow && activeContext ? { row: activeRow, context: activeContext } : null,
    overviewByCategory: buildOverviewByCategory(dataset, filteredRows, suggestedResourceCategoryId),
    availableStrategyOptions: buildFacetOptions(
      dataset.strategy_filters,
      strategyScopedRows,
      suggestedStrategyTermId,
      (row) => row.strategy_terms,
    ),
    availableTechDomainOptions: buildFacetOptions(
      dataset.tech_domain_filters,
      techDomainScopedRows,
      suggestedTechDomainId,
      (row) => row.tech_terms,
    ),
    strategyScopeContentCount: strategyScopedRows.length,
    techDomainScopeContentCount: techDomainScopedRows.length,
    projectionScopeContentCount: projectionScopedRows.length,
    curatedProjectionContentCount: projectionScopedRows.filter((row) => row.projection_status === "curated").length,
    provisionalProjectionContentCount: projectionScopedRows.filter((row) => row.projection_status === "provisional").length,
    suggestedResourceCategoryId,
    suggestedStrategyTermId,
    suggestedTechDomainId,
    suggestedProjectionStatus,
    suggestedActivePolicyId,
    suggestedActiveContentId,
    visiblePolicyCount: policyViews.length,
    matchedContentCount: filteredRows.length,
    visibleContentCount: activeRows.length,
  };
}
