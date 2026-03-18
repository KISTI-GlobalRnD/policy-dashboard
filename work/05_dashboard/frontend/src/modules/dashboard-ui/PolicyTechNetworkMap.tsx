import { Panel } from "../../shared/ui/Panel";
import { formatNumber } from "../../shared/lib/format";
import type { MatrixDomainSummary, PolicyTechMatrixRow } from "../dashboard-model/mappingWorkbenchSelectors";
import { EmptyState } from "../../shared/ui/EmptyState";
import styles from "./MappingWorkbenchPage.module.css";

type PolicyTechNetworkMapProps = {
  rows: PolicyTechMatrixRow[];
  domains: MatrixDomainSummary[];
  selectedPolicyId: string | null;
  selectedDomainId: string | null;
  onSelectPolicy: (policyId: string | null) => void;
  onSelectDomain: (domainId: string | null) => void;
  onSelectCell: (policyId: string, domainId: string) => void;
};

type PolicyNode = {
  id: string;
  type: "policy";
  label: string;
  x: number;
  y: number;
  r: number;
  contentCount: number;
  evidenceCount: number;
  policyId: string;
  isSelected: boolean;
  isHighlighted: boolean;
};

type DomainNode = {
  id: string;
  type: "domain";
  label: string;
  shortLabel: string;
  x: number;
  y: number;
  r: number;
  contentCount: number;
  mappedPolicyCount: number;
  mappedContentCount: number;
  evidenceCount: number;
  domainId: string;
  isSelected: boolean;
  isHighlighted: boolean;
};

type GraphLink = {
  key: string;
  policyId: string;
  domainId: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  contentCount: number;
  evidenceCount: number;
  reviewedContentCount: number;
  isHighlighted: boolean;
};

function toUpperSafe(value: string | null | undefined) {
  return String(value ?? "").toUpperCase();
}

