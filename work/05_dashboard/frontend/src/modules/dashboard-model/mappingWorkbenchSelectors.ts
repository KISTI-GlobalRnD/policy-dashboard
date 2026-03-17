import type {
  ContentContext,
  ContentRow,
  DashboardDataset,
  DashboardPolicy,
  ResourceCategoryId,
  StrategyFilter,
} from "../dashboard-data/dashboard.types";
import type { MappingStatusFilter, ReviewStatusFilter } from "./mappingWorkbenchStore";
import { TECH_DOMAIN_REFERENCES, TECH_DOMAIN_REFERENCE_MAP, type TechDomainReference } from "./techDomainCatalog";

export type MatrixDomainId = string;

export type ActiveTrace = {
  row: ContentRow;
  context: ContentContext;
};

export type FacetOption = {
  value: string;
  label: string;
  count: number;
  isSelected: boolean;
};

export type ResourceMixEntry = {
  resourceCategoryId: Exclude<ResourceCategoryId, "all">;
  label: string;
  count: number;
};

export type ReviewStateSummary = "reviewed" | "needs_review" | "mixed" | "empty";

export type MatrixDomainSummary = TechDomainReference & {
  groupCount: number;
  contentCount: number;
  mappedPolicyCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  isSelected: boolean;
};

export type PolicyTechMatrixCell = {
  key: string;
  policyId: string;
  techDomainId: MatrixDomainId;
  techDomainLabel: string;
  shortLabel: string;
  rows: ContentRow[];
  groupCount: number;
  contentCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  reviewStatus: ReviewStateSummary;
  resourceMix: ResourceMixEntry[];
  strategyLabels: string[];
  isSelected: boolean;
  isActiveRow: boolean;
  isActiveColumn: boolean;
  intensity: number;
};

export type PolicyTechMatrixRow = {
  policy: DashboardPolicy;
  cells: PolicyTechMatrixCell[];
  mappedDomainCount: number;
  mappedContentCount: number;
  unmappedContentCount: number;
  totalEvidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
};

export type PolicySummaryView = {
  policy: DashboardPolicy;
  mappedDomainCount: number;
  mappedContentCount: number;
  unmappedContentCount: number;
  totalEvidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  topDomains: MatrixDomainSummary[];
};

export type DomainPolicyView = {
  policyId: string;
  policyName: string;
  groupCount: number;
  contentCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
};

export type DomainSummaryView = {
  domain: MatrixDomainSummary;
  policyCount: number;
  groupCount: number;
  contentCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  policies: DomainPolicyView[];
  strategyLabels: string[];
};

export type CellGroupView = {
  groupId: string;
  label: string;
  summary: string;
  resourceMix: ResourceMixEntry[];
  contentCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  reviewStatus: ReviewStateSummary;
  groupReviewStatus: ContentRow["group_review_status"];
  strategyLabels: string[];
};

export type MappingWorkbenchViewModel = {
  filteredRows: ContentRow[];
  matrixDomains: MatrixDomainSummary[];
  matrixRows: PolicyTechMatrixRow[];
  selectedCell: PolicyTechMatrixCell | null;
  selectedCellContents: ContentRow[];
  selectedCellGroups: CellGroupView[];
  selectedPolicyUnmappedContents: ContentRow[];
  selectedPolicySummary: PolicySummaryView | null;
  selectedDomainSummary: DomainSummaryView | null;
  activeTrace: ActiveTrace | null;
  availablePolicies: FacetOption[];
  availableStrategies: FacetOption[];
  availableTechDomains: FacetOption[];
  availableReviewStatuses: FacetOption[];
  visiblePolicyCount: number;
  mappedDomainCount: number;
  mappedGroupCount: number;
  mappedContentCount: number;
  unmappedContentCount: number;
  evidenceReadyContentCount: number;
  reviewedContentCount: number;
  needsReviewContentCount: number;
  suggestedInspectorPolicyId: string | null;
  suggestedInspectorTechDomainId: string | null;
  suggestedActiveContentId: string | null;
};

type BuildMappingWorkbenchViewModelOptions = {
  search: string;
  policyFilterId: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainFilterId: string;
  mappingStatus: MappingStatusFilter;
  reviewStatus: ReviewStatusFilter;
  inspectorPolicyId: string | null;
  inspectorTechDomainId: string | null;
  activeContentId: string | null;
};

const UNMAPPED_DOMAIN = {
  termId: "unmapped",
  label: "미매핑",
  shortLabel: "GAP",
} as const;

