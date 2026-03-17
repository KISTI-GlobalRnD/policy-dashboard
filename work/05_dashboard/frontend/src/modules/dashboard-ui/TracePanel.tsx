import { useEffect, useMemo, useState } from "react";
import { Chip } from "../../shared/ui/Chip";
import { EmptyState } from "../../shared/ui/EmptyState";
import { getAssetPreviewKind, resolveAssetHref, sanitizeAssetPath } from "../../shared/lib/assets";
import type { ActiveTrace } from "../dashboard-model/dashboardSelectors";
import styles from "./DashboardWorkbenchPage.module.css";

type TracePanelProps = {
  activeTrace: ActiveTrace | null;
};

type SourceAsset = ReturnType<typeof buildUniqueSourceAssets>[number];

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

function buildUniqueSourceAssets(activeTrace: ActiveTrace) {
  const deduped = new Map<string, (typeof activeTrace.context.content.evidence)[number]["source_assets"][number]>();

  for (const evidence of activeTrace.context.content.evidence) {
    for (const sourceAsset of evidence.source_assets) {
      deduped.set(sourceAsset.source_asset_id, sourceAsset);
    }
  }

  return [...deduped.values()];
}

type SourceAssetInsight = {
  sourceAsset: SourceAsset;
  evidenceCount: number;
  representationTypes: string[];
  locationValues: string[];
  evidenceLabels: string[];
  sourceObjectTypes: string[];
  structuredPayloadPaths: string[];
  previewKind: ReturnType<typeof getAssetPreviewKind>;
  isFigureAsset: boolean;
};

function buildSourceAssetInsights(activeTrace: ActiveTrace): SourceAssetInsight[] {
  const assetMap = new Map<
    string,
    {
      sourceAsset: ReturnType<typeof buildUniqueSourceAssets>[number];
      evidenceIds: Set<string>;
      representationTypes: Set<string>;
      locationValues: Set<string>;
      evidenceLabels: Set<string>;
      sourceObjectTypes: Set<string>;
      structuredPayloadPaths: Set<string>;
    }
  >();

  for (const evidence of activeTrace.context.content.evidence) {
    for (const sourceAsset of evidence.source_assets) {
      const existing = assetMap.get(sourceAsset.source_asset_id) ?? {
        sourceAsset,
        evidenceIds: new Set<string>(),
        representationTypes: new Set<string>(),
        locationValues: new Set<string>(),
        evidenceLabels: new Set<string>(),
        sourceObjectTypes: new Set<string>(),
        structuredPayloadPaths: new Set<string>(),
      };

      existing.sourceAsset = sourceAsset;
      existing.evidenceIds.add(evidence.derived_representation_id);
      existing.representationTypes.add(evidence.representation_type);
      if (evidence.evidence_label) {
        existing.evidenceLabels.add(evidence.evidence_label);
      }
      if (evidence.source_object_type) {
        existing.sourceObjectTypes.add(evidence.source_object_type);
      }
      if (evidence.structured_payload_path) {
        existing.structuredPayloadPaths.add(evidence.structured_payload_path);
      }

      if (evidence.location_value) {
        existing.locationValues.add(evidence.location_value);
      }

      assetMap.set(sourceAsset.source_asset_id, existing);
    }
  }

  return [...assetMap.values()]
    .map((entry) => ({
      sourceAsset: entry.sourceAsset,
      evidenceCount: entry.evidenceIds.size,
      representationTypes: [...entry.representationTypes],
      locationValues: [...entry.locationValues],
      evidenceLabels: [...entry.evidenceLabels],
      sourceObjectTypes: [...entry.sourceObjectTypes],
      structuredPayloadPaths: [...entry.structuredPayloadPaths],
      previewKind: getAssetPreviewKind(entry.sourceAsset.asset_path_or_url),
      isFigureAsset: entry.sourceAsset.asset_type === "figure_image",
    }))
    .sort((left, right) => {
      const leftPriority = left.isFigureAsset ? 3 : left.previewKind === "image" ? 2 : left.previewKind === "pdf" ? 1 : 0;
      const rightPriority = right.isFigureAsset ? 3 : right.previewKind === "image" ? 2 : right.previewKind === "pdf" ? 1 : 0;

      if (leftPriority !== rightPriority) {
        return rightPriority - leftPriority;
      }

      return right.evidenceCount - left.evidenceCount;
    });
}