export function PolicyTechNetworkMap({
  rows,
  domains,
  selectedPolicyId,
  selectedDomainId,
  onSelectPolicy,
  onSelectDomain,
  onSelectCell,
}: PolicyTechNetworkMapProps) {
  const { policyNodes, domainNodes, links, totalConnections, totalNodes, selectedPolicyCount, selectedDomainCount } =
    (() => {
      const policyContentById = new Map<string, number>();
      const evidenceByPolicy = new Map<string, number>();
      const normalizedLinks: GraphLink[] = [];

      for (const row of rows) {
        for (const cell of row.cells) {
          if (cell.techDomainId === "unmapped" || cell.contentCount <= 0) {
            continue;
          }

          const sourceX = 0;
          const sourceY = 0;
          const targetX = 0;
          const targetY = 0;

          normalizedLinks.push({
            key: `${cell.policyId}:${cell.techDomainId}`,
            policyId: cell.policyId,
            domainId: cell.techDomainId,
            sourceX,
            sourceY,
            targetX,
            targetY,
            contentCount: cell.contentCount,
            evidenceCount: cell.evidenceCount,
            reviewedContentCount: cell.reviewedContentCount,
            isHighlighted:
              (selectedPolicyId !== null && selectedPolicyId === cell.policyId) ||
              (selectedDomainId !== null && selectedDomainId === cell.techDomainId),
          });

          const currentContent = policyContentById.get(cell.policyId) ?? 0;
          policyContentById.set(cell.policyId, currentContent + cell.contentCount);
          const currentEvidence = evidenceByPolicy.get(cell.policyId) ?? 0;
          evidenceByPolicy.set(cell.policyId, currentEvidence + cell.evidenceCount);
        }
      }

      const visibleDomainIds = new Set<string>();
      for (const link of normalizedLinks) {
        visibleDomainIds.add(link.domainId);
      }

      const chartWidth = 1040;
      const chartHeight = 520;
      const xPadding = 84;
      const policyY = 150;
      const domainY = 388;
      const policyNodes: PolicyNode[] = [];
      const domainNodes: DomainNode[] = [];

      const activeRows = rows.filter((row) => row.cells.some((cell) => cell.contentCount > 0 && cell.techDomainId !== "unmapped"));
      const visiblePolicies =
        activeRows.length > 0 || selectedPolicyId
          ? activeRows
          : rows.length > 0
            ? [rows[0]]
            : [];

      visiblePolicies.forEach((row, index) => {
        const weight = policyContentById.get(row.policy.policy_id) ?? 0;
        const x = xPadding + (visiblePolicies.length === 1 ? chartWidth / 2 : (index / (visiblePolicies.length - 1)) * (chartWidth - xPadding * 2) + xPadding);
        const policyRadius = Math.max(22, Math.min(42, Math.sqrt(weight || 1) * 6));
        const isSelected = selectedPolicyId === row.policy.policy_id;
        const isHighlighted = selectedDomainId !== null && normalizedLinks.some((link) => link.domainId === selectedDomainId && link.policyId === row.policy.policy_id);

        policyNodes.push({
          id: `policy-${row.policy.policy_id}`,
          type: "policy",
          label: row.policy.policy_name,
          x,
          y: policyY,
          r: policyRadius,
          contentCount: weight,
          evidenceCount: evidenceByPolicy.get(row.policy.policy_id) ?? 0,
          policyId: row.policy.policy_id,
          isSelected,
          isHighlighted,
        });
      });

      const visibleDomains = domains
        .filter((domain) => domain.termId !== "unmapped" && (domain.contentCount > 0 || visibleDomainIds.has(domain.termId) || domain.termId === selectedDomainId))
        .sort((left, right) => (right.contentCount === left.contentCount ? right.label.localeCompare(left.label, "ko") : right.contentCount - left.contentCount));

      visibleDomains.forEach((domain, index) => {
        const x = xPadding + (visibleDomains.length === 1 ? chartWidth / 2 : (index / (visibleDomains.length - 1)) * (chartWidth - xPadding * 2) + xPadding);
        const domainRadius = Math.max(16, Math.min(34, Math.sqrt(domain.contentCount || 1) * 5.2));
        const isSelected = selectedDomainId === domain.termId;
        const isHighlighted =
          selectedPolicyId !== null && normalizedLinks.some((link) => link.policyId === selectedPolicyId && link.domainId === domain.termId);

        domainNodes.push({
          id: `domain-${domain.termId}`,
          type: "domain",
          label: domain.label,
          shortLabel: domain.shortLabel,
          x,
          y: domainY,
          r: domainRadius,
          contentCount: domain.contentCount,
          mappedPolicyCount: domain.mappedPolicyCount,
          mappedContentCount: domain.contentCount,
          evidenceCount: domain.evidenceCount,
          domainId: domain.termId,
          isSelected,
          isHighlighted,
        });
      });

      const domainNodeMap = new Map(domainNodes.map((node) => [node.domainId, node]));
      const policyNodeMap = new Map(policyNodes.map((node) => [node.policyId, node]));

      const links = normalizedLinks
        .map((link): GraphLink | null => {
          const source = policyNodeMap.get(link.policyId);
          const target = domainNodeMap.get(link.domainId);
          if (!source || !target) {
            return null;
          }

          return {
            ...link,
            sourceX: source.x,
            sourceY: source.y + source.r,
            targetX: target.x,
            targetY: target.y - target.r,
          };
        })
        .filter((item): item is GraphLink => item !== null);

      return {
        policyNodes,
        domainNodes,
        links,
        totalConnections: links.length,
        totalNodes: policyNodes.length + domainNodes.length,
        selectedPolicyCount: policyNodes.filter((node) => node.isSelected).length,
        selectedDomainCount: domainNodes.filter((node) => node.isSelected).length,
      };
    })();

  const maxContent = Math.max(...links.map((link) => link.contentCount), 1);
  const maxEvidence = Math.max(...links.map((link) => link.evidenceCount), 1);
  const chartWidth = 1040;
  const chartHeight = 520;

  if (totalConnections === 0 || totalNodes === 0) {
    return (
      <Panel className={styles.networkPanel}>
        <EmptyState
          eyebrow="Network Map"
          title="현재 필터에서 표시할 관계가 없습니다."
          body="필터를 완화하거나 정책/기술 대분류를 확장해 노드를 다시 구성해 보세요."
        />
      </Panel>
    );
  }

  return (
    <Panel className={styles.networkPanel}>
      <div className={styles.networkHeader}>
        <div>
          <p className={styles.eyebrow}>Network View</p>
          <h2 className={styles.sectionTitle}>정책-기술 대분류 네트워크</h2>
        </div>
        <p className={styles.sectionBody}>
          연결 데이터 출처: 현재 화면의 정책×기술 매트릭스(내용 수/근거 수 집계) 기반으로 네트워크를 생성합니다.
          노드를 클릭하면 인스펙터로 이동하고, 엣지를 클릭하면 해당 정책-기술 셀로 드릴다운됩니다.
        </p>
      </div>

      <div className={styles.networkSummary}>
        <p className={styles.networkSummaryCell}>
          <span>활성 노드</span>
          <strong>{formatNumber(totalNodes)}</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>연결 수</span>
          <strong>{formatNumber(totalConnections)}</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>선택 정책</span>
          <strong>{formatNumber(selectedPolicyCount)}개</strong>
        </p>
        <p className={styles.networkSummaryCell}>
          <span>선택 기술</span>
          <strong>{formatNumber(selectedDomainCount)}개</strong>
        </p>
      </div>

      <div className={styles.networkWrap}>
        <svg
          className={styles.networkCanvas}
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="정책과 기술 대분류 네트워크 연결도"
        >
          <defs>
            <linearGradient id="networkLineActive" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(8, 145, 178, 0.22)" />
              <stop offset="100%" stopColor="rgba(8, 145, 178, 0.74)" />
            </linearGradient>
            <linearGradient id="networkLineDimmed" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(71, 85, 105, 0.16)" />
              <stop offset="100%" stopColor="rgba(71, 85, 105, 0.5)" />
            </linearGradient>
          </defs>

          {links.map((link) => {
            const intensity = Math.max(1.5, (link.contentCount / maxContent) * 8);
            const evidenceOpacity = Math.max(0.22, (link.evidenceCount / maxEvidence) * 0.74);

            return (
              <g key={link.key} className={styles.networkLinkLayer}>
                <line
                  x1={link.sourceX}
                  y1={link.sourceY}
                  x2={link.targetX}
                  y2={link.targetY}
                  stroke={link.isHighlighted ? "url(#networkLineActive)" : "url(#networkLineDimmed)"}
                  strokeWidth={intensity}
                  strokeLinecap="round"
                  opacity={link.isHighlighted ? 0.95 : evidenceOpacity}
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
                <title>{`${link.policyId} → ${link.domainId}: content ${link.contentCount}, reviewed ${link.reviewedContentCount}`}</title>
              </g>
            );
          })}

          {domainNodes.map((node) => (
            <g
              key={node.id}
              className={styles.networkNode}
              onClick={() => onSelectDomain(node.isSelected ? null : node.domainId)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectDomain(node.isSelected ? null : node.domainId);
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={`${node.label} 영역 선택`}
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                className={node.isSelected ? styles.domainNodeSelected : node.isHighlighted ? styles.domainNodeHighlighted : styles.domainNode}
              />
              <text x={node.x} y={node.y - node.r - 8} textAnchor="middle" className={styles.networkLabel}>
                {node.shortLabel}
              </text>
              <text x={node.x} y={node.y + 4} textAnchor="middle" className={styles.networkNodeTitle}>
                {node.label}
              </text>
              <text x={node.x} y={node.y + 20} textAnchor="middle" className={styles.networkNodeMeta}>
                {formatNumber(node.contentCount)}C
              </text>
              <title>
                {`${node.label}\ncontent ${node.contentCount}\npolicies ${node.mappedPolicyCount}\nevidence ${formatNumber(node.evidenceCount)}`}
              </title>
            </g>
          ))}

          {policyNodes.map((node) => (
            <g
              key={node.id}
              className={styles.networkNode}
              onClick={() => onSelectPolicy(node.isSelected ? null : node.policyId)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectPolicy(node.isSelected ? null : node.policyId);
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
              <text x={node.x} y={node.y + 19} textAnchor="middle" className={styles.networkNodeMeta}>
                {formatNumber(node.contentCount)}C
              </text>
              <title>{`${node.label}\ncontent ${node.contentCount}\nevidence ${formatNumber(node.evidenceCount)}`}</title>
            </g>
          ))}
        </svg>
      </div>

      <p className={styles.networkFooter}>
        선명도는 content 수 대비, 선 굵기는 같은 관계의 커버리지 비율을 반영합니다.
      </p>
    </Panel>
  );
}