const RESOURCE_CATEGORY_LABELS: Record<Exclude<ResourceCategoryId, "all">, string> = {
  technology: "기술",
  infrastructure_institutional: "인프라·제도",
  talent: "인재",
};

function normalizeText(value: string | undefined) {
  return String(value ?? "").trim().toLowerCase();
}

function uniqueCount(values: string[]) {
  return new Set(values).size;
}

function hasTechDomain(row: ContentRow, techDomainId: string) {
  return row.tech_terms.some((term) => term.term_id === techDomainId);
}

function rowMatchesSearch(row: ContentRow, query: string) {
  return !query || row.search_text.includes(query);
}

function rowMatchesPolicy(row: ContentRow, policyFilterId: string) {
  return policyFilterId === "all" || row.policy_id === policyFilterId;
}

function rowMatchesResource(row: ContentRow, resourceCategoryId: ResourceCategoryId) {
  return resourceCategoryId === "all" || row.resource_category_id === resourceCategoryId;
}

function rowMatchesStrategy(row: ContentRow, strategyTermId: string) {
  return strategyTermId === "all" || row.strategy_terms.some((term) => term.term_id === strategyTermId);
}

function rowMatchesTechFilter(row: ContentRow, techDomainFilterId: string) {
  return techDomainFilterId === "all" || hasTechDomain(row, techDomainFilterId);
}

function rowMatchesMapping(row: ContentRow, mappingStatus: MappingStatusFilter) {
  if (mappingStatus === "all") {
    return true;
  }

  if (mappingStatus === "mapped") {
    return row.tech_terms.length > 0;
  }

  return row.tech_terms.length === 0;
}

function rowMatchesReview(row: ContentRow, reviewStatus: ReviewStatusFilter) {
  return reviewStatus === "all" || row.mapping_review_status === reviewStatus;
}

function summarizeReviewState(rows: ContentRow[]): ReviewStateSummary {
  if (rows.length === 0) {
    return "empty";
  }

  const reviewedCount = rows.filter((row) => row.mapping_review_status === "reviewed").length;
  if (reviewedCount === rows.length) {
    return "reviewed";
  }

  if (reviewedCount === 0) {
    return "needs_review";
  }

  return "mixed";
}

function buildResourceMix(rows: ContentRow[]): ResourceMixEntry[] {
  const counts = new Map<Exclude<ResourceCategoryId, "all">, number>();

  for (const row of rows) {
    counts.set(row.resource_category_id, (counts.get(row.resource_category_id) ?? 0) + 1);
  }

  return [...counts.entries()]
    .map(([resourceCategoryId, count]) => ({
      resourceCategoryId,
      label: RESOURCE_CATEGORY_LABELS[resourceCategoryId],
      count,
    }))
    .sort((left, right) => right.count - left.count);
}

function buildStrategyLabels(rows: ContentRow[]) {
  return [...new Set(rows.flatMap((row) => row.strategy_terms.map((term) => term.label)))].sort((left, right) =>
    left.localeCompare(right, "ko"),
  );
}

function sortRows(rows: ContentRow[]) {
  return [...rows].sort((left, right) => {
    if (left.policy_order !== right.policy_order) {
      return left.policy_order - right.policy_order;
    }

    if (left.group_label !== right.group_label) {
      return left.group_label.localeCompare(right.group_label, "ko");
    }

    return left.display_order - right.display_order;
  });
}

function buildFacetOptions(
  values: Array<{ value: string; label: string }>,
  counts: Map<string, number>,
  selectedValue: string,
) {
  return values.map((entry) => ({
    value: entry.value,
    label: entry.label,
    count: counts.get(entry.value) ?? 0,
    isSelected: selectedValue === entry.value,
  }));
}

function buildStrategyFacetOptions(filters: StrategyFilter[], rows: ContentRow[], selectedValue: string) {
  const counts = new Map<string, number>();

  for (const row of rows) {
    for (const term of row.strategy_terms) {
      counts.set(term.term_id, (counts.get(term.term_id) ?? 0) + 1);
    }
  }

  return buildFacetOptions(
    filters.map((entry) => ({ value: entry.term_id, label: entry.label })),
    counts,
    selectedValue,
  );
}

