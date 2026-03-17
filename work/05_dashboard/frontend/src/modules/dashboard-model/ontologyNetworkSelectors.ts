import type { TechnologyLensProjection } from "../dashboard-data/dashboard.types";

type OntologyTechEdge = {
  policyId: string;
  domainId: string;
  domainLabel: string;
  contentCount: number;
  evidenceCount: number;
  groupCount: number;
  groupIds: string[];
};

type NormalizedPolicy = {
  policyId: string;
  policyName: string;
  groupCount: number;
  contentCount: number;
  evidenceCount: number;
};

type NormalizedDomain = {
  domainId: string;
  domainLabel: string;
  groupCount: number;
  contentCount: number;
  policyCount: number;
  evidenceCount: number;
};

export type OntologyNetworkNode = {
  id: string;
  type: "policy" | "domain";
  policyId?: string;
  domainId?: string;
  label: string;
  x: number;
  y: number;
  r: number;
  isSelected: boolean;
  isHighlighted: boolean;
  contentCount: number;
  evidenceCount: number;
  groupCount: number;
};

export type OntologyNetworkLink = {
  key: string;
  policyId: string;
  domainId: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  contentCount: number;
  evidenceCount: number;
  groupCount: number;
  isHighlighted: boolean;
};

export type OntologyNetworkBoard = {
  policyNodes: OntologyNetworkNode[];
  domainNodes: OntologyNetworkNode[];
  links: OntologyNetworkLink[];
  chartWidth: number;
  chartHeight: number;
  totalNodes: number;
  totalConnections: number;
  selectedPolicyCount: number;
  selectedDomainCount: number;
};

type BuildOntologyNetworkOptions = {
  selectedPolicyId: string | null;
  selectedDomainId: string | null;
  search: string;
  activePolicyId: string | null;
};

function normalizeText(value: string) {
  return value.trim().toLowerCase();
}

function toNumber(value: unknown) {
  return Number.isFinite(Number(value)) ? Number(value) : 0;
}

function extractEvidenceCount(content: { evidence_count?: unknown; evidence?: unknown[] }) {
  const explicit = toNumber(content.evidence_count);
  if (explicit > 0) {
    return explicit;
  }

  return Array.isArray(content.evidence) ? content.evidence.length : 0;
}

function createLayout({ count, base, max }: { count: number; base: number; max: number }) {
  return Math.max(base, Math.min(max, Math.sqrt(Math.max(1, count)) * 3.9));
}

function hasQueryMatch(text: string, query: string) {
  return query.length === 0 || normalizeText(text).includes(query);
}

