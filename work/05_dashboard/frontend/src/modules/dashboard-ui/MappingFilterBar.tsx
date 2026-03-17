import type { ChangeEvent } from "react";
import { Chip } from "../../shared/ui/Chip";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type { ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { FacetOption } from "../dashboard-model/mappingWorkbenchSelectors";
import type { MappingStatusFilter, ReviewStatusFilter } from "../dashboard-model/mappingWorkbenchStore";
import styles from "./MappingWorkbenchPage.module.css";

type MappingFilterBarProps = {
  search: string;
  policyFilterId: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainFilterId: string;
  mappingStatus: MappingStatusFilter;
  reviewStatus: ReviewStatusFilter;
  filteredContentCount: number;
  visiblePolicyCount: number;
  availablePolicies: FacetOption[];
  availableStrategies: FacetOption[];
  availableTechDomains: FacetOption[];
  availableReviewStatuses: FacetOption[];
  onSearchChange: (value: string) => void;
  onPolicyFilterChange: (value: string) => void;
  onResourceCategoryChange: (value: ResourceCategoryId) => void;
  onStrategyChange: (value: string) => void;
  onTechDomainFilterChange: (value: string) => void;
  onMappingStatusChange: (value: MappingStatusFilter) => void;
  onReviewStatusChange: (value: ReviewStatusFilter) => void;
  onReset: () => void;
  isResetDisabled: boolean;
};

const RESOURCE_OPTIONS: Array<{ value: ResourceCategoryId; label: string }> = [
  { value: "all", label: "전체 자원유형" },
  { value: "technology", label: "기술" },
  { value: "infrastructure_institutional", label: "인프라·제도" },
  { value: "talent", label: "인재" },
];

const MAPPING_STATUS_OPTIONS: Array<{ value: MappingStatusFilter; label: string }> = [
  { value: "all", label: "전체 상태" },
  { value: "mapped", label: "매핑됨" },
  { value: "unmapped", label: "미매핑" },
];

const REVIEW_STATUS_OPTIONS: Array<{ value: ReviewStatusFilter; label: string }> = [
  { value: "all", label: "전체 리뷰상태" },
  { value: "reviewed", label: "리뷰 완료" },
  { value: "needs_review", label: "리뷰 필요" },
];

export function MappingFilterBar({
  search,
  policyFilterId,
  resourceCategoryId,
  strategyTermId,
  techDomainFilterId,
  mappingStatus,
  reviewStatus,
  filteredContentCount,
  visiblePolicyCount,
  availablePolicies,
  availableStrategies,
  availableTechDomains,
  availableReviewStatuses,
  onSearchChange,
  onPolicyFilterChange,
  onResourceCategoryChange,
  onStrategyChange,
  onTechDomainFilterChange,
  onMappingStatusChange,
  onReviewStatusChange,
  onReset,
  isResetDisabled,
}: MappingFilterBarProps) {
  const selectedPolicyLabel =
    policyFilterId === "all" ? "전체 정책" : availablePolicies.find((entry) => entry.value === policyFilterId)?.label ?? policyFilterId;
  const selectedStrategyLabel =
    strategyTermId === "all"
      ? "전체 전략"
      : availableStrategies.find((entry) => entry.value === strategyTermId)?.label ?? strategyTermId;
  const selectedTechLabel =
    techDomainFilterId === "all"
      ? "전체 기술대분류"
      : availableTechDomains.find((entry) => entry.value === techDomainFilterId)?.label ?? techDomainFilterId;
  const selectedResourceLabel =
    RESOURCE_OPTIONS.find((entry) => entry.value === resourceCategoryId)?.label ?? resourceCategoryId;
  const selectedMappingStatus =
    MAPPING_STATUS_OPTIONS.find((entry) => entry.value === mappingStatus)?.label ?? mappingStatus;
  const selectedReviewStatus =
    REVIEW_STATUS_OPTIONS.find((entry) => entry.value === reviewStatus)?.label ?? reviewStatus;

  return (
    <Panel className={styles.filterPanel}>
      <div className={styles.filterIntro}>
        <p className={styles.eyebrow}>Filter Stack</p>
        <h2 className={styles.sectionTitle}>매핑 범위를 먼저 좁힌다</h2>
        <p className={styles.sectionBody}>
          현재 결과는 {formatNumber(visiblePolicyCount)}개 정책, {formatNumber(filteredContentCount)}개 대표 내용을 기준으로
          다시 집계된다. 정책과 기술대분류를 직접 고정하지 않아도 셀 클릭으로 drill-down 할 수 있다.
        </p>
        <button
          type="button"
          className={styles.filterResetButton}
          onClick={onReset}
          disabled={isResetDisabled}
        >
          필터 초기화
        </button>
      </div>

      <div className={styles.filterGrid}>
        <label className={styles.field}>
          <span>검색</span>
          <input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="정책명, 그룹명, 내용 검색" />
        </label>

        <label className={styles.field}>
          <span>정책</span>
          <select value={policyFilterId} onChange={(event: ChangeEvent<HTMLSelectElement>) => onPolicyFilterChange(event.target.value)}>
            <option value="all">전체 정책 ({formatNumber(visiblePolicyCount)})</option>
            {availablePolicies.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label} ({formatNumber(entry.count)})
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>자원유형</span>
          <select
            value={resourceCategoryId}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              onResourceCategoryChange(event.target.value as ResourceCategoryId)
            }
          >
            {RESOURCE_OPTIONS.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>전략</span>
          <select value={strategyTermId} onChange={(event) => onStrategyChange(event.target.value)}>
            <option value="all">전체 전략</option>
            {availableStrategies.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label} ({formatNumber(entry.count)})
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>기술대분류</span>
          <select value={techDomainFilterId} onChange={(event) => onTechDomainFilterChange(event.target.value)}>
            <option value="all">전체 기술대분류</option>
            {availableTechDomains.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label} ({formatNumber(entry.count)})
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>매핑상태</span>
          <select
            value={mappingStatus}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              onMappingStatusChange(event.target.value as MappingStatusFilter)
            }
          >
            {MAPPING_STATUS_OPTIONS.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>리뷰상태</span>
          <select
            value={reviewStatus}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              onReviewStatusChange(event.target.value as ReviewStatusFilter)
            }
          >
            <option value="all">전체 리뷰상태</option>
            {availableReviewStatuses.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label} ({formatNumber(entry.count)})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.filterChips}>
        {search ? <Chip tone="primary">검색어 "{search}"</Chip> : <Chip>검색어 없음</Chip>}
        <Chip>{selectedPolicyLabel}</Chip>
        <Chip>{selectedResourceLabel}</Chip>
        <Chip>{selectedStrategyLabel}</Chip>
        <Chip>{selectedTechLabel}</Chip>
        <Chip>{selectedMappingStatus}</Chip>
        <Chip>{selectedReviewStatus}</Chip>
      </div>
    </Panel>
  );
}
