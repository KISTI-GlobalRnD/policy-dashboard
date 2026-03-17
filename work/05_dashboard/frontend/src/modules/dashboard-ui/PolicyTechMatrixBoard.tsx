import type { CSSProperties } from "react";
import { EmptyState } from "../../shared/ui/EmptyState";
import { cn } from "../../shared/lib/cn";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type { MatrixDomainSummary, PolicyTechMatrixRow } from "../dashboard-model/mappingWorkbenchSelectors";
import { getReviewStateSummaryShortLabel } from "./reviewStatus";
import styles from "./MappingWorkbenchPage.module.css";

type PolicyTechMatrixBoardProps = {
  rows: PolicyTechMatrixRow[];
  domains: MatrixDomainSummary[];
  selectedPolicyId: string | null;
  selectedDomainId: string | null;
  onSelectPolicy: (policyId: string | null) => void;
  onSelectDomain: (domainId: string | null) => void;
  onSelectCell: (policyId: string, domainId: string) => void;
};

export function PolicyTechMatrixBoard({
  rows,
  domains,
  selectedPolicyId,
  selectedDomainId,
  onSelectPolicy,
  onSelectDomain,
  onSelectCell,
}: PolicyTechMatrixBoardProps) {
  const hasContent = rows.some((row) => row.cells.some((cell) => cell.contentCount > 0));
  const getReviewPillClassName = (status: "reviewed" | "needs_review" | "mixed" | "empty") =>
    cn(
      styles.matrixReviewPill,
      status === "reviewed" && styles.matrixReviewPillReviewed,
      status === "needs_review" && styles.matrixReviewPillNeedsReview,
      status === "mixed" && styles.matrixReviewPillMixed,
      status === "empty" && styles.matrixReviewPillNeutral,
    );

  if (rows.length === 0 || domains.length === 0) {
    return (
      <Panel className={styles.matrixPanel}>
        <EmptyState
          eyebrow="Matrix"
          title="표시할 정책 또는 기술대분류가 없습니다."
          body="필터를 완화하면 정책 x 기술대분류 매트릭스를 다시 볼 수 있습니다."
        />
      </Panel>
    );
  }

  return (
    <Panel className={styles.matrixPanel}>
      <div className={styles.panelHead}>
        <div>
          <p className={styles.eyebrow}>Policy x Tech Domain</p>
          <h2 className={styles.sectionTitle}>정책 x 기술 대분류 매트릭스</h2>
        </div>
        <p className={styles.sectionBody}>
          셀 숫자는 대표 내용 수를 우선 표시한다. 정책 행이나 기술 대분류 헤더를 눌러 요약을 보고, 실제 drill-down은 셀에서
          시작한다.
        </p>
      </div>

      {!hasContent ? (
        <EmptyState
          eyebrow="No Mapping"
          title="현재 필터에서 매핑 결과가 없습니다."
          body="검색어나 필터를 완화하거나 다른 기술 대분류를 선택하면 매핑 셀을 다시 볼 수 있습니다."
        />
      ) : (
        <div className={styles.matrixScroller}>
          <table className={styles.matrixTable}>
            <thead>
              <tr>
                <th className={styles.matrixCorner}>정책 / 기술대분류</th>
                {domains.map((domain) => (
                  <th key={domain.termId} className={styles.matrixHeaderCell}>
                    <button
                      type="button"
                      className={
                        selectedPolicyId === null && selectedDomainId === domain.termId
                          ? styles.matrixHeaderButtonActive
                          : styles.matrixHeaderButton
                      }
                      onClick={() => onSelectDomain(selectedPolicyId === null && selectedDomainId === domain.termId ? null : domain.termId)}
                    >
                      <span className={styles.matrixHeaderCode}>{domain.shortLabel}</span>
                      <strong>{domain.label}</strong>
                      <span>
                        {formatNumber(domain.mappedPolicyCount)}P / {formatNumber(domain.contentCount)}C
                      </span>
                      <span className={styles.matrixReviewMeta}>리뷰 완료 {formatNumber(domain.reviewedContentCount)}</span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr key={row.policy.policy_id}>
                  <th className={styles.matrixPolicyCell}>
                    <button
                      type="button"
                      className={selectedPolicyId === row.policy.policy_id ? styles.matrixPolicyButtonActive : styles.matrixPolicyButton}
                      onClick={() => onSelectPolicy(selectedPolicyId === row.policy.policy_id ? null : row.policy.policy_id)}
                    >
                      <strong>{row.policy.policy_name}</strong>
                      <span>
                        {formatNumber(row.mappedDomainCount)}개 대분류 / {formatNumber(row.mappedContentCount)}C
                      </span>
                      <span className={styles.matrixReviewMeta}>
                        완료 {formatNumber(row.reviewedContentCount)} / 필요 {formatNumber(row.needsReviewContentCount)}
                      </span>
                    </button>
                  </th>
                  {row.cells.map((cell) => (
                    <td key={cell.key} className={styles.matrixDataCell}>
                      <button
                        type="button"
                        className={cell.isSelected ? styles.matrixCellButtonActive : styles.matrixCellButton}
                        onClick={() => onSelectCell(cell.policyId, cell.techDomainId)}
                        disabled={cell.contentCount === 0}
                        style={
                          {
                            "--cell-intensity": `${Math.max(cell.intensity, cell.contentCount > 0 ? 18 : 0)}%`,
                          } as CSSProperties
                        }
                      >
                        <strong>{formatNumber(cell.contentCount)}</strong>
                        <span>
                          {formatNumber(cell.groupCount)}G / {formatNumber(cell.evidenceCount)}E
                        </span>
                        <span className={getReviewPillClassName(cell.reviewStatus)}>
                          {`${getReviewStateSummaryShortLabel(cell.reviewStatus)} ${formatNumber(cell.reviewedContentCount)}/${formatNumber(cell.contentCount)}`}
                        </span>
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