function buildTechFacetOptions(rows: ContentRow[], selectedValue: string) {
  const counts = new Map<string, number>();

  for (const row of rows) {
    for (const term of row.tech_terms) {
      counts.set(term.term_id, (counts.get(term.term_id) ?? 0) + 1);
    }
  }

  return buildFacetOptions(
    TECH_DOMAIN_REFERENCES.filter((entry) => counts.get(entry.termId) !== 0 || entry.termId === selectedValue).map((entry) => ({
      value: entry.termId,
      label: entry.label,
    })),
    counts,
    selectedValue,
  );
}

function buildReviewFacetOptions(rows: ContentRow[], selectedValue: ReviewStatusFilter) {
  const counts = new Map<string, number>();

  for (const row of rows) {
    counts.set(row.mapping_review_status, (counts.get(row.mapping_review_status) ?? 0) + 1);
  }

  return buildFacetOptions(
    [
      { value: "reviewed", label: "리뷰 완료" },
      { value: "needs_review", label: "리뷰 필요" },
    ],
    counts,
    selectedValue,
  );
}

function buildDomainSummary(domain: TechDomainReference, rows: ContentRow[], selectedDomainId: string | null): MatrixDomainSummary {
  return {
    ...domain,
    groupCount: uniqueCount(rows.map((row) => row.policy_item_group_id)),
    contentCount: rows.length,
    mappedPolicyCount: uniqueCount(rows.map((row) => row.policy_id)),
    evidenceCount: rows.reduce((sum, row) => sum + row.evidence_count, 0),
    reviewedContentCount: rows.filter((row) => row.mapping_review_status === "reviewed").length,
    needsReviewContentCount: rows.filter((row) => row.mapping_review_status === "needs_review").length,
    isSelected: selectedDomainId === domain.termId,
  };
}

