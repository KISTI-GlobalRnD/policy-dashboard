import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import { EmptyState } from "../../shared/ui/EmptyState";
import { buildOntologyNetworkBoard } from "../dashboard-model/ontologyNetworkSelectors";
import type { TechnologyLensProjection } from "../dashboard-data/dashboard.types";
import styles from "./MappingWorkbenchPage.module.css";

type OntologyTechNetworkMapProps = {
  projection: TechnologyLensProjection;
  search: string;
  activePolicyId: string | null;
  selectedPolicyId: string | null;
  selectedDomainId: string | null;
  onSelectPolicy: (policyId: string | null) => void;
  onSelectDomain: (domainId: string | null) => void;
  onSelectCell: (policyId: string, domainId: string) => void;
};

function toUpperSafe(value: string | null | undefined) {
  return String(value ?? "").toUpperCase();
}

export function OntologyTechNetworkMap({
  projection,
  search,
  activePolicyId,
  selectedPolicyId,
  selectedDomainId,
  onSelectPolicy,
  onSelectDomain,
  onSelectCell,
}: OntologyTechNetworkMapProps) {
  const { policyNodes, domainNodes, links, totalConnections, totalNodes, chartWidth, chartHeight, selectedPolicyCount, selectedDomainCount } =
    buildOntologyNetworkBoard(projection, {
      search,
      activePolicyId,
      selectedPolicyId,
      selectedDomainId,
    });

  const maxContent = Math.max(...links.map((link) => link.contentCount), 1);
  const maxEvidence = Math.max(...links.map((link) => link.evidenceCount), 1);

  if (totalNodes === 0 || totalConnections === 0) {
    return (
      <Panel className={styles.networkPanel}>
        <EmptyState
          eyebrow="정책-기술 연결"
          title="현재 정책/기술 연결이 없습니다"
          body="필터/검색 조건을 완화하거나 정책-기술 연결 조건을 다시 확인해 주세요."
        />
      </Panel>
    );
  }

  return (
    <Panel className={styles.networkPanel}>
      <div className={styles.networkHeader}>
        <div>
          <p className={styles.eyebrow}>정책-기술 연결</p>
          <h2 className={styles.sectionTitle}>정책별 집중 기술영역 지도</h2>
        </div>
        <p className={styles.sectionBody}>
          노드를 클릭해 정책 또는 기술영역을 고정하고, 연결선을 클릭하면 근거 추적 화면으로 이동해 원문 확인까지 이어갑니다.
        </p>
      </div>

      <div className={styles.networkSummary}>
        <p className={styles.networkSummaryCell}>
          <span>화면 노드</span>
          <strong>{formatNumber(totalNodes)}개</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>정책-기술 연결</span>
          <strong>{formatNumber(totalConnections)}</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>선택된 정책</span>
          <strong>{formatNumber(selectedPolicyCount)}개</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>선택된 기술영역</span>
          <strong>{formatNumber(selectedDomainCount)}개</strong>
        </p>
      </div>

      <div className={styles.networkWrap}>
        <svg
          className={styles.networkCanvas}
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="기술축 중심 네트워크 연결도"
        >
          <defs>
            <linearGradient id="ontologyNetworkLineActive" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(5, 150, 105, 0.22)" />
              <stop offset="100%" stopColor="rgba(4, 120, 87, 0.74)" />
            </linearGradient>
            <linearGradient id="ontologyNetworkLineDimmed" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(71, 85, 105, 0.16)" />
              <stop offset="100%" stopColor="rgba(71, 85, 105, 0.5)" />
            </linearGradient>
          </defs>

          {links.map((link) => {
            const intensity = Math.max(1.8, (link.contentCount / maxContent) * 8);
            const evidenceOpacity = Math.max(0.18, (link.evidenceCount / maxEvidence) * 0.75);

            return (
              <g key={link.key} className={styles.networkLinkLayer}>
                <line
                  x1={link.sourceX}
                  y1={link.sourceY}
                  x2={link.targetX}
                  y2={link.targetY}
                  stroke={link.isHighlighted ? "url(#ontologyNetworkLineActive)" : "url(#ontologyNetworkLineDimmed)"}
                  strokeWidth={intensity}
                  strokeLinecap="round"
                  opacity={link.isHighlighted ? 0.98 : evidenceOpacity}
                  className={styles.networkLink}
                  onClick={() => onSelectCell(link.policyId, link.domainId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelectCell(link.policyId, link.domainId);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  aria-label={`${toUpperSafe(link.policyId)}-${toUpperSafe(link.domainId)} 연결`}
                />
                <title>{`${link.policyId} → ${link.domainId}: 내용 ${link.contentCount}, 근거 ${link.evidenceCount}`}</title>
              </g>
            );
          })}

          {domainNodes.map((node) => (
            <g
              key={node.id}
              className={styles.networkNode}
              onClick={() => onSelectDomain(node.isSelected ? null : node.domainId ?? null)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectDomain(node.isSelected ? null : node.domainId ?? null);
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={`${node.label} 기술 루트 선택`}
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                className={node.isSelected ? styles.domainNodeSelected : node.isHighlighted ? styles.domainNodeHighlighted : styles.domainNode}
              />
              <text x={node.x} y={node.y - node.r - 8} textAnchor="middle" className={styles.networkLabel}>
                {node.label}
              </text>
              <text x={node.x} y={node.y + 4} textAnchor="middle" className={styles.networkNodeTitle}>
                {formatNumber(node.groupCount)}개 그룹
              </text>
              <text x={node.x} y={node.y + 20} textAnchor="middle" className={styles.networkNodeMeta}>
                {formatNumber(node.contentCount)}건
              </text>
              <title>
                {`${node.label}\n내용 ${node.contentCount}\n그룹 ${node.groupCount}\n근거 ${node.evidenceCount}`}
              </title>
            </g>
          ))}

          {policyNodes.map((node) => (
            <g
              key={node.id}
              className={styles.networkNode}
              onClick={() => onSelectPolicy(node.isSelected ? null : node.policyId ?? null)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectPolicy(node.isSelected ? null : node.policyId ?? null);
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={`${node.label} 정책 선택`}
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                className={node.isSelected ? styles.policyNodeSelected : node.isHighlighted ? styles.policyNodeHighlighted : styles.policyNode}
              />
              <text x={node.x} y={node.y + 4} textAnchor="middle" className={styles.networkNodeTitle}>
                {node.label}
              </text>
              <text x={node.x} y={node.y + 20} textAnchor="middle" className={styles.networkNodeMeta}>
                {formatNumber(node.contentCount)}건
              </text>
              <title>{`${node.label}\n내용 ${node.contentCount}\n근거 ${node.evidenceCount}`}</title>
            </g>
          ))}
        </svg>
      </div>

      <p className={styles.networkFooter}>선 두께는 정책-기술 연결 건수, 선 투명도는 근거 건수를 반영합니다.</p>
    </Panel>
  );
}
