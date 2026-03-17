import { useEffect, useState } from "react";
import { Chip } from "../../shared/ui/Chip";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type {
  CellGroupView,
  ContentRow,
  DomainSummaryView,
  PolicySummaryView,
  PolicyTechMatrixCell,
  ReviewStateSummary,
} from "../dashboard-model/mappingWorkbenchSelectors";
import { getReviewStateSummaryLabel, getReviewStatusLabel } from "./reviewStatus";
import styles from "./MappingWorkbenchPage.module.css";

type InspectorTab = "contents" | "groups" | "gaps";

type CellInspectorPanelProps = {
  selectedCell: PolicyTechMatrixCell | null;
  selectedPolicySummary: PolicySummaryView | null;
  selectedDomainSummary: DomainSummaryView | null;
  selectedCellGroups: CellGroupView[];
  selectedPolicyUnmappedContents: ContentRow[];
  activeContentId: string | null;
  onOpenCell: (policyId: string, domainId: string) => void;
  onSelectContent: (contentId: string | null) => void;
};

function ReviewBadge({ status }: { status: ReviewStateSummary | ContentRow["mapping_review_status"] }) {
  const className =
    status === "reviewed"
      ? styles.reviewBadgeReviewed
      : status === "needs_review"
        ? styles.reviewBadgeNeedsReview
        : status === "mixed"
          ? styles.reviewBadgeMixed
          : styles.reviewBadgeNeutral;

  const label =
    status === "mixed" || status === "empty" ? getReviewStateSummaryLabel(status) : getReviewStatusLabel(status);

  return <span className={className}>{label}</span>;
}