export function buildMappingWorkbenchViewModel(
  dataset: DashboardDataset,
  options: BuildMappingWorkbenchViewModelOptions,
): MappingWorkbenchViewModel {
  const query = normalizeText(options.search);
  const validPolicyFilterId =
    options.policyFilterId === "all" || dataset.policyMap.has(options.policyFilterId) ? options.policyFilterId : "all";
  const validStrategyTermId =
    options.strategyTermId === "all" || dataset.strategyFilterMap.has(options.strategyTermId)
      ? options.strategyTermId
      : "all";
  const validTechDomainFilterId =
    options.techDomainFilterId === "all" || TECH_DOMAIN_REFERENCE_MAP.has(options.techDomainFilterId)
      ? options.techDomainFilterId
      : "all";
  const validReviewStatus = options.reviewStatus === "reviewed" || options.reviewStatus === "needs_review" ? options.reviewStatus : "all";

  const filteredRows = sortRows(
    dataset.content_rows.filter(
      (row) =>
        rowMatchesSearch(row, query) &&
        rowMatchesPolicy(row, validPolicyFilterId) &&
        rowMatchesResource(row, options.resourceCategoryId) &&
        rowMatchesStrategy(row, validStrategyTermId) &&
        rowMatchesTechFilter(row, validTechDomainFilterId) &&
        rowMatchesMapping(row, options.mappingStatus) &&
        rowMatchesReview(row, validReviewStatus),
    ),
  );

  const visiblePolicies =
    validPolicyFilterId === "all"
      ? dataset.policies
      : dataset.policies.filter((policy) => policy.policy_id === validPolicyFilterId);

  const visibleDomainRefs =
    validTechDomainFilterId === "all"
      ? TECH_DOMAIN_REFERENCES
      : TECH_DOMAIN_REFERENCES.filter((entry) => entry.termId === validTechDomainFilterId);

  const matrixDomains = [
    ...visibleDomainRefs
      .map((domain) =>
        buildDomainSummary(
          domain,
          filteredRows.filter((row) => hasTechDomain(row, domain.termId)),
          options.inspectorPolicyId ? null : options.inspectorTechDomainId,
        ),
      )
      .filter(
        (domain) =>
          domain.contentCount > 0 ||
          (options.inspectorPolicyId === null && options.inspectorTechDomainId === domain.termId) ||
          validTechDomainFilterId === domain.termId,
      ),
    ...[
      buildDomainSummary(
        UNMAPPED_DOMAIN,
        filteredRows.filter((row) => row.tech_terms.length === 0),
        options.inspectorPolicyId ? null : options.inspectorTechDomainId,
      ),
    ].filter(
      (domain) =>
        domain.contentCount > 0 ||
        domain.termId === options.inspectorTechDomainId,
    ),
  ];

  const maxCellContentCount =
    Math.max(
      1,
      ...visiblePolicies.flatMap((policy) =>
        matrixDomains.map(
          (domain) =>
            filteredRows.filter(
              (row) =>
                row.policy_id === policy.policy_id &&
                (domain.termId === UNMAPPED_DOMAIN.termId ? row.tech_terms.length === 0 : hasTechDomain(row, domain.termId)),
            ).length,
        ),
      ),
    ) || 1;

  const matrixRows = visiblePolicies
    .map((policy) => {
      const policyRows = filteredRows.filter((row) => row.policy_id === policy.policy_id);
      const cells = matrixDomains.map((domain) => {
        const rows = policyRows.filter((row) =>
          domain.termId === UNMAPPED_DOMAIN.termId ? row.tech_terms.length === 0 : hasTechDomain(row, domain.termId),
        );
      const contentCount = rows.length;
      const evidenceCount = rows.reduce((sum, row) => sum + row.evidence_count, 0);
      const reviewedContentCount = rows.filter((row) => row.mapping_review_status === "reviewed").length;
      const needsReviewContentCount = rows.filter((row) => row.mapping_review_status === "needs_review").length;

      return {
        key: `${policy.policy_id}:${domain.termId}`,
        policyId: policy.policy_id,
        techDomainId: domain.termId,
        techDomainLabel: domain.label,
        shortLabel: domain.shortLabel,
        rows,
        groupCount: uniqueCount(rows.map((row) => row.policy_item_group_id)),
        contentCount,
        evidenceCount,
        reviewedContentCount,
        needsReviewContentCount,
        reviewStatus: summarizeReviewState(rows),
        resourceMix: buildResourceMix(rows),
        strategyLabels: buildStrategyLabels(rows),
        isSelected: options.inspectorPolicyId === policy.policy_id && options.inspectorTechDomainId === domain.termId,
        isActiveRow: options.inspectorPolicyId === policy.policy_id,
        isActiveColumn: !options.inspectorPolicyId && options.inspectorTechDomainId === domain.termId,
        intensity: Math.round((contentCount / maxCellContentCount) * 100),
      } satisfies PolicyTechMatrixCell;
    });

      return {
        policy,
        cells,
        mappedDomainCount: cells.filter((cell) => cell.techDomainId !== UNMAPPED_DOMAIN.termId && cell.contentCount > 0).length,
        mappedContentCount: policyRows.filter((row) => row.tech_terms.length > 0).length,
        unmappedContentCount: policyRows.filter((row) => row.tech_terms.length === 0).length,
        totalEvidenceCount: policyRows.reduce((sum, row) => sum + row.evidence_count, 0),
        reviewedContentCount: policyRows.filter((row) => row.mapping_review_status === "reviewed").length,
        needsReviewContentCount: policyRows.filter((row) => row.mapping_review_status === "needs_review").length,
      } satisfies PolicyTechMatrixRow;
    })
    .filter((row) => row.mappedContentCount > 0 || row.unmappedContentCount > 0);

  const validInspectorPolicyId =
    options.inspectorPolicyId && matrixRows.some((row) => row.policy.policy_id === options.inspectorPolicyId)
      ? options.inspectorPolicyId
      : null;
  const validInspectorTechDomainId =
    options.inspectorTechDomainId &&
    (options.inspectorTechDomainId === UNMAPPED_DOMAIN.termId ||
      matrixDomains.some((domain) => domain.termId === options.inspectorTechDomainId))
      ? options.inspectorTechDomainId
      : null;

  const selectedPolicyRow =
    validInspectorPolicyId === null
      ? null
      : matrixRows.find((row) => row.policy.policy_id === validInspectorPolicyId) ?? null;
  const selectedCell =
    selectedPolicyRow && validInspectorTechDomainId
      ? selectedPolicyRow.cells.find((cell) => cell.techDomainId === validInspectorTechDomainId) ?? null
      : null;
  const selectedCellContents = selectedCell?.rows ?? [];
  const selectedCellGroups = (() => {
    const groups = new Map<string, CellGroupView>();

    for (const row of selectedCellContents) {
      const groupRows = selectedCellContents.filter((entry) => entry.policy_item_group_id === row.policy_item_group_id);
      const current = groups.get(row.policy_item_group_id) ?? {
        groupId: row.policy_item_group_id,
        label: row.group_label,
        summary: row.group_summary || row.group_description,
        resourceMix: [],
        contentCount: 0,
        evidenceCount: 0,
        reviewedContentCount: 0,
        needsReviewContentCount: 0,
        reviewStatus: "empty",
        groupReviewStatus: row.group_review_status,
        strategyLabels: [],
      };

      current.contentCount += 1;
      current.evidenceCount += row.evidence_count;
      current.reviewedContentCount = groupRows.filter((entry) => entry.mapping_review_status === "reviewed").length;
      current.needsReviewContentCount = groupRows.filter((entry) => entry.mapping_review_status === "needs_review").length;
      current.reviewStatus = summarizeReviewState(groupRows);
      current.resourceMix = buildResourceMix(groupRows);
      current.strategyLabels = buildStrategyLabels(groupRows);
      groups.set(row.policy_item_group_id, current);
    }

    return [...groups.values()].sort((left, right) => right.contentCount - left.contentCount);
  })();

  const selectedPolicyUnmappedContents =
    validInspectorPolicyId === null
      ? []
      : sortRows(
          dataset.content_rows.filter(
            (row) =>
              row.policy_id === validInspectorPolicyId &&
              rowMatchesSearch(row, query) &&
              rowMatchesResource(row, options.resourceCategoryId) &&
              rowMatchesStrategy(row, validStrategyTermId) &&
              rowMatchesReview(row, validReviewStatus) &&
              row.tech_terms.length === 0,
          ),
        );

  const selectedPolicySummary =
    selectedPolicyRow && !selectedCell
      ? {
          policy: selectedPolicyRow.policy,
          mappedDomainCount: selectedPolicyRow.mappedDomainCount,
          mappedContentCount: selectedPolicyRow.mappedContentCount,
          unmappedContentCount: selectedPolicyRow.unmappedContentCount,
          totalEvidenceCount: selectedPolicyRow.totalEvidenceCount,
          reviewedContentCount: selectedPolicyRow.reviewedContentCount,
          needsReviewContentCount: selectedPolicyRow.needsReviewContentCount,
          topDomains: selectedPolicyRow.cells
            .filter((cell) => cell.techDomainId !== UNMAPPED_DOMAIN.termId && cell.contentCount > 0)
            .sort((left, right) => right.contentCount - left.contentCount)
            .slice(0, 4)
            .map((cell) => ({
              ...(TECH_DOMAIN_REFERENCE_MAP.get(cell.techDomainId) ?? {
                termId: cell.techDomainId,
                label: cell.techDomainLabel,
                shortLabel: cell.shortLabel,
              }),
              groupCount: cell.groupCount,
              contentCount: cell.contentCount,
              mappedPolicyCount: 1,
              evidenceCount: cell.evidenceCount,
              isSelected: false,
            })),
        }
      : null;

  const selectedDomainSummary =
    !validInspectorPolicyId && validInspectorTechDomainId
      ? (() => {
        const domain = matrixDomains.find((entry) => entry.termId === validInspectorTechDomainId);
        if (!domain) {
          return null;
        }

          const rows = filteredRows.filter((row) =>
            validInspectorTechDomainId === UNMAPPED_DOMAIN.termId
              ? row.tech_terms.length === 0
              : hasTechDomain(row, validInspectorTechDomainId),
          );

          return {
            domain,
            policyCount: uniqueCount(rows.map((row) => row.policy_id)),
            groupCount: uniqueCount(rows.map((row) => row.policy_item_group_id)),
            contentCount: rows.length,
            evidenceCount: rows.reduce((sum, row) => sum + row.evidence_count, 0),
            reviewedContentCount: rows.filter((row) => row.mapping_review_status === "reviewed").length,
            needsReviewContentCount: rows.filter((row) => row.mapping_review_status === "needs_review").length,
            policies: visiblePolicies
              .map((policy) => {
                const policyRows = rows.filter((row) => row.policy_id === policy.policy_id);

                return {
                  policyId: policy.policy_id,
                  policyName: policy.policy_name,
                  groupCount: uniqueCount(policyRows.map((row) => row.policy_item_group_id)),
                  contentCount: policyRows.length,
                  evidenceCount: policyRows.reduce((sum, row) => sum + row.evidence_count, 0),
                  reviewedContentCount: policyRows.filter((row) => row.mapping_review_status === "reviewed").length,
                  needsReviewContentCount: policyRows.filter((row) => row.mapping_review_status === "needs_review").length,
                };
              })
              .filter((entry) => entry.contentCount > 0)
              .sort((left, right) => right.contentCount - left.contentCount),
            strategyLabels: buildStrategyLabels(rows),
          } satisfies DomainSummaryView;
        })()
      : null;

  const activeContentPool =
    selectedCell !== null ? selectedCellContents : selectedPolicySummary !== null ? selectedPolicyUnmappedContents : [];
  const suggestedActiveContentId =
    options.activeContentId && activeContentPool.some((row) => row.policy_item_content_id === options.activeContentId)
      ? options.activeContentId
      : null;
  const activeRow =
    suggestedActiveContentId === null
      ? null
      : activeContentPool.find((row) => row.policy_item_content_id === suggestedActiveContentId) ?? null;
  const activeContext = activeRow ? dataset.contentContextMap.get(activeRow.policy_item_content_id) ?? null : null;

  const policyFacetRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesResource(row, options.resourceCategoryId) &&
      rowMatchesStrategy(row, validStrategyTermId) &&
      rowMatchesTechFilter(row, validTechDomainFilterId) &&
      rowMatchesMapping(row, options.mappingStatus) &&
      rowMatchesReview(row, validReviewStatus),
  );
  const policyFacetCounts = new Map<string, number>();
  for (const row of policyFacetRows) {
    policyFacetCounts.set(row.policy_id, (policyFacetCounts.get(row.policy_id) ?? 0) + 1);
  }

  const strategyFacetRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesPolicy(row, validPolicyFilterId) &&
      rowMatchesResource(row, options.resourceCategoryId) &&
      rowMatchesTechFilter(row, validTechDomainFilterId) &&
      rowMatchesMapping(row, options.mappingStatus) &&
      rowMatchesReview(row, validReviewStatus),
  );

  const techFacetRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesPolicy(row, validPolicyFilterId) &&
      rowMatchesResource(row, options.resourceCategoryId) &&
      rowMatchesStrategy(row, validStrategyTermId) &&
      rowMatchesMapping(row, options.mappingStatus) &&
      rowMatchesReview(row, validReviewStatus),
  );

  const reviewFacetRows = dataset.content_rows.filter(
    (row) =>
      rowMatchesSearch(row, query) &&
      rowMatchesPolicy(row, validPolicyFilterId) &&
      rowMatchesResource(row, options.resourceCategoryId) &&
      rowMatchesStrategy(row, validStrategyTermId) &&
      rowMatchesTechFilter(row, validTechDomainFilterId) &&
      rowMatchesMapping(row, options.mappingStatus),
  );

  return {
    filteredRows,
    matrixDomains,
    matrixRows,
    selectedCell,
    selectedCellContents,
    selectedCellGroups,
    selectedPolicyUnmappedContents,
    selectedPolicySummary,
    selectedDomainSummary,
    activeTrace: activeRow && activeContext ? { row: activeRow, context: activeContext } : null,
    availablePolicies: buildFacetOptions(
      dataset.policies.map((policy) => ({ value: policy.policy_id, label: policy.policy_name })),
      policyFacetCounts,
      validPolicyFilterId,
    ).filter((entry) => entry.count > 0 || entry.value === validPolicyFilterId),
    availableStrategies: buildStrategyFacetOptions(dataset.strategy_filters, strategyFacetRows, validStrategyTermId),
    availableTechDomains: buildTechFacetOptions(techFacetRows, validTechDomainFilterId),
    availableReviewStatuses: buildReviewFacetOptions(reviewFacetRows, validReviewStatus),
    visiblePolicyCount: matrixRows.length,
    mappedDomainCount: matrixDomains.filter((entry) => entry.termId !== UNMAPPED_DOMAIN.termId && entry.contentCount > 0).length,
    mappedGroupCount: uniqueCount(filteredRows.filter((row) => row.tech_terms.length > 0).map((row) => row.policy_item_group_id)),
    mappedContentCount: filteredRows.filter((row) => row.tech_terms.length > 0).length,
    unmappedContentCount: filteredRows.filter((row) => row.tech_terms.length === 0).length,
    evidenceReadyContentCount: filteredRows.filter((row) => row.evidence_count > 0).length,
    reviewedContentCount: filteredRows.filter((row) => row.mapping_review_status === "reviewed").length,
    needsReviewContentCount: filteredRows.filter((row) => row.mapping_review_status === "needs_review").length,
    suggestedInspectorPolicyId: validInspectorPolicyId,
    suggestedInspectorTechDomainId: validInspectorTechDomainId,
    suggestedActiveContentId,
  };
}