export function buildOntologyNetworkBoard(
  projection: TechnologyLensProjection,
  options: BuildOntologyNetworkOptions,
): OntologyNetworkBoard {
  const query = normalizeText(options.search ?? "");
  const activePolicyId = options.activePolicyId ?? null;
  const selectedPolicyId = options.selectedPolicyId;
  const selectedDomainId = options.selectedDomainId;

  const domainNodesMap = new Map<string, NormalizedDomain>();
  const policyNodesMap = new Map<string, NormalizedPolicy>();
  const edgeMap = new Map<string, OntologyTechEdge>();
  const visiblePolicyIds = new Set<string>();

  for (const domain of projection.tech_domains ?? []) {
    if (!domain?.tech_domain_id || !domain?.tech_domain_label) {
      continue;
    }

    const domainId = domain.tech_domain_id;
    const domainLabel = domain.tech_domain_label;
    const policyGroupsById = new Map<string, { policyName: string; contentCount: number; evidenceCount: number; groupCount: number; groupIds: string[] }>();

    for (const group of domain.groups ?? []) {
      const policyId = group?.policy?.policy_id;
      const policyName = group?.policy?.policy_name;
      if (!policyId || !policyName) {
        continue;
      }

      const contents = group.contents ?? [];
      const contentCount = contents.length;
      const groupEvidenceCount = contents.reduce((sum, content) => sum + extractEvidenceCount(content as never), 0);

      if (contentCount === 0) {
        continue;
      }

      visiblePolicyIds.add(policyId);

      const entry = policyGroupsById.get(policyId) ?? {
        policyName,
        contentCount: 0,
        evidenceCount: 0,
        groupCount: 0,
        groupIds: [],
      };

      const current = {
        ...entry,
        contentCount: entry.contentCount + contentCount,
        evidenceCount: entry.evidenceCount + groupEvidenceCount,
        groupCount: entry.groupCount + 1,
        groupIds: [...entry.groupIds, group.policy_item_group_id].filter(Boolean),
      };
      policyGroupsById.set(policyId, current);
    }

    const policyRows = [...policyGroupsById.entries()].filter(([policyId]) => policyId);

    for (const [policyId, summary] of policyRows) {
      const edgeKey = `${policyId}::${domainId}`;
      const currentEdge = edgeMap.get(edgeKey);
      if (currentEdge) {
        currentEdge.contentCount += summary.contentCount;
        currentEdge.evidenceCount += summary.evidenceCount;
        currentEdge.groupCount += summary.groupCount;
        currentEdge.groupIds = [...currentEdge.groupIds, ...summary.groupIds];
        continue;
      }

      edgeMap.set(edgeKey, {
        policyId,
        domainId,
        domainLabel,
        contentCount: summary.contentCount,
        evidenceCount: summary.evidenceCount,
        groupCount: summary.groupCount,
        groupIds: summary.groupIds,
      });
    }

    let domainContentCount = 0;
    let domainEvidenceCount = 0;
    let domainPolicyCount = 0;

    for (const [policyId, summary] of policyRows) {
      domainContentCount += summary.contentCount;
      domainEvidenceCount += summary.evidenceCount;
      if (summary.contentCount > 0) {
        domainPolicyCount += 1;
      }
      const policyNode =
        policyNodesMap.get(policyId) ?? {
          policyId,
          policyName: summary.policyName,
          groupCount: 0,
          contentCount: 0,
          evidenceCount: 0,
        };
      policyNodesMap.set(policyId, {
        policyId,
        policyName: summary.policyName,
        groupCount: policyNode.groupCount + summary.groupCount,
        contentCount: policyNode.contentCount + summary.contentCount,
        evidenceCount: policyNode.evidenceCount + summary.evidenceCount,
      });
    }

    domainNodesMap.set(domainId, {
      domainId,
      domainLabel,
      groupCount: toNumber(domain.group_count) || [...policyRows].length,
      contentCount: domainContentCount || toNumber(domain.content_count),
      policyCount: domainPolicyCount,
      evidenceCount: domainEvidenceCount,
    });
  }

  const filteredPolicyIds = new Set<string>();
  const nodesByPolicy = [...policyNodesMap.entries()]
    .map(([policyId, summary]) => ({ policyId, ...summary }))
    .filter((entry) => entry.contentCount > 0)
    .map((entry) => ({ ...entry }));

  const policyNodeList: OntologyNetworkNode[] = [];

  for (const entry of nodesByPolicy) {
    const policyName = entry.policyName || entry.policyId;
    const nodeMatchesSearch = hasQueryMatch(`${entry.policyName} ${entry.policyId}`, query);
    if (!nodeMatchesSearch && query && activePolicyId !== entry.policyId) {
      continue;
    }

    const isSelected = selectedPolicyId === entry.policyId;
    const isHighlighted =
      selectedDomainId !== null &&
      [...edgeMap.values()].some((edge) => edge.policyId === entry.policyId && edge.domainId === selectedDomainId);

    filteredPolicyIds.add(entry.policyId);
    policyNodeList.push({
      id: `policy-${entry.policyId}`,
      type: "policy",
      policyId: entry.policyId,
      label: policyName,
      x: 0,
      y: 0,
      r: createLayout({ count: entry.contentCount, base: 20, max: 40 }),
      isSelected,
      isHighlighted,
      contentCount: entry.contentCount,
      evidenceCount: entry.evidenceCount,
      groupCount: entry.groupCount,
    });
  }

  const filteredDomainRows = [...domainNodesMap.entries()]
    .map(([domainId, summary]) => ({ domainId, ...summary }))
    .filter((entry) => entry.contentCount > 0)
    .filter((entry) => {
      if (query.length === 0) {
        return true;
      }

      const matchesQuery = hasQueryMatch(`${entry.domainLabel} ${entry.domainId}`, query);
      if (matchesQuery || selectedDomainId === entry.domainId) {
        return true;
      }

      return [...edgeMap.values()].some((edge) => edge.domainId === entry.domainId && filteredPolicyIds.has(edge.policyId));
    });

  const domainNodeList: OntologyNetworkNode[] = [];
  for (const entry of filteredDomainRows) {
    const isSelected = selectedDomainId === entry.domainId;
    const isHighlighted =
      selectedPolicyId !== null &&
      [...edgeMap.values()].some((edge) => edge.policyId === selectedPolicyId && edge.domainId === entry.domainId);

    domainNodeList.push({
      id: `domain-${entry.domainId}`,
      type: "domain",
      domainId: entry.domainId,
      label: entry.domainLabel,
      x: 0,
      y: 0,
      r: createLayout({ count: entry.contentCount, base: 16, max: 34 }),
      isSelected,
      isHighlighted,
      contentCount: entry.contentCount,
      evidenceCount: entry.evidenceCount,
      groupCount: entry.groupCount,
    });
  }

  if (policyNodeList.length === 0 || domainNodeList.length === 0) {
    const maxNodesInRow = Math.max(policyNodeList.length, domainNodeList.length, 1);
    const fallbackWidth = Math.max(680, Math.min(1320, maxNodesInRow * 150 + 140));

    return {
      policyNodes: policyNodeList,
      domainNodes: domainNodeList,
      links: [],
      chartWidth: fallbackWidth,
      chartHeight: 320,
      totalNodes: policyNodeList.length + domainNodeList.length,
      totalConnections: 0,
      selectedPolicyCount: policyNodeList.filter((node) => node.isSelected).length,
      selectedDomainCount: domainNodeList.filter((node) => node.isSelected).length,
    };
  }

  const rowGap = 132;
  const chartWidth = (() => {
    const maxNodesInRow = Math.max(visiblePolicyNodes.length, visibleDomainNodes.length, 1);
    return Math.max(680, Math.min(1320, maxNodesInRow * 150 + 140));
  })();
  const chartHeight = Math.max(300, Math.min(460, rowGap + 190));
  const xPadding = 72;
  const policyY = chartHeight * 0.34;
  const domainY = chartHeight * 0.74;

  const activePolicyIds = new Set(
    [...filteredPolicyIds].filter((policyId) => {
      const policyNode = policyNodeList.find((entry) => entry.policyId === policyId);
      return policyNode !== undefined;
    }),
  );

  const visiblePolicyNodes = policyNodeList
    .filter((node) => activePolicyIds.has(node.policyId!))
    .sort((left, right) => right.contentCount - left.contentCount);
  const visibleDomainNodes = domainNodeList.sort((left, right) => right.contentCount - left.contentCount);
  const maxConnections = Math.max(
    1,
    ...visiblePolicyNodes.flatMap((policyNode) =>
      visibleDomainNodes.map((domainNode) =>
        edgeMap.get(`${policyNode.policyId}::${domainNode.domainId}`)?.contentCount || 0,
      ),
    ),
  );

  visiblePolicyNodes.forEach((node, index) => {
    const x =
      visiblePolicyNodes.length === 1
        ? chartWidth / 2
        : (index / (visiblePolicyNodes.length - 1)) * (chartWidth - xPadding * 2) + xPadding;

    node.x = x;
    node.y = policyY;
    node.r = Math.max(18, Math.min(38, (Math.sqrt(node.contentCount || 1) * 5) + 8));
    node.isHighlighted = selectedDomainId !== null && edgeMap.has(`${node.policyId}::${selectedDomainId}`);
    node.isSelected = selectedPolicyId === node.policyId;
  });

  visibleDomainNodes.forEach((node, index) => {
    const x =
      visibleDomainNodes.length === 1
        ? chartWidth / 2
        : (index / (visibleDomainNodes.length - 1)) * (chartWidth - xPadding * 2) + xPadding;

    node.x = x;
    node.y = domainY;
    node.r = Math.max(14, Math.min(32, (Math.sqrt(node.contentCount || 1) * 4.1) + 7));
    node.isHighlighted = selectedPolicyId !== null && edgeMap.has(`${selectedPolicyId}::${node.domainId}`);
    node.isSelected = selectedDomainId === node.domainId;
  });

  const links: OntologyNetworkLink[] = [];
  for (const edge of edgeMap.values()) {
    const source = visiblePolicyNodes.find((node) => node.policyId === edge.policyId);
    const target = visibleDomainNodes.find((node) => node.domainId === edge.domainId);
    if (!source || !target) {
      continue;
    }

    links.push({
      key: `${edge.policyId}::${edge.domainId}`,
      policyId: edge.policyId,
      domainId: edge.domainId,
      sourceX: source.x,
      sourceY: source.y + source.r,
      targetX: target.x,
      targetY: target.y - target.r,
      contentCount: edge.contentCount,
      evidenceCount: edge.evidenceCount,
      groupCount: edge.groupCount,
      isHighlighted:
        (selectedPolicyId !== null && selectedPolicyId === edge.policyId) ||
        (selectedDomainId !== null && selectedDomainId === edge.domainId),
    });
  }

  if (maxConnections > 1) {
    links.sort((left, right) => right.contentCount - left.contentCount);
  }

  return {
    policyNodes: visiblePolicyNodes,
    domainNodes: visibleDomainNodes,
    links: links.filter((link) => {
      const edge = edgeMap.get(`${link.policyId}::${link.domainId}`);
      return edge && edge.contentCount > 0;
    }),
    chartWidth,
    chartHeight,
    totalNodes: visiblePolicyNodes.length + visibleDomainNodes.length,
    totalConnections: links.length,
    selectedPolicyCount: visiblePolicyNodes.filter((node) => node.isSelected).length,
    selectedDomainCount: visibleDomainNodes.filter((node) => node.isSelected).length,
  };
}