function ContentList({
  rows,
  activeContentId,
  onSelectContent,
}: {
  rows: ContentRow[];
  activeContentId: string | null;
  onSelectContent: (contentId: string | null) => void;
}) {
  if (rows.length === 0) {
    return (
      <div className={styles.inspectorEmptyBlock}>
        <p>현재 선택 조건에 해당하는 대표 내용이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className={styles.contentList}>
      {rows.map((row) => {
        const isActive = activeContentId === row.policy_item_content_id;

        return (
          <button
            key={row.policy_item_content_id}
            type="button"
            className={isActive ? styles.contentCardActive : styles.contentCard}
            onClick={() => onSelectContent(isActive ? null : row.policy_item_content_id)}
          >
            <div className={styles.contentCardHead}>
              <div>
                <p className={styles.cardEyebrow}>{row.policy_item_content_id}</p>
                <strong>{row.content_label}</strong>
              </div>
              <div className={styles.statusStack}>
                <span className={styles.countPill}>{formatNumber(row.evidence_count)}E</span>
                <ReviewBadge status={row.mapping_review_status} />
              </div>
            </div>
            <p className={styles.contentSummary}>{row.content_summary || row.content_statement}</p>
            <div className={styles.contentMetaRow}>
              <span>{row.group_label}</span>
              <span>{row.resource_category_label}</span>
            </div>
            <div className={styles.inlineChips}>
              {row.primary_strategy ? <Chip tone="primary">{row.primary_strategy.label}</Chip> : null}
              {row.tech_subterms.slice(0, 3).map((term) => (
                <Chip key={term.term_id}>{term.label}</Chip>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
}

function GroupList({ groups }: { groups: CellGroupView[] }) {
  if (groups.length === 0) {
    return (
      <div className={styles.inspectorEmptyBlock}>
        <p>표시할 대표 그룹이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className={styles.groupList}>
      {groups.map((group) => (
        <article key={group.groupId} className={styles.groupCard}>
          <div className={styles.groupCardHead}>
            <div>
              <p className={styles.cardEyebrow}>{group.groupId}</p>
              <strong>{group.label}</strong>
            </div>
            <div className={styles.statusStack}>
              <span className={styles.countPill}>
                {formatNumber(group.contentCount)}C / {formatNumber(group.evidenceCount)}E
              </span>
              <ReviewBadge status={group.reviewStatus} />
            </div>
          </div>
          <p className={styles.contentSummary}>{group.summary || "대표 그룹 요약 없음"}</p>
          <div className={styles.inlineChips}>
            <ReviewBadge status={group.groupReviewStatus} />
            <Chip>{`리뷰 완료 ${formatNumber(group.reviewedContentCount)}`}</Chip>
            <Chip>{`리뷰 필요 ${formatNumber(group.needsReviewContentCount)}`}</Chip>
            {group.resourceMix.map((entry) => (
              <Chip key={entry.resourceCategoryId}>{`${entry.label} ${formatNumber(entry.count)}`}</Chip>
            ))}
            {group.strategyLabels.map((label) => (
              <Chip key={label} tone="primary">
                {label}
              </Chip>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

export function CellInspectorPanel({
  selectedCell,
  selectedPolicySummary,
  selectedDomainSummary,
  selectedCellGroups,
  selectedPolicyUnmappedContents,
  activeContentId,
  onOpenCell,
  onSelectContent,
}: CellInspectorPanelProps) {
  const mode = selectedCell ? "cell" : selectedPolicySummary ? "policy" : selectedDomainSummary ? "domain" : "empty";
  const [tab, setTab] = useState<InspectorTab>("contents");

  useEffect(() => {
    setTab("contents");
  }, [mode, selectedCell?.key]);

  if (mode === "empty") {
    return (
      <aside className={styles.inspectorPanel}>
        <EmptyState
          eyebrow="Inspector"
          title="매트릭스에서 셀을 선택하세요"
          body="정책 행이나 기술대분류 헤더로 요약을 본 뒤, 셀을 누르면 대표 내용과 대표 그룹이 오른쪽 패널에 나타납니다."
        />
      </aside>
    );
  }

  if (mode === "policy" && selectedPolicySummary) {
    return (
      <aside className={styles.inspectorPanel}>
        <div className={styles.panelHead}>
          <div>
            <p className={styles.eyebrow}>Policy Summary</p>
            <h2 className={styles.sectionTitle}>{selectedPolicySummary.policy.policy_name}</h2>
          </div>
        </div>

        <div className={styles.summaryGrid}>
          <article className={styles.summaryCard}>
            <span>매핑 대분류</span>
            <strong>{formatNumber(selectedPolicySummary.mappedDomainCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>매핑 내용</span>
            <strong>{formatNumber(selectedPolicySummary.mappedContentCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>미매핑 내용</span>
            <strong>{formatNumber(selectedPolicySummary.unmappedContentCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>근거 수</span>
            <strong>{formatNumber(selectedPolicySummary.totalEvidenceCount)}</strong>
          </article>
        </div>

        <div className={styles.inlineChips}>
          <Chip>{`리뷰 완료 ${formatNumber(selectedPolicySummary.reviewedContentCount)}`}</Chip>
          <Chip>{`리뷰 필요 ${formatNumber(selectedPolicySummary.needsReviewContentCount)}`}</Chip>
        </div>

        <Panel className={styles.inspectorSection}>
          <p className={styles.eyebrow}>Top Domains</p>
          <div className={styles.domainList}>
            {selectedPolicySummary.topDomains.length === 0 ? (
              <p className={styles.sectionBody}>현재 정책에서 매핑된 기술 대분류가 없습니다.</p>
            ) : (
              selectedPolicySummary.topDomains.map((domain) => (
                <button
                  key={domain.termId}
                  type="button"
                  className={styles.domainRowButton}
                  onClick={() => onOpenCell(selectedPolicySummary.policy.policy_id, domain.termId)}
                >
                  <span>{domain.label}</span>
                  <div className={styles.domainRowStats}>
                    <strong>
                      {formatNumber(domain.groupCount)}G / {formatNumber(domain.contentCount)}C
                    </strong>
                    <span className={styles.domainRowMeta}>리뷰 완료 {formatNumber(domain.reviewedContentCount)}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </Panel>

        <Panel className={styles.inspectorSection}>
          <p className={styles.eyebrow}>Unmapped</p>
          <ContentList rows={selectedPolicyUnmappedContents} activeContentId={activeContentId} onSelectContent={onSelectContent} />
        </Panel>
      </aside>
    );
  }

  if (mode === "domain" && selectedDomainSummary) {
    return (
      <aside className={styles.inspectorPanel}>
        <div className={styles.panelHead}>
          <div>
            <p className={styles.eyebrow}>Tech Domain Summary</p>
            <h2 className={styles.sectionTitle}>{selectedDomainSummary.domain.label}</h2>
          </div>
        </div>

        <div className={styles.summaryGrid}>
          <article className={styles.summaryCard}>
            <span>연결 정책</span>
            <strong>{formatNumber(selectedDomainSummary.policyCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>대표 그룹</span>
            <strong>{formatNumber(selectedDomainSummary.groupCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>대표 내용</span>
            <strong>{formatNumber(selectedDomainSummary.contentCount)}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>근거 수</span>
            <strong>{formatNumber(selectedDomainSummary.evidenceCount)}</strong>
          </article>
        </div>

        <div className={styles.inlineChips}>
          <Chip>{`리뷰 완료 ${formatNumber(selectedDomainSummary.reviewedContentCount)}`}</Chip>
          <Chip>{`리뷰 필요 ${formatNumber(selectedDomainSummary.needsReviewContentCount)}`}</Chip>
        </div>

        <Panel className={styles.inspectorSection}>
          <p className={styles.eyebrow}>Connected Policies</p>
          <div className={styles.domainList}>
            {selectedDomainSummary.policies.map((policy) => (
              <button
                key={policy.policyId}
                type="button"
                className={styles.domainRowButton}
                onClick={() => onOpenCell(policy.policyId, selectedDomainSummary.domain.termId)}
              >
                <span>{policy.policyName}</span>
                <div className={styles.domainRowStats}>
                  <strong>
                    {formatNumber(policy.groupCount)}G / {formatNumber(policy.contentCount)}C
                  </strong>
                  <span className={styles.domainRowMeta}>
                    완료 {formatNumber(policy.reviewedContentCount)} / 필요 {formatNumber(policy.needsReviewContentCount)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </Panel>

        <Panel className={styles.inspectorSection}>
          <p className={styles.eyebrow}>Strategy Tags</p>
          <div className={styles.inlineChips}>
            {selectedDomainSummary.strategyLabels.map((label) => (
              <Chip key={label} tone="primary">
                {label}
              </Chip>
            ))}
          </div>
        </Panel>
      </aside>
    );
  }

  if (!selectedCell) {
    return null;
  }

  return (
    <aside className={styles.inspectorPanel}>
      <div className={styles.panelHead}>
        <div>
          <p className={styles.eyebrow}>Cell Inspector</p>
          <h2 className={styles.sectionTitle}>
            {selectedCell.rows[0]?.policy_name ?? selectedCell.policyId} × {selectedCell.techDomainLabel}
          </h2>
        </div>
      </div>

      <div className={styles.summaryGrid}>
        <article className={styles.summaryCard}>
          <span>대표 그룹</span>
          <strong>{formatNumber(selectedCell.groupCount)}</strong>
        </article>
        <article className={styles.summaryCard}>
          <span>대표 내용</span>
          <strong>{formatNumber(selectedCell.contentCount)}</strong>
        </article>
        <article className={styles.summaryCard}>
          <span>근거 수</span>
          <strong>{formatNumber(selectedCell.evidenceCount)}</strong>
        </article>
        <article className={styles.summaryCard}>
          <span>리뷰 상태</span>
          <strong>{getReviewStateSummaryLabel(selectedCell.reviewStatus)}</strong>
        </article>
      </div>

      <div className={styles.inlineChips}>
        <Chip>{`리뷰 완료 ${formatNumber(selectedCell.reviewedContentCount)}`}</Chip>
        <Chip>{`리뷰 필요 ${formatNumber(selectedCell.needsReviewContentCount)}`}</Chip>
        {selectedCell.strategyLabels.map((label) => (
          <Chip key={label} tone="primary">
            {label}
          </Chip>
        ))}
        {selectedCell.resourceMix.map((entry) => (
          <Chip key={entry.resourceCategoryId}>{`${entry.label} ${formatNumber(entry.count)}`}</Chip>
        ))}
      </div>

      <div className={styles.tabRow}>
        <button
          type="button"
          className={tab === "contents" ? styles.tabButtonActive : styles.tabButton}
          onClick={() => setTab("contents")}
        >
          Contents
        </button>
        <button
          type="button"
          className={tab === "groups" ? styles.tabButtonActive : styles.tabButton}
          onClick={() => setTab("groups")}
        >
          Groups
        </button>
        <button
          type="button"
          className={tab === "gaps" ? styles.tabButtonActive : styles.tabButton}
          onClick={() => setTab("gaps")}
        >
          Gaps
        </button>
      </div>

      {tab === "contents" ? (
        <ContentList rows={selectedCell.rows} activeContentId={activeContentId} onSelectContent={onSelectContent} />
      ) : null}
      {tab === "groups" ? <GroupList groups={selectedCellGroups} /> : null}
      {tab === "gaps" ? (
        <ContentList rows={selectedPolicyUnmappedContents} activeContentId={activeContentId} onSelectContent={onSelectContent} />
      ) : null}
    </aside>
  );
}
