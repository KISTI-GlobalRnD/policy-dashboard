import { Chip } from "../../shared/ui/Chip";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type { DashboardDataset, ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { OverviewCategoryView } from "../dashboard-model/dashboardSelectors";
import styles from "./DashboardWorkbenchPage.module.css";

function formatRepresentationLabel(value: string) {
  switch (value) {
    case "normalized_paragraph":
      return "문단";
    case "canonical_table":
      return "표";
    case "figure_or_diagram":
      return "figure";
    default:
      return value;
  }
}

type OverviewBoardProps = {
  dataset: DashboardDataset;
  overviewByCategory: OverviewCategoryView[];
  visiblePolicyCount: number;
  matchedContentCount: number;
  search: string;
  resourceCategoryId: ResourceCategoryId;
  strategyTermId: string;
  techDomainId: string;
};

export function OverviewBoard({
  dataset,
  overviewByCategory,
  visiblePolicyCount,
  matchedContentCount,
  search,
  resourceCategoryId,
  strategyTermId,
  techDomainId,
}: OverviewBoardProps) {
  const activeStrategyLabel =
    strategyTermId === "all" ? "전체 전략" : dataset.strategyFilterMap.get(strategyTermId)?.label ?? strategyTermId;
  const activeDomainLabel =
    techDomainId === "all" ? "전체 기술분야" : dataset.techDomainFilterMap.get(techDomainId)?.label ?? techDomainId;
  const activeCategoryLabel =
    resourceCategoryId === "all"
      ? "전체 부문"
      : overviewByCategory.find((entry) => entry.resourceCategoryId === resourceCategoryId)?.label ?? resourceCategoryId;
  const topStrategies = dataset.strategy_filters.slice(0, 3);
  const topDomains = dataset.tech_domain_filters.slice(0, 4);
  const topRepresentations = dataset.representation_summaries.slice(0, 3);
  const evidencePerContent =
    dataset.stats.content_count === 0 ? 0 : dataset.stats.content_evidence_count / dataset.stats.content_count;

  return (
    <Panel className={styles.overviewPanel}>
      <div className={styles.overviewBand}>
        <section className={styles.overviewHeader}>
          <div className={styles.overviewHeaderMeta}>
            <p className={styles.eyebrow}>Operational Overview</p>
            <h2 className={styles.overviewBandTitle}>Technology Lens Snapshot</h2>
            <p className={styles.overviewBandBody}>
              기술 축 projection의 전역 모수와 현재 범위를 먼저 읽고, 바로 아래 정책 인덱스와 content table로
              내려가도록 압축했다.
            </p>
          </div>

          <div className={styles.overviewHeaderTags}>
            {search ? <Chip tone="primary">검색어 "{search}"</Chip> : <Chip>검색어 없음</Chip>}
            <Chip>{activeCategoryLabel}</Chip>
            <Chip>{activeStrategyLabel}</Chip>
            <Chip>{activeDomainLabel}</Chip>
            <Chip>{dataset.sample_scope.generated_from}</Chip>
          </div>
        </section>

        <section className={styles.overviewMetricGrid}>
          <div className={styles.overviewMetricCard}>
            <span>정책 범위</span>
            <strong>
              {formatNumber(visiblePolicyCount)} / {formatNumber(dataset.stats.policy_count)}
            </strong>
            <em>visible policies</em>
          </div>
          <div className={styles.overviewMetricCard}>
            <span>대표 내용</span>
            <strong>
              {formatNumber(matchedContentCount)} / {formatNumber(dataset.stats.content_count)}
            </strong>
            <em>matched contents</em>
          </div>
          <div className={styles.overviewMetricCard}>
            <span>대표 그룹</span>
            <strong>{formatNumber(dataset.stats.group_count)}</strong>
            <em>raw member {formatNumber(dataset.stats.group_member_count)}</em>
          </div>
          <div className={styles.overviewMetricCard}>
            <span>근거 밀도</span>
            <strong>{evidencePerContent.toFixed(1)}</strong>
            <em>{formatNumber(dataset.stats.content_evidence_count)} evidences</em>
          </div>
        </section>

        <section className={styles.overviewClusterGrid}>
          <div className={styles.overviewCategoryCompactList}>
            <div className={styles.overviewSectionHead}>
              <p className={styles.eyebrow}>Coverage Matrix</p>
              <p className={styles.sectionBody}>부문별 전체 모수 대비 현재 작업 범위를 압축해 본다.</p>
            </div>

            <div className={styles.overviewCategoryCompactGrid}>
              {overviewByCategory.map((row) => (
                <div
                  key={row.resourceCategoryId}
                  className={row.isFocused ? styles.overviewCategoryCompactActive : styles.overviewCategoryCompactCard}
                >
                  <div className={styles.overviewCategoryCompactHead}>
                    <div>
                      <p className={styles.overviewCategoryCode}>{row.shortLabel}</p>
                      <h3 className={styles.overviewCategoryTitle}>{row.label}</h3>
                    </div>
                    <strong className={styles.overviewCategoryCompactValue}>
                      {formatNumber(row.filteredContentCount)}C
                    </strong>
                  </div>
                  <div className={styles.overviewCompactBarTrack}>
                    <span
                      className={styles.overviewCompactBarFill}
                      style={{ width: `${Math.max(row.ratio, row.filteredContentCount > 0 ? 10 : 0)}%` }}
                    />
                  </div>
                  <p className={styles.overviewCategoryBody}>
                    {formatNumber(row.filteredGroupCount)}G / {formatNumber(row.filteredContentCount)}C /{" "}
                    {formatNumber(row.filteredPolicyCount)}P
                  </p>
                  <p className={styles.overviewCompactMeta}>
                    전체 {formatNumber(row.totalGroupCount)}G / {formatNumber(row.totalContentCount)}C
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.overviewLedgerCluster}>
            <section className={styles.overviewLedgerBlock}>
              <div className={styles.overviewSectionHead}>
                <p className={styles.eyebrow}>Strategy Axis</p>
                <p className={styles.sectionBody}>대표 내용 기준 상위 전략 축</p>
              </div>
              <div className={styles.overviewLedgerRows}>
                {topStrategies.map((entry, index) => (
                  <div key={entry.term_id} className={styles.overviewLedgerRow}>
                    <span className={styles.overviewDomainRank}>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{entry.label}</strong>
                    <span>{formatNumber(entry.content_count)}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className={styles.overviewLedgerBlock}>
              <div className={styles.overviewSectionHead}>
                <p className={styles.eyebrow}>Tech Axis</p>
                <p className={styles.sectionBody}>대표 내용 기준 상위 기술분야</p>
              </div>
              <div className={styles.overviewLedgerRows}>
                {topDomains.map((entry, index) => (
                  <div key={entry.term_id} className={styles.overviewLedgerRow}>
                    <span className={styles.overviewDomainRank}>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{entry.label}</strong>
                    <span>{formatNumber(entry.content_count)}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className={styles.overviewLedgerBlock}>
              <div className={styles.overviewSectionHead}>
                <p className={styles.eyebrow}>Representation Mix</p>
                <p className={styles.sectionBody}>근거 표현 계층별 구성</p>
              </div>
              <div className={styles.overviewLedgerRows}>
                {topRepresentations.map((entry) => (
                  <div key={entry.representation_type} className={styles.overviewLedgerRow}>
                    <span className={styles.overviewDomainRank}>{formatRepresentationLabel(entry.representation_type)}</span>
                    <strong>{entry.evidence_count} evidences</strong>
                    <span>{entry.content_count} contents</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </section>
      </div>
    </Panel>
  );
}
