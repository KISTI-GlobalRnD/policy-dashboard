import type { ChangeEvent } from "react";
import { Chip } from "../../shared/ui/Chip";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type { DashboardDataset, ProjectionFilterId, ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { FacetOption } from "../dashboard-model/dashboardSelectors";
import styles from "./DashboardWorkbenchPage.module.css";

type FilterBarProps = {
  dataset: DashboardDataset;
  search: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainId: string;
  projectionStatus: ProjectionFilterId;
  rowLimit: number;
  strategyOptions: FacetOption[];
  techDomainOptions: FacetOption[];
  strategyScopeContentCount: number;
  techDomainScopeContentCount: number;
  projectionScopeContentCount: number;
  curatedProjectionContentCount: number;
  provisionalProjectionContentCount: number;
  visiblePolicyCount: number;
  matchedContentCount: number;
  activePolicyName: string | null;
  onSearchChange: (value: string) => void;
  onResourceCategoryChange: (value: ResourceCategoryId) => void;
  onStrategyChange: (value: string) => void;
  onTechDomainChange: (value: string) => void;
  onProjectionStatusChange: (value: ProjectionFilterId) => void;
  onRowLimitChange: (value: number) => void;
  onResetFilters: () => void;
  isResetDisabled: boolean;
};

export function FilterBar({
  dataset,
  search,
  resourceCategoryId,
  strategyTermId,
  techDomainId,
  projectionStatus,
  rowLimit,
  strategyOptions,
  techDomainOptions,
  strategyScopeContentCount,
  techDomainScopeContentCount,
  projectionScopeContentCount,
  curatedProjectionContentCount,
  provisionalProjectionContentCount,
  visiblePolicyCount,
  matchedContentCount,
  activePolicyName,
  onSearchChange,
  onResourceCategoryChange,
  onStrategyChange,
  onTechDomainChange,
  onProjectionStatusChange,
  onRowLimitChange,
  onResetFilters,
  isResetDisabled,
}: FilterBarProps) {
  const categoryLabel =
    resourceCategoryId === "all"
      ? "전체 부문"
      : dataset.resource_categories.find((entry) => entry.resource_category_id === resourceCategoryId)?.display_label ??
        resourceCategoryId;
  const strategyLabel =
    strategyTermId === "all" ? "전체 전략" : dataset.strategyFilterMap.get(strategyTermId)?.label ?? strategyTermId;
  const techLabel =
    techDomainId === "all" ? "전체 기술분야" : dataset.techDomainFilterMap.get(techDomainId)?.label ?? techDomainId;
  const projectionLabel =
    projectionStatus === "all" ? "전체 projection" : projectionStatus === "curated" ? "curated만" : "provisional만";

  return (
    <Panel className={styles.filterBar}>
      <div className={styles.filterCopy}>
        <p className={styles.eyebrow}>Filter Stack</p>
        <h2 className={styles.sectionTitle}>탐색 조건</h2>
        <p className={styles.sectionBody}>
          현재 결과는 {formatNumber(visiblePolicyCount)}개 정책, {formatNumber(matchedContentCount)}개 대표 내용이다.
          검색, 전략 축, 기술분야는 전역 필터이고, 부문은 <strong>{activePolicyName ?? "선택 정책"}</strong> 내부 세그먼트로
          동작한다.
        </p>
        <div className={styles.filterActions}>
          <button
            type="button"
            className={styles.filterResetButton}
            onClick={onResetFilters}
            disabled={isResetDisabled}
          >
            필터 초기화
          </button>
        </div>
      </div>

      <div className={styles.filterControls}>
        <label className={styles.field}>
          <span>정책·그룹·내용 검색</span>
          <input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="정책명, 그룹명, 내용문구 검색" />
        </label>
        <label className={styles.field}>
          <span>선택 정책 부문</span>
          <select
            value={resourceCategoryId}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              onResourceCategoryChange(event.target.value as ResourceCategoryId)
            }
          >
            <option value="all">전체 부문</option>
            {dataset.resource_categories.map((entry) => (
              <option key={entry.resource_category_id} value={entry.resource_category_id}>
                {entry.display_label}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.field}>
          <span>전략 축</span>
          <select value={strategyTermId} onChange={(event) => onStrategyChange(event.target.value)}>
            <option value="all">전체 전략 ({formatNumber(strategyScopeContentCount)})</option>
            {strategyOptions.map((entry) => (
              <option key={entry.termId} value={entry.termId} disabled={entry.contentCount === 0 && !entry.isSelected}>
                {entry.label} ({formatNumber(entry.contentCount)})
              </option>
            ))}
          </select>
        </label>
        <label className={styles.field}>
          <span>표시 행 수</span>
          <select value={rowLimit} onChange={(event) => onRowLimitChange(Number(event.target.value))}>
            <option value={8}>8개</option>
            <option value={12}>12개</option>
            <option value={20}>20개</option>
            <option value={9999}>전체</option>
          </select>
        </label>
      </div>

      <div className={styles.techFilterRow}>
        <div className={styles.techFilterHead}>
          <div>
            <p className={styles.eyebrow}>Tech Axis</p>
            <p className={styles.sectionBody}>기술분야 칩은 현재 검색어와 전략 축 기준으로 다시 계산된다.</p>
          </div>
        </div>
        <div className={styles.techFilterStrip}>
          <button
            type="button"
            className={techDomainId === "all" ? styles.techFilterActive : styles.techFilter}
            onClick={() => onTechDomainChange("all")}
          >
            전체 {formatNumber(techDomainScopeContentCount)}
          </button>
          {techDomainOptions.map((entry) => (
            <button
              key={entry.termId}
              type="button"
              className={techDomainId === entry.termId ? styles.techFilterActive : styles.techFilter}
              onClick={() => onTechDomainChange(entry.termId)}
              disabled={entry.contentCount === 0 && !entry.isSelected}
            >
              {entry.label} {formatNumber(entry.contentCount)}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.projectionFilterRow}>
        <div className={styles.techFilterHead}>
          <div>
            <p className={styles.eyebrow}>Projection Status</p>
            <p className={styles.sectionBody}>curated 확정본과 provisional fallback을 분리해 볼 수 있다.</p>
          </div>
        </div>
        <div className={styles.projectionFilterStrip}>
          <button
            type="button"
            className={projectionStatus === "all" ? styles.projectionFilterActive : styles.projectionFilter}
            onClick={() => onProjectionStatusChange("all")}
          >
            전체 {formatNumber(projectionScopeContentCount)}
          </button>
          <button
            type="button"
            className={projectionStatus === "curated" ? styles.projectionFilterActive : styles.projectionFilter}
            onClick={() => onProjectionStatusChange("curated")}
            disabled={curatedProjectionContentCount === 0 && projectionStatus !== "curated"}
          >
            curated {formatNumber(curatedProjectionContentCount)}
          </button>
          <button
            type="button"
            className={projectionStatus === "provisional" ? styles.projectionFilterActive : styles.projectionFilter}
            onClick={() => onProjectionStatusChange("provisional")}
            disabled={provisionalProjectionContentCount === 0 && projectionStatus !== "provisional"}
          >
            provisional {formatNumber(provisionalProjectionContentCount)}
          </button>
        </div>
      </div>

      <div className={styles.summaryChips}>
        {search ? <Chip tone="primary">검색어 "{search}"</Chip> : <Chip>검색어 없음</Chip>}
        <Chip>{activePolicyName ?? "정책 미선택"}</Chip>
        <Chip>{categoryLabel}</Chip>
        <Chip>{strategyLabel}</Chip>
        <Chip>{techLabel}</Chip>
        <Chip>{projectionLabel}</Chip>
        <Chip>{rowLimit >= 9999 ? "전체 행 표시" : `${rowLimit}개 행 표시`}</Chip>
      </div>
    </Panel>
  );
}