function TracePanelContent({ activeTrace }: { activeTrace: ActiveTrace }) {
  const { row, context } = activeTrace;
  const sourceAssets = useMemo(() => buildUniqueSourceAssets(activeTrace), [activeTrace]);
  const sourceAssetInsights = useMemo(() => buildSourceAssetInsights(activeTrace), [activeTrace]);
  const [selectedSourceAssetId, setSelectedSourceAssetId] = useState<string | null>(null);

  useEffect(() => {
    if (sourceAssetInsights.length === 0) {
      if (selectedSourceAssetId !== null) {
        setSelectedSourceAssetId(null);
      }
      return;
    }

    if (!selectedSourceAssetId || !sourceAssetInsights.some((entry) => entry.sourceAsset.source_asset_id === selectedSourceAssetId)) {
      setSelectedSourceAssetId(sourceAssetInsights[0]?.sourceAsset.source_asset_id ?? null);
    }
  }, [selectedSourceAssetId, sourceAssetInsights]);

  const selectedAssetInsight =
    sourceAssetInsights.find((entry) => entry.sourceAsset.source_asset_id === selectedSourceAssetId) ??
    sourceAssetInsights[0] ??
    null;
  const primarySourceAsset = selectedAssetInsight?.sourceAsset ?? context.primary_source_asset ?? sourceAssets[0] ?? null;
  const sourceHref = resolveAssetHref(primarySourceAsset?.asset_path_or_url);
  const previewKind = getAssetPreviewKind(primarySourceAsset?.asset_path_or_url);
  const sanitizedAssetPath = sanitizeAssetPath(primarySourceAsset?.asset_path_or_url);
  const selectedSourceEvidence =
    primarySourceAsset === null
      ? context.content.evidence
      : context.content.evidence.filter((evidence) =>
          evidence.source_assets.some((asset) => asset.source_asset_id === primarySourceAsset.source_asset_id),
        );
  const selectedEvidenceLabels = selectedSourceEvidence
    .map((evidence) => evidence.evidence_label)
    .filter((value): value is string => Boolean(value));
  const assetExtension = sanitizedAssetPath?.split(".").pop()?.toUpperCase() ?? null;
  const previewTitle =
    previewKind === "pdf"
      ? "문서 내장 미리보기"
      : selectedAssetInsight?.isFigureAsset
        ? "Figure Preview"
        : previewKind === "image"
          ? "이미지 미리보기"
          : "직접 미리보기 불가";
  const previewBody =
    previewKind === "pdf"
      ? "PDF 원문을 패널 안에서 바로 확인할 수 있습니다."
      : selectedAssetInsight?.isFigureAsset
        ? "figure_or_diagram evidence에 연결된 원문 이미지 자산입니다."
        : previewKind === "image"
        ? "렌더된 원문 이미지를 즉시 확인할 수 있습니다."
        : primarySourceAsset?.asset_path_or_url?.includes("::")
          ? "압축 아카이브 내부 문서라 패널 내 미리보기를 제공하지 않습니다."
          : "HWP/HWPX 등 편집 포맷은 외부 앱 연결 또는 후속 렌더 파이프라인이 필요합니다.";

  return (
    <aside className={styles.tracePanel}>
      <div className={styles.traceHead}>
        <div>
          <p className={styles.eyebrow}>
            {context.policy.policy_name} / {context.bucket.resource_category_label}
          </p>
          <h2 className={styles.traceTitle}>{row.content_label}</h2>
          <div className={styles.traceChipRow}>
            <Chip tone="primary">{row.policy_item_content_id}</Chip>
            <Chip>{row.content_type}</Chip>
            {row.primary_strategy ? <Chip>{row.primary_strategy.label}</Chip> : null}
          </div>
        </div>
        <span className={styles.traceBadge}>trace ready</span>
      </div>

      <div className={styles.traceSummaryGrid}>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>대표 그룹</span>
          <strong className={styles.traceSummaryValue}>{context.group.group_label}</strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>전략 축</span>
          <strong className={styles.traceSummaryValue}>{row.primary_strategy?.label ?? "전략 미지정"}</strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>기술 태그</span>
          <strong className={styles.traceSummaryValue}>
            {context.tech_terms.length > 0 ? context.tech_terms.map((term) => term.label).join(" / ") : "기술 태그 없음"}
          </strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>세부기술</span>
          <strong className={styles.traceSummaryValue}>
            {context.tech_subterms.length > 0 ? context.tech_subterms.map((term) => term.label).join(" / ") : "세부기술 없음"}
          </strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>representation</span>
          <strong className={styles.traceSummaryValue}>
            {[...new Set(context.content.evidence.map((evidence) => evidence.representation_type))]
              .map((entry) => formatRepresentationLabel(entry))
              .join(" / ")}
          </strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>raw members</span>
          <strong className={styles.traceSummaryValue}>{context.group.member_items.length}</strong>
        </div>
        <div className={styles.traceSummaryItem}>
          <span className={styles.traceSummaryLabel}>source</span>
          <strong className={styles.traceSummaryValue}>
            {primarySourceAsset?.source_asset_id ?? "원문 자산 미상"} · {sourceAssets.length} asset
          </strong>
        </div>
      </div>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>01 Content Statement</p>
        <div className={styles.traceBlock}>
          <p>{row.content_statement}</p>
          <p className={styles.mutedText}>{row.content_summary || "대표 내용 요약 없음"}</p>
        </div>
      </section>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>02 Source Assets</p>
        <div className={styles.traceBlock}>
          {sourceAssets.length === 0 ? (
            <p className={styles.emptyNote}>연결된 원문 자산이 없습니다.</p>
          ) : (
            <div className={styles.sourceAssetCompareList}>
              {sourceAssetInsights.map((entry) => {
                const asset = entry.sourceAsset;
                const href = resolveAssetHref(asset.asset_path_or_url);
                const assetPath = sanitizeAssetPath(asset.asset_path_or_url) ?? asset.asset_path_or_url;
                const isSelected = asset.source_asset_id === primarySourceAsset?.source_asset_id;

                return (
                  <div
                    key={asset.source_asset_id}
                    className={isSelected ? styles.sourceAssetCompareCardActive : styles.sourceAssetCompareCard}
                  >
                    <button
                      type="button"
                      className={styles.sourceAssetSelect}
                      onClick={() => setSelectedSourceAssetId(asset.source_asset_id)}
                    >
                      <div className={styles.sourceAssetCompareHead}>
                        <div>
                          <strong>{asset.source_asset_id}</strong>
                          <p className={styles.mutedText}>
                            {asset.asset_type}
                            {asset.section_id ? ` · ${asset.section_id}` : ""}
                            {asset.page_no ? ` · page ${asset.page_no}` : ""}
                          </p>
                        </div>
                        <span className={styles.sourceAssetCount}>{entry.evidenceCount} evidence</span>
                      </div>

                      <div className={styles.sourceAssetCompareMeta}>
                        {entry.representationTypes.map((representationType) => (
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
                        {entry.isFigureAsset ? <span className={styles.sourceAssetFigureBadge}>figure image</span> : null}
                      </div>

                      <p className={styles.sourceAssetCompareBody}>
                        {entry.evidenceLabels[0] ??
                          (entry.locationValues.length > 0 ? entry.locationValues.join(" / ") : "위치 정보 없음")}
                      </p>
                      <span className={styles.sourcePath}>{assetPath}</span>
                    </button>

                    <div className={styles.sourceAssetCompareActions}>
                      <span className={styles.mutedText}>{isSelected ? "preview selected" : "select to preview"}</span>
                      {href ? (
                        <a className={styles.traceLink} href={href} target="_blank" rel="noreferrer">
                          원문 열기
                        </a>
                      ) : (
                        <span className={styles.mutedText}>링크 없음</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>03 Source Preview</p>
        <div className={styles.previewShell}>
          <div className={styles.previewHead}>
            <div>
              <p className={styles.previewTitle}>
                {previewTitle}
                {primarySourceAsset ? ` · ${primarySourceAsset.source_asset_id}` : ""}
              </p>
              <p className={styles.previewBody}>{previewBody}</p>
              {selectedEvidenceLabels[0] ? <p className={styles.previewBody}>{selectedEvidenceLabels[0]}</p> : null}
            </div>
            {sourceHref ? (
              <a className={styles.previewAction} href={sourceHref} target="_blank" rel="noreferrer">
                원문 열기
              </a>
            ) : null}
          </div>

          <div className={styles.previewFrame}>
            {previewKind === "image" && sourceHref ? (
              <img
                className={styles.previewImage}
                src={sourceHref}
                alt={`${row.content_label} source preview`}
                loading="lazy"
              />
            ) : null}
            {previewKind === "pdf" && sourceHref ? (
              <iframe className={styles.previewDocument} src={sourceHref} title={`${row.content_label} PDF preview`} />
            ) : null}
            {previewKind !== "image" && previewKind !== "pdf" ? (
              <div className={styles.previewFallback}>
                <div className={styles.previewFallbackGlow} />
                <div className={styles.previewFallbackCard}>
                  <p className={styles.previewFallbackType}>{assetExtension ?? "SOURCE"}</p>
                  <h3 className={styles.previewFallbackTitle}>{primarySourceAsset?.source_asset_id ?? "원문 자산"}</h3>
                  <p className={styles.previewFallbackBody}>{previewBody}</p>
                  <div className={styles.previewMetaStrip}>
                    <span>{primarySourceAsset?.asset_type ?? "asset type 미상"}</span>
                    <span>{sanitizedAssetPath ?? "경로 미상"}</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>04 Group Context</p>
        <div className={styles.traceBlock}>
          <div className={styles.traceMetaRow}>
            <p>{context.group.policy_item_group_id}</p>
            <p>
              {context.group.contents.length} contents · {context.group.member_items.length} members
            </p>
          </div>
          <p>{context.group.group_description || context.group.group_summary}</p>
          <div className={styles.taxonomyRow}>
            {context.strategy_terms.map((term) => (
              <Chip key={term.term_id} tone={term.is_primary ? "primary" : "neutral"}>
                {term.label}
              </Chip>
            ))}
            {context.tech_terms.map((term) => (
              <Chip key={term.term_id}>{term.label}</Chip>
            ))}
            {context.tech_subterms.map((term) => (
              <Chip key={term.term_id}>{term.label}</Chip>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>05 Evidence Stack</p>
        <div className={styles.traceBlock}>
          <div className={styles.traceMetaRow}>
            <p>{primarySourceAsset ? `${primarySourceAsset.source_asset_id} 기준 evidence` : "전체 evidence"}</p>
            <p>
              {selectedSourceEvidence.length} / {context.content.evidence.length} evidences
            </p>
          </div>
          {context.content.evidence.length === 0 ? (
            <p className={styles.emptyNote}>연결된 evidence가 없습니다.</p>
          ) : (
            <div className={styles.evidenceList}>
              {selectedSourceEvidence.map((evidence) => {
                const evidenceAsset = evidence.source_assets[0];
                const evidenceHref = resolveAssetHref(evidenceAsset?.asset_path_or_url);

                return (
                  <div key={evidence.derived_representation_id} className={styles.evidenceCard}>
                    <div className={styles.evidenceHead}>
                      <strong>
                        {evidence.source_policy_item_label}
                        {evidence.location_value ? ` · ${evidence.location_value}` : ""}
                      </strong>
                      <span>{evidence.derived_representation_id}</span>
                    </div>
                    <p>{evidence.evidence_text}</p>
                    <div className={styles.evidenceMeta}>
                      <span>{evidence.source_object_type || "source object 미상"}</span>
                      <span>{evidence.representation_type}</span>
                      <span>{evidence.source_assets.map((asset) => asset.source_asset_id).join(" / ")}</span>
                      {evidenceHref ? (
                        <a href={evidenceHref} target="_blank" rel="noreferrer">
                          원문 링크
                        </a>
                      ) : (
                        <span>원문 링크 없음</span>
                      )}
                    </div>
                    {evidence.evidence_label ? <p className={styles.evidenceLabel}>{evidence.evidence_label}</p> : null}
                    {evidence.structured_payload_path ? (
                      <p className={styles.evidencePayloadPath}>{evidence.structured_payload_path}</p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className={styles.traceSection}>
        <p className={styles.traceLabel}>06 Raw Members</p>
        <div className={styles.traceBlock}>
          {context.group.member_items.length === 0 ? (
            <p className={styles.emptyNote}>연결된 raw member가 없습니다.</p>
          ) : (
            <div className={styles.memberList}>
              {context.group.member_items.map((member) => (
                <div key={member.policy_item_id} className={styles.memberRow}>
                  <span className={member.is_representative ? styles.memberRolePrimary : styles.memberRole}>
                    {member.is_representative ? "REP" : member.member_role}
                  </span>
                  <div className={styles.memberCopy}>
                    <strong>{member.item_label}</strong>
                    <p>{member.item_statement}</p>
                    <span className={styles.memberMeta}>
                      {member.policy_item_id} · {member.derived_representation_id}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </aside>
  );
}

export function TracePanel({ activeTrace }: TracePanelProps) {
  if (!activeTrace) {
    return (
      <aside className={styles.tracePanel}>
        <EmptyState
          eyebrow="Trace Detail"
          title="대표 내용을 선택하면"
          body="중앙 테이블에서 행을 선택하면 group context, raw members, evidence stack, source asset을 오른쪽에서 이어서 보여줍니다."
        />
      </aside>
    );
  }

  return <TracePanelContent activeTrace={activeTrace} />;
}
