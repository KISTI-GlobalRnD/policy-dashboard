import { Chip } from "../../shared/ui/Chip";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import { getAssetPreviewKind, resolveAssetHref, sanitizeAssetPath } from "../../shared/lib/assets";
import type { ActiveTrace } from "../dashboard-model/mappingWorkbenchSelectors";
import { getReviewStatusLabel } from "./reviewStatus";
import styles from "./MappingWorkbenchPage.module.css";

type EvidenceTraceDrawerProps = {
  activeTrace: ActiveTrace | null;
  onClose: () => void;
};

export function EvidenceTraceDrawer({ activeTrace, onClose }: EvidenceTraceDrawerProps) {
  if (!activeTrace) {
    return (
      <Panel className={styles.drawerPanel}>
        <EmptyState
          eyebrow="Evidence Drawer"
          title="대표 내용을 선택하면 근거가 열립니다"
          body="셀 상세 패널의 content를 고르면 evidence, source asset, 원문 preview를 이 패널에서 바로 확인할 수 있습니다."
        />
      </Panel>
    );
  }

  const { row, context } = activeTrace;
  const primarySourceAsset = context.preferred_source_asset ?? row.preferred_source_asset ?? null;
  const sourceHref = resolveAssetHref(primarySourceAsset?.asset_path_or_url);
  const previewKind = getAssetPreviewKind(primarySourceAsset?.asset_path_or_url);
  const sanitizedAssetPath = sanitizeAssetPath(primarySourceAsset?.asset_path_or_url);

  return (
    <Panel className={styles.drawerPanel}>
      <div className={styles.drawerHead}>
        <div>
          <p className={styles.eyebrow}>Evidence Trace</p>
          <h2 className={styles.sectionTitle}>{row.content_label}</h2>
        </div>
        <button type="button" className={styles.drawerCloseButton} onClick={onClose}>
          닫기
        </button>
      </div>

      <div className={styles.inlineChips}>
        <Chip tone="primary">{row.policy_item_content_id}</Chip>
        <Chip>{row.group_label}</Chip>
        <Chip>{row.resource_category_label}</Chip>
        {row.primary_strategy ? <Chip>{row.primary_strategy.label}</Chip> : null}
        <span className={row.mapping_review_status === "reviewed" ? styles.reviewBadgeReviewed : styles.reviewBadgeNeedsReview}>
          {`매핑 ${getReviewStatusLabel(row.mapping_review_status)}`}
        </span>
        <span className={row.content_review_status === "reviewed" ? styles.reviewBadgeReviewed : styles.reviewBadgeNeedsReview}>
          {`내용 ${getReviewStatusLabel(row.content_review_status)}`}
        </span>
      </div>

      <section className={styles.drawerSection}>
        <p className={styles.eyebrow}>Content Statement</p>
        <div className={styles.drawerTextBlock}>
          <p>{row.content_statement}</p>
          <p className={styles.sectionBody}>{row.content_summary || "대표 내용 요약 없음"}</p>
        </div>
      </section>

      <section className={styles.drawerSection}>
        <div className={styles.drawerSectionHead}>
          <p className={styles.eyebrow}>Source Preview</p>
          {sourceHref ? (
            <a className={styles.drawerLink} href={sourceHref} target="_blank" rel="noreferrer">
              원문 열기
            </a>
          ) : null}
        </div>

        <div className={styles.previewShell}>
          {previewKind === "image" && sourceHref ? (
            <img className={styles.previewImage} src={sourceHref} alt={`${row.content_label} source preview`} loading="lazy" />
          ) : null}
          {previewKind === "pdf" && sourceHref ? (
            <iframe className={styles.previewDocument} src={sourceHref} title={`${row.content_label} pdf preview`} />
          ) : null}
          {previewKind !== "image" && previewKind !== "pdf" ? (
            <div className={styles.previewFallback}>
              <p className={styles.previewFallbackTitle}>{primarySourceAsset?.source_asset_id ?? "원문 자산"}</p>
              <p className={styles.sectionBody}>{sanitizedAssetPath ?? "패널 내 직접 미리보기 불가"}</p>
            </div>
          ) : null}
        </div>
      </section>

      <section className={styles.drawerSection}>
        <p className={styles.eyebrow}>Evidence Stack</p>
        <div className={styles.evidenceList}>
          {context.content.evidence.map((evidence) => (
            <article key={evidence.derived_representation_id} className={styles.evidenceCard}>
              <div className={styles.evidenceHead}>
                <strong>{evidence.source_policy_item_label}</strong>
                <span>{evidence.location_value || evidence.source_object_type || "위치 미상"}</span>
              </div>
              <p>{evidence.evidence_text}</p>
              <div className={styles.evidenceMeta}>
                <span>{evidence.representation_type}</span>
                <span>{formatNumber(evidence.source_assets.length)} asset</span>
                <span>{evidence.derived_representation_id}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </Panel>
  );
}
