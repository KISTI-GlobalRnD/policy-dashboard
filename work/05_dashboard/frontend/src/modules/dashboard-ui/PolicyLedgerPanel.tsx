import { formatNumber } from "../../shared/lib/format";
import { Panel } from "../../shared/ui/Panel";
import type { PolicyTechMatrixRow, ReviewStateSummary } from "../dashboard-model/mappingWorkbenchSelectors";
import { getReviewStateSummaryShortLabel } from "./reviewStatus";
import styles from "./MappingWorkbenchPage.module.css";

type PolicyLedgerPanelProps = {
  rows: PolicyTechMatrixRow[];
  selectedPolicyId: string | null;
  onSelectPolicy: (policyId: string | null) => void;
};

function getReviewSummary(row: PolicyTechMatrixRow): ReviewStateSummary {
  if (row.mappedContentCount === 0) {
    return "empty";
  }

  if (row.reviewedContentCount === row.mappedContentCount) {
    return "reviewed";
  }

  if (row.reviewedContentCount === 0) {
    return "needs_review";
  }

  return "mixed";
}

export function PolicyLedgerPanel({ rows, selectedPolicyId, onSelectPolicy }: PolicyLedgerPanelProps) {
  return (
    <Panel className={styles.policyLedgerPanel}>
      <div className={styles.panelHead}>
        <div>
          <p className={styles.eyebrow}>Policy Ledger</p>
          <h2 className={styles.sectionTitle}>정책 인덱스</h2>
        </div>
        <button
          type="button"
          className={styles.filterResetButton}
          onClick={() => onSelectPolicy(null)}
          disabled={selectedPolicyId === null}
        >
          전체 정책 보기
        </button>
      </div>

      <div className={styles.policyLedgerList}>
        {rows.map((row) => {
          const isActive = selectedPolicyId === row.policy.policy_id;
          const reviewState = getReviewSummary(row);

          return (
            <button
              key={row.policy.policy_id}
              type="button"
              className={isActive ? styles.policyLedgerCardActive : styles.policyLedgerCard}
              onClick={() => onSelectPolicy(row.policy.policy_id)}
            >
              <div className={styles.policyLedgerCardHead}>
                <span className={styles.policyLedgerIndex}>{String(row.policy.policy_order).padStart(2, "0")}</span>
                <span
                  className={
                    reviewState === "reviewed"
                      ? styles.matrixReviewPillReviewed
                      : reviewState === "needs_review"
                        ? styles.matrixReviewPillNeedsReview
                        : reviewState === "mixed"
                          ? styles.matrixReviewPillMixed
                          : styles.matrixReviewPillNeutral
                  }
                >
                  {getReviewStateSummaryShortLabel(reviewState)}
                </span>
              </div>

              <strong className={styles.policyLedgerTitle}>{row.policy.policy_name}</strong>
              <p className={styles.policyLedgerMeta}>
                {formatNumber(row.mappedDomainCount)}개 대분류 · {formatNumber(row.mappedContentCount)}C ·{" "}
                {formatNumber(row.unmappedContentCount)} gap
              </p>
              <p className={styles.policyLedgerSubmeta}>
                리뷰 완료 {formatNumber(row.reviewedContentCount)} / 필요 {formatNumber(row.needsReviewContentCount)}
              </p>
            </button>
          );
        })}
      </div>
    </Panel>
  );
}
