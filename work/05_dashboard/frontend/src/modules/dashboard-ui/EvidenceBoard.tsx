import { EmptyState } from "../../shared/ui/EmptyState";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import { resolveAssetHref, sanitizeAssetPath } from "../../shared/lib/assets";
import type { ResourceCategoryId } from "../dashboard-data/dashboard.types";
import type { PolicyView } from "../dashboard-model/dashboardSelectors";
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

type EvidenceBoardProps = {
  activePolicyView: PolicyView | null;
  activeRows: PolicyView["matchedRows"];
  resourceCategoryId: ResourceCategoryId;
  activeContentId: string | null;
  onSelectCategory: (value: ResourceCategoryId) => void;
  onSelectContent: (contentId: string) => void;
};

export function EvidenceBoard({
  activePolicyView,
  activeRows,
  resourceCategoryId,
  activeContentId,
  onSelectCategory,
  onSelectContent,
}: EvidenceBoardProps) {
  if (!activePolicyView) {
    return (
      <Panel className={styles.boardPanel}>
        <EmptyState
          eyebrow="Content Table"
          title="정책을 선택하세요"
          body="왼쪽 정책 인덱스에서 하나를 고르면 대표 내용 테이블과 오른쪽 trace가 함께 갱신됩니다."
        />
      </Panel>
    );
  }

  const activeCategoryMatchedCount =
    resourceCategoryId === "all"
      ? activePolicyView.matchedContentCount
      : activePolicyView.bucketSignals.find((bucket) => bucket.resource_category_id === resourceCategoryId)?.matched_content_count ?? 0;

  return (
    <Panel className={styles.boardPanel}>
      <div className={styles.panelHead}>
        <div>
          <p className={styles.eyebrow}>Content Table</p>
          <h2 className={styles.panelTitle}>{activePolicyView.policy.policy_name}</h2>
        </div>
        <p className={styles.panelSummary}>
          {formatNumber(activeRows.length)}개 표시 / {formatNumber(activeCategoryMatchedCount)}개 일치 · 총{" "}
          {formatNumber(activePolicyView.policy.total_content_count)}개 대표 내용
        </p>
      </div>

      <div className={styles.boardToolbar}>
        <p className={styles.boardToolbarCopy}>
          대표 내용 단위로 전략, 기술, 근거 수, 원문 링크를 같은 행에서 읽고, 특정 행을 선택하면 오른쪽에서 provenance를
          끝까지 추적한다.
        </p>
        <div className={styles.tableChips}>
          <span className={styles.tableChip}>{activePolicyView.primaryStrategyLabel}</span>
          <span className={styles.tableChip}>
            {formatNumber(activePolicyView.policy.total_group_count)} groups / {formatNumber(activePolicyView.policy.total_member_count)} raw
            members
          </span>
          <span className={styles.tableChip}>
            {formatNumber(activePolicyView.curatedContentCount)} curated / {formatNumber(activePolicyView.provisionalContentCount)} provisional
          </span>
        </div>
      </div>

      <div className={styles.boardMetaStrip}>
        <div className={styles.boardMetaCell}>
          <span className={styles.boardMetaLabel}>정책 ID</span>
          <strong className={styles.boardMetaValue}>{activePolicyView.policy.policy_id}</strong>
        </div>
        <div className={styles.boardMetaCell}>
          <span className={styles.boardMetaLabel}>대표 그룹</span>
          <strong className={styles.boardMetaValue}>
            {formatNumber(activePolicyView.matchedGroupCount)} / {formatNumber(activePolicyView.policy.total_group_count)}
          </strong>
        </div>
        <div className={styles.boardMetaCell}>
          <span className={styles.boardMetaLabel}>대표 내용</span>
          <strong className={styles.boardMetaValue}>
            {formatNumber(activeRows.length)} / {formatNumber(activeCategoryMatchedCount)}
          </strong>
        </div>
        <div className={styles.boardMetaCell}>
          <span className={styles.boardMetaLabel}>raw members</span>
          <strong className={styles.boardMetaValue}>{formatNumber(activePolicyView.policy.total_member_count)}</strong>
        </div>
        <div className={styles.boardMetaCell}>
          <span className={styles.boardMetaLabel}>evidences</span>
          <strong className={styles.boardMetaValue}>{formatNumber(activePolicyView.policy.total_evidence_count)}</strong>
        </div>
      </div>

      <div className={styles.categorySegment}>
        <button
          type="button"
          className={resourceCategoryId === "all" ? styles.categorySegmentActive : styles.categorySegmentButton}
          onClick={() => onSelectCategory("all")}
        >
          전체
          <strong>{formatNumber(activePolicyView.matchedContentCount)}C</strong>
        </button>
        {activePolicyView.bucketSignals.map((bucket) => (
          <button
            key={bucket.policy_bucket_id}
            type="button"
            className={
              resourceCategoryId === bucket.resource_category_id ? styles.categorySegmentActive : styles.categorySegmentButton
            }
            onClick={() => onSelectCategory(bucket.resource_category_id)}
          >
            {bucket.label}
            <strong>
              {formatNumber(bucket.matched_group_count)}G / {formatNumber(bucket.matched_content_count)}C
            </strong>
          </button>
        ))}
      </div>

      {activeRows.length === 0 ? (
        <EmptyState
          eyebrow="No Rows"
          title="현재 정책에서 일치하는 내용이 없습니다."
          body="검색어나 전략·기술 필터를 완화하면 다시 대표 내용 행이 나타납니다."
        />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.itemTable}>
            <colgroup>
              <col className={styles.colCategory} />
              <col className={styles.colGroup} />
              <col className={styles.colContent} />
              <col className={styles.colTaxonomy} />
              <col className={styles.colEvidence} />
              <col className={styles.colSource} />
            </colgroup>
            <thead>
              <tr>
                <th>부문</th>
                <th>대표 그룹</th>
                <th>대표 내용</th>
                <th>전략·기술</th>
                <th>근거</th>
                <th>원문 링크</th>
              </tr>
            </thead>
            <tbody>
              {activeRows.map((row) => {
                const isActive = row.policy_item_content_id === activeContentId;
                const sourceHref = resolveAssetHref(row.preferred_source_asset?.asset_path_or_url);
                const sourcePath = sanitizeAssetPath(row.preferred_source_asset?.asset_path_or_url) ?? "원문 경로 미상";
                const locations = row.location_labels.length > 0 ? row.location_labels.join(" / ") : "위치 정보 없음";

                return (
                  <tr key={row.policy_item_content_id} className={isActive ? styles.tableRowActive : styles.tableRow}>
                    <td>
                      <span
                        className={
                          row.resource_category_id === "technology"
                            ? styles.tableCategoryTech
                            : row.resource_category_id === "infrastructure_institutional"
                              ? styles.tableCategoryInfra
                              : styles.tableCategoryTalent
                        }
                      >
                        {row.resource_category_label}
                      </span>
                    </td>
                    <td>
                      <div className={styles.tableTitle}>
                        <span className={styles.tableId}>{row.policy_item_group_id}</span>
                        <div className={styles.tableBadgeRow}>
                          <span
                            className={
                              row.projection_status === "curated"
                                ? styles.projectionBadgeCurated
                                : styles.projectionBadgeProvisional
                            }
                          >
                            {row.projection_status}
                          </span>
                        </div>
                        <strong>{row.group_label}</strong>
                        <div className={styles.tableSummary}>
                          {row.group_summary || `${formatNumber(row.member_count)} raw members`}
                        </div>
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        className={isActive ? styles.contentSelectButtonActive : styles.contentSelectButton}
                        onClick={() => onSelectContent(row.policy_item_content_id)}
                      >
                        <span className={styles.tableId}>{row.policy_item_content_id}</span>
                        <strong>{row.content_label}</strong>
                        <div className={styles.tableSummary}>{row.content_summary || row.content_statement}</div>
                      </button>
                    </td>
                    <td>
                      <div className={styles.tableTaxonomy}>
                        <span className={styles.tableStrategy}>{row.primary_strategy?.label ?? "전략 미지정"}</span>
                        <div className={styles.tableDomain}>
                          {row.tech_terms.length === 0 ? <span>기술 태그 없음</span> : row.tech_terms.map((term) => <span key={term.term_id}>{term.label}</span>)}
                        </div>
                        <div className={styles.tableSubdomain}>
                          {row.tech_subterms.length === 0 ? (
                            <span>세부기술 없음</span>
                          ) : (
                            row.tech_subterms.slice(0, 3).map((term) => <span key={term.term_id}>{term.label}</span>)
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className={styles.tableEvidence}>
                        <strong>{formatNumber(row.evidence_count)}</strong>
                        <span>{locations}</span>
                        <div className={styles.tableRepresentationList}>
                          {row.representation_types.map((representationType) => (
                            <span
                              key={representationType}
                              className={
                                representationType === "canonical_table"
                                  ? styles.tableRepresentationAccent
                                  : representationType === "figure_or_diagram"
                                  ? styles.tableRepresentationAccent
                                  : styles.tableRepresentation
                              }
                            >
                              {formatRepresentationLabel(representationType)}
                            </span>
                          ))}
                        </div>
                        {row.figure_evidence_count > 0 ? (
                          <span className={styles.tableFigureHint}>
                            figure evidence {formatNumber(row.figure_evidence_count)}건 포함
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td>
                      <div className={styles.tableSource}>
                        <span className={styles.sourceDoc}>
                          {row.preferred_source_asset?.source_asset_id ?? "source asset"} · {formatNumber(row.source_asset_count)} asset
                        </span>
                        {row.figure_evidence_count > 0 ? (
                          <span className={styles.sourceMode}>figure preview available</span>
                        ) : null}
                        {sourceHref ? (
                          <a
                            className={styles.sourceLink}
                            href={sourceHref}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(event) => event.stopPropagation()}
                          >
                            원문 열기
                          </a>
                        ) : (
                          <span className={styles.sourceLinkMuted}>원문 없음</span>
                        )}
                        <span className={styles.sourcePath}>{sourcePath}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {activeCategoryMatchedCount > activeRows.length ? (
        <p className={styles.emptyNote}>
          {formatNumber(activeCategoryMatchedCount - activeRows.length)}개 행이 더 있습니다. 표시 행 수를 늘리면 더 볼 수
          있습니다.
        </p>
      ) : null}
    </Panel>
  );
}
