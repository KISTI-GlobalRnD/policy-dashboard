import { formatNumber } from "../../shared/lib/format";
import type { PolicyView } from "../dashboard-model/dashboardSelectors";
import styles from "./DashboardWorkbenchPage.module.css";

type PolicyRailProps = {
  policyViews: PolicyView[];
  activePolicyId: string | null;
  hasFilter: boolean;
  onSelectPolicy: (policyId: string) => void;
};

export function PolicyRail({ policyViews, activePolicyId, hasFilter, onSelectPolicy }: PolicyRailProps) {
  return (
    <aside className={styles.policyRail}>
      <div className={styles.panelHead}>
        <div>
          <p className={styles.eyebrow}>Policy Ledger</p>
          <h2 className={styles.panelTitle}>정책 인덱스</h2>
        </div>
        <p className={styles.railSummary}>{formatNumber(policyViews.length)}개 정책</p>
      </div>

      <div className={styles.policyList}>
        {policyViews.map((view) => (
          <button
            key={view.policy.policy_id}
            type="button"
            className={view.policy.policy_id === activePolicyId ? styles.policyRowActive : styles.policyRow}
            onClick={() => onSelectPolicy(view.policy.policy_id)}
          >
            <span className={styles.policyIndex}>{String(view.policy.policy_order).padStart(2, "0")}</span>

            <div className={styles.policyRowBody}>
              <div className={styles.policyRowHeadline}>
                <strong className={styles.policyName}>{view.policy.policy_name}</strong>
                <span
                  className={
                    view.projectionStatus === "curated"
                      ? styles.badgeReady
                      : view.projectionStatus === "provisional"
                        ? styles.badgeWarn
                        : styles.badgeMixed
                  }
                >
                  {view.projectionStatus}
                </span>
              </div>

              <p className={styles.policySummary}>
                {hasFilter
                  ? `${formatNumber(view.matchedGroupCount)} groups · ${formatNumber(view.matchedContentCount)} contents 일치`
                  : `${formatNumber(view.policy.total_group_count)} groups · ${formatNumber(view.policy.total_content_count)} contents · ${formatNumber(view.policy.total_member_count)} raw members`}
              </p>
              <p className={styles.policyContext}>{view.primaryStrategyLabel}</p>

              <div className={styles.policySignals}>
                <span className={styles.policySignal}>
                  <span>projection</span>
                  <strong>
                    {formatNumber(view.curatedContentCount)}C curated / {formatNumber(view.provisionalContentCount)}C provisional
                  </strong>
                </span>
                {view.bucketSignals.map((bucket) => (
                  <span key={bucket.policy_bucket_id} className={styles.policySignal}>
                    <span>{bucket.label}</span>
                    <strong>
                      {formatNumber(hasFilter ? bucket.matched_group_count : bucket.group_count)}G /{" "}
                      {formatNumber(hasFilter ? bucket.matched_content_count : bucket.content_count)}C
                    </strong>
                  </span>
                ))}
                {view.policy.tech_labels.slice(0, 2).map((label) => (
                  <span key={label} className={styles.policySignal}>
                    <span>tech</span>
                    <strong>{label}</strong>
                  </span>
                ))}
              </div>
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}
