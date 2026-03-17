import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(scriptDir, "..");
const repoRoot = resolve(projectRoot, "..", "..", "..");

const RESOURCE_CATEGORY_LABELS = {
  technology: "기술",
  infrastructure_institutional: "인프라·제도",
  talent: "인재",
};

const RESOURCE_CATEGORY_ORDER = {
  technology: 1,
  infrastructure_institutional: 2,
  talent: 3,
};

const rawDatasetSourcePath = resolve(projectRoot, "..", "data-contracts", "sample-dashboard.json");
const rawDatasetTargetPath = resolve(projectRoot, "public", "data", "sample-dashboard.json");

const curatedPackSourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "curated_content_sample",
  "curated_content_sample_pack.json",
);
const curatedPackTargetPath = resolve(projectRoot, "public", "data", "curated-content-sample-pack.json");

const curatedSummarySourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "curated_content_sample",
  "curated_content_sample_summary.json",
);
const curatedSummaryTargetPath = resolve(projectRoot, "public", "data", "curated-content-sample-summary.json");

const technologyLensSourcePath = resolve(projectRoot, "..", "data-contracts", "technology-lens.json");
const technologyLensTargetPath = resolve(projectRoot, "public", "data", "technology-lens.json");

const curatedDisplayTextsSourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "curated_content_sample",
  "display_texts_curated_sample.csv",
);
const curatedGroupTaxonomyMapSourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "curated_content_sample",
  "policy_item_group_taxonomy_map_sample.csv",
);
const curatedMappingSupportTargetPath = resolve(projectRoot, "public", "data", "mapping-support.json");

const autoPolicyItemsSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "policy_items_auto.csv");
const autoStrategyMapSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "policy_item_strategy_map_auto.csv");
const autoTaxonomyMapSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "policy_item_taxonomy_map_auto.csv");
const autoEvidenceLinksSourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "policy_item_evidence_links_auto.csv",
);
const autoDisplayTextsSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "display_texts_auto.csv");
const autoSourceAssetsSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "source_assets_auto.csv");
const autoDerivedToSourceAssetMapSourcePath = resolve(
  repoRoot,
  "work",
  "04_ontology",
  "sample_build",
  "derived_to_source_asset_map_auto.csv",
);
const strategiesSeedSourcePath = resolve(repoRoot, "work", "04_ontology", "instances", "strategies_seed.csv");
const techDomainsSeedSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "tech_domains_seed.csv");
const techSubdomainsSeedSourcePath = resolve(repoRoot, "work", "04_ontology", "sample_build", "tech_subdomains_seed.csv");

const runtimePackTargetPath = resolve(projectRoot, "public", "data", "mapping-workbench-pack.json");
const runtimeSummaryTargetPath = resolve(projectRoot, "public", "data", "mapping-workbench-summary.json");
const runtimeSupportTargetPath = resolve(projectRoot, "public", "data", "mapping-workbench-support.json");

const assetTargetRoot = resolve(projectRoot, "public", "source-assets");

function sanitizeAssetPath(path) {
  if (!path || path.startsWith("http://") || path.startsWith("https://")) {
    return null;
  }

  return path.split("::")[0]?.replace(/^\.?\//, "") ?? null;
}

function copyJsonFile(sourcePath, targetPath) {
  mkdirSync(dirname(targetPath), { recursive: true });
  copyFileSync(sourcePath, targetPath);
}

function writeJsonFile(targetPath, value) {
  mkdirSync(dirname(targetPath), { recursive: true });
  writeFileSync(targetPath, `${JSON.stringify(value, null, 2)}\n`);
}

function parseCsv(text) {
  const normalizedText = text.replace(/^\uFEFF/, "");
  const rows = [];
  let currentRow = [];
  let currentValue = "";
  let isInsideQuotes = false;

  for (let index = 0; index < normalizedText.length; index += 1) {
    const character = normalizedText[index];
    const nextCharacter = normalizedText[index + 1];

    if (character === "\"") {
      if (isInsideQuotes && nextCharacter === "\"") {
        currentValue += "\"";
        index += 1;
        continue;
      }

      isInsideQuotes = !isInsideQuotes;
      continue;
    }

    if (character === "," && !isInsideQuotes) {
      currentRow.push(currentValue);
      currentValue = "";
      continue;
    }

    if ((character === "\n" || character === "\r") && !isInsideQuotes) {
      currentRow.push(currentValue);
      currentValue = "";

      if (currentRow.some((value) => value.length > 0)) {
        rows.push(currentRow);
      }

      currentRow = [];

      if (character === "\r" && nextCharacter === "\n") {
        index += 1;
      }

      continue;
    }

    currentValue += character;
  }

  currentRow.push(currentValue);
  if (currentRow.some((value) => value.length > 0)) {
    rows.push(currentRow);
  }

  const [headerRow = [], ...dataRows] = rows;

  return dataRows.map((row) =>
    Object.fromEntries(headerRow.map((header, index) => [header, row[index] ?? ""])),
  );
}

function parseCsvFile(sourcePath) {
  return parseCsv(readFileSync(sourcePath, "utf8"));
}

function normalizeReviewStatus(value) {
  return value === "reviewed" ? "reviewed" : "needs_review";
}

function toBooleanFlag(value) {
  return value === "1" || value === "true" || value === "yes";
}

function getOrCreateArray(map, key) {
  if (!map.has(key)) {
    map.set(key, []);
  }

  return map.get(key);
}

function pushToMapArray(map, key, value) {
  if (!key) {
    return;
  }

  getOrCreateArray(map, key).push(value);
}

function uniqueBy(items, getKey) {
  const seen = new Set();
  const deduped = [];

  for (const item of items) {
    const key = getKey(item);
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    deduped.push(item);
  }

  return deduped;
}

function buildLabelMap(rows, idKey, labelKey) {
  return new Map(
    rows
      .map((row) => [row[idKey], row[labelKey]])
      .filter(([id, label]) => Boolean(id) && Boolean(label)),
  );
}

function buildCuratedMappingSupport(displayTexts, groupTaxonomyMap) {
  const contentReviewStatusById = {};
  const groupReviewStatusById = {};
  const groupTechReviewStatusByKey = {};

  for (const row of displayTexts) {
    const targetObjectId = row.target_object_id;
    if (!targetObjectId) {
      continue;
    }

    const reviewStatus = normalizeReviewStatus(row.review_status);

    if (row.target_object_type === "policy_item_content") {
      contentReviewStatusById[targetObjectId] = reviewStatus;
    }

    if (row.target_object_type === "policy_item_group") {
      groupReviewStatusById[targetObjectId] = reviewStatus;
    }
  }

  for (const row of groupTaxonomyMap) {
    if (row.taxonomy_type !== "tech_domain" || !row.policy_item_group_id || !row.term_id) {
      continue;
    }

    groupTechReviewStatusByKey[`${row.policy_item_group_id}::${row.term_id}`] = normalizeReviewStatus(row.review_status);
  }

  return {
    content_review_status_by_id: contentReviewStatusById,
    group_review_status_by_id: groupReviewStatusById,
    group_tech_review_status_by_key: groupTechReviewStatusByKey,
  };
}

function normalizeProjectionReviewStatus(value, fallback = "needs_review") {
  const normalized = String(value ?? "").trim().toLowerCase();
  if (normalized === "reviewed" || normalized === "reviewed_manual" || normalized === "sample_curated") {
    return "reviewed";
  }

  return fallback;
}

function buildLensTaxonomyTerm(term, taxonomyType, isPrimary = false) {
  if (!term?.term_id || !term?.label) {
    return null;
  }

  return {
    taxonomy_type: taxonomyType,
    term_id: term.term_id,
    label: term.label,
    is_primary: isPrimary,
  };
}

function buildLensGroupTaxonomies(group) {
  const taxonomy = group.taxonomy ?? {};
  const terms = [
    buildLensTaxonomyTerm(taxonomy.primary_tech_domain, "tech_domain", true),
    ...(taxonomy.secondary_tech_domains ?? []).map((term) => buildLensTaxonomyTerm(term, "tech_domain", false)),
    buildLensTaxonomyTerm(taxonomy.primary_tech_subdomain, "tech_subdomain", true),
    ...(taxonomy.secondary_tech_subdomains ?? []).map((term) => buildLensTaxonomyTerm(term, "tech_subdomain", false)),
    ...((taxonomy.strategies ?? []).map((term) =>
      buildLensTaxonomyTerm(term, "strategy", Boolean(term.is_primary)),
    )),
  ].filter(Boolean);

  return uniqueBy(terms, (term) => `${term.taxonomy_type}::${term.term_id}`);
}

function normalizeLensSourceAsset(asset, derivedRepresentationId) {
  return {
    derived_representation_id: derivedRepresentationId,
    source_asset_id: asset.source_asset_id,
    asset_type: asset.asset_type,
    asset_path_or_url: asset.asset_path_or_url,
    page_no: asset.page_no || null,
    section_id: asset.section_id || null,
  };
}

function normalizeLensEvidence(group, content, evidence) {
  const sourcePolicyItemId =
    content.source_policy_item_id ||
    group.source_policy_item_id ||
    group.member_items?.find((member) => member.is_representative)?.policy_item_id ||
    group.member_items?.[0]?.policy_item_id ||
    "";
  const sourcePolicyItemLabel =
    group.member_items?.find((member) => member.policy_item_id === sourcePolicyItemId)?.item_label ||
    content.display?.title_text ||
    content.content_label ||
    group.display?.title_text ||
    group.group_label ||
    sourcePolicyItemId;

  return {
    source_policy_item_id: sourcePolicyItemId,
    source_policy_item_label: sourcePolicyItemLabel,
    derived_representation_id: evidence.derived_representation_id,
    source_object_type: evidence.source_object_type || "",
    source_object_id: evidence.source_object_id || evidence.derived_representation_id,
    representation_type: evidence.representation_type || "normalized_paragraph",
    document_id: evidence.document?.document_id || "",
    location_type: evidence.location_type || null,
    location_value: evidence.location_value || null,
    evidence_text: evidence.plain_text || content.content_statement || group.group_summary || "",
    evidence_label: evidence.link_role || evidence.evidence_strength || "",
    structured_payload_path: "",
    table_json_path: "",
    source_assets: uniqueBy(
      (evidence.source_assets ?? []).map((asset) => normalizeLensSourceAsset(asset, evidence.derived_representation_id)),
      (asset) => asset.source_asset_id,
    ),
  };
}

function buildRuntimeDashboardPackFromTechnologyLens(projection) {
  const runtimePolicies = new Map();
  const seenGroups = new Set();

  const techDomains = [...(projection.tech_domains ?? [])].sort(
    (left, right) => (left.display_order ?? 999) - (right.display_order ?? 999),
  );

  for (const techDomain of techDomains) {
    const groups = [...(techDomain.groups ?? [])].sort(
      (left, right) => (left.display_order ?? 999) - (right.display_order ?? 999),
    );

    for (const group of groups) {
      if (!group?.policy_item_group_id || seenGroups.has(group.policy_item_group_id)) {
        continue;
      }

      seenGroups.add(group.policy_item_group_id);

      const policyMeta = group.policy ?? {};
      const bucketMeta = group.bucket ?? {};
      if (!policyMeta.policy_id || !bucketMeta.policy_bucket_id) {
        continue;
      }

      const contentEntries = [...(group.contents ?? [])]
        .sort((left, right) => (left.display_order ?? 999) - (right.display_order ?? 999))
        .map((content) => ({
          policy_item_content_id: content.policy_item_content_id,
          content_label: content.display?.title_text || content.content_label || group.group_label || content.policy_item_content_id,
          content_statement: content.content_statement || content.display?.summary_text || "",
          content_summary: content.display?.summary_text || content.content_summary || content.content_statement || "",
          content_type: content.content_type || "policy_action",
          display_order: content.display_order ?? 999,
          evidence: (content.evidence ?? []).map((evidence) => normalizeLensEvidence(group, content, evidence)),
        }));
      const representativeEvidenceId =
        contentEntries[0]?.evidence[0]?.derived_representation_id ??
        group.contents?.[0]?.primary_policy_evidence?.derived_representation_id ??
        `DRV-LENS-${group.policy_item_group_id}`;
      const memberItems = (group.member_items ?? []).map((member, index) => ({
        policy_item_id: member.policy_item_id,
        item_label: member.item_label || group.group_label || member.policy_item_id,
        item_statement: member.item_statement || group.group_summary || "",
        member_role: member.member_role || (index === 0 ? "representative_item" : "member_item"),
        is_representative: Boolean(member.is_representative),
        derived_representation_id: representativeEvidenceId,
      }));

      let policyEntry = runtimePolicies.get(policyMeta.policy_id);
      if (!policyEntry) {
        policyEntry = {
          policy_id: policyMeta.policy_id,
          policy_name: policyMeta.policy_name,
          policy_order: policyMeta.policy_order ?? 999,
          buckets: new Map(),
        };
        runtimePolicies.set(policyMeta.policy_id, policyEntry);
      }

      let bucketEntry = policyEntry.buckets.get(bucketMeta.policy_bucket_id);
      if (!bucketEntry) {
        bucketEntry = {
          policy_bucket_id: bucketMeta.policy_bucket_id,
          resource_category_id: bucketMeta.resource_category_id,
          resource_category_label: bucketMeta.resource_category_label,
          bucket_display_order: bucketMeta.bucket_display_order ?? 999,
          groups: [],
        };
        policyEntry.buckets.set(bucketMeta.policy_bucket_id, bucketEntry);
      }

      bucketEntry.groups.push({
        policy_item_group_id: group.policy_item_group_id,
        group_label: group.display?.title_text || group.group_label || group.policy_item_group_id,
        group_summary: group.display?.summary_text || group.group_summary || "",
        group_description: group.display?.description_text || group.group_description || "",
        taxonomies: buildLensGroupTaxonomies(group),
        member_items: memberItems,
        contents: contentEntries,
      });
    }
  }

  const runtimePack = {
    sample_scope: {
      pack_id: "technology-lens-dashboard-v1",
      generated_from: "work/05_dashboard/data-contracts/technology-lens.json",
      purpose: "Technology-first dashboard pack with curated groups plus provisional fallback",
      policy_count: 0,
      group_count: 0,
      content_count: 0,
    },
    policies: [...runtimePolicies.values()]
      .sort((left, right) => left.policy_order - right.policy_order)
      .map((policy) => ({
        policy_id: policy.policy_id,
        policy_name: policy.policy_name,
        buckets: [...policy.buckets.values()]
          .sort((left, right) => left.bucket_display_order - right.bucket_display_order)
          .map((bucket) => ({
            policy_bucket_id: bucket.policy_bucket_id,
            resource_category_id: bucket.resource_category_id,
            resource_category_label: bucket.resource_category_label,
            groups: bucket.groups.sort((left, right) => {
              const leftOrder = left.contents[0]?.display_order ?? 999;
              const rightOrder = right.contents[0]?.display_order ?? 999;
              return leftOrder - rightOrder;
            }),
          })),
      })),
  };

  runtimePack.sample_scope.policy_count = runtimePack.policies.length;
  runtimePack.sample_scope.group_count = runtimePack.policies.reduce(
    (sum, policy) => sum + policy.buckets.reduce((bucketSum, bucket) => bucketSum + bucket.groups.length, 0),
    0,
  );
  runtimePack.sample_scope.content_count = runtimePack.policies.reduce(
    (sum, policy) =>
      sum +
      policy.buckets.reduce(
        (bucketSum, bucket) =>
          bucketSum + bucket.groups.reduce((groupSum, group) => groupSum + group.contents.length, 0),
        0,
      ),
    0,
  );

  return runtimePack;
}

function buildRuntimeMappingSupportFromTechnologyLens(projection) {
  const contentReviewStatusById = {};
  const groupReviewStatusById = {};
  const groupTechReviewStatusByKey = {};
  const seenGroups = new Set();

  for (const techDomain of projection.tech_domains ?? []) {
    for (const group of techDomain.groups ?? []) {
      if (!group?.policy_item_group_id || seenGroups.has(group.policy_item_group_id)) {
        continue;
      }

      seenGroups.add(group.policy_item_group_id);

      const defaultGroupStatus = group.group_status === "sample_curated" ? "reviewed" : "needs_review";
      groupReviewStatusById[group.policy_item_group_id] = defaultGroupStatus;

      for (const content of group.contents ?? []) {
        contentReviewStatusById[content.policy_item_content_id] =
          content.content_status === "sample_curated" ? "reviewed" : defaultGroupStatus;
      }

      const techTerms = [
        group.taxonomy?.primary_tech_domain,
        ...(group.taxonomy?.secondary_tech_domains ?? []),
      ].filter((term) => term?.term_id);

      for (const techTerm of techTerms) {
        groupTechReviewStatusByKey[`${group.policy_item_group_id}::${techTerm.term_id}`] = normalizeProjectionReviewStatus(
          techTerm.review_status,
          defaultGroupStatus,
        );
      }
    }
  }

  return {
    content_review_status_by_id: contentReviewStatusById,
    group_review_status_by_id: groupReviewStatusById,
    group_tech_review_status_by_key: groupTechReviewStatusByKey,
  };
}

function buildPolicyMetadata(rawDataset) {
  const policyById = new Map();
  const bucketById = new Map();

  rawDataset.policies.forEach((policy, policyIndex) => {
    policyById.set(policy.policy_id, {
      policy_id: policy.policy_id,
      policy_name: policy.policy_name,
      policy_order: policyIndex + 1,
    });

    for (const bucket of policy.buckets ?? []) {
      bucketById.set(bucket.policy_bucket_id, {
        policy_id: policy.policy_id,
        policy_name: policy.policy_name,
        policy_order: policyIndex + 1,
        policy_bucket_id: bucket.policy_bucket_id,
        resource_category_id: bucket.resource_category_id,
        resource_category_label: RESOURCE_CATEGORY_LABELS[bucket.resource_category_id] ?? bucket.resource_category_id,
      });
    }
  });

  return {
    policyById,
    bucketById,
  };
}

function runtimeGroupId(policyItemId) {
  return `PIG-AUTO-${policyItemId}`;
}

function runtimeContentId(policyItemId) {
  return `PIC-AUTO-${policyItemId}`;
}

function parseDocumentIdFromDerivedRepresentationId(derivedRepresentationId) {
  const match = String(derivedRepresentationId ?? "").match(/DOC-POL-\d{3}/);
  return match?.[0] ?? "";
}

function getRepresentationType(derivedRepresentationId) {
  if (derivedRepresentationId.startsWith("DRV-FIG-")) {
    return "figure_or_diagram";
  }

  if (derivedRepresentationId.startsWith("DRV-CTBL-")) {
    return "table";
  }

  return "paragraph";
}

function getSourceObjectType(derivedRepresentationId) {
  if (derivedRepresentationId.startsWith("DRV-FIG-")) {
    return "figure";
  }

  if (derivedRepresentationId.startsWith("DRV-CTBL-")) {
    return "table";
  }

  return "paragraph";
}

function normalizeSourceAsset(asset) {
  return {
    derived_representation_id: asset.derived_representation_id,
    source_asset_id: asset.source_asset_id,
    asset_type: asset.asset_type,
    asset_path_or_url: asset.asset_path_or_url,
    page_no: asset.page_no || null,
    section_id: asset.section_id || null,
  };
}

function getLocationMeta(sourceAssets) {
  const primaryAsset = sourceAssets.find((asset) => asset.page_no || asset.section_id) ?? sourceAssets[0] ?? null;
  if (!primaryAsset) {
    return {
      location_type: null,
      location_value: null,
    };
  }

  if (primaryAsset.page_no) {
    return {
      location_type: "page_no",
      location_value: primaryAsset.page_no,
    };
  }

  if (primaryAsset.section_id) {
    return {
      location_type: "section_id",
      location_value: primaryAsset.section_id,
    };
  }

  return {
    location_type: null,
    location_value: null,
  };
}

function sortRuntimePack(runtimePack) {
  runtimePack.policies.sort((left, right) => left.policy_id.localeCompare(right.policy_id, "en"));

  for (const policy of runtimePack.policies) {
    policy.buckets.sort(
      (left, right) =>
        (RESOURCE_CATEGORY_ORDER[left.resource_category_id] ?? 99) - (RESOURCE_CATEGORY_ORDER[right.resource_category_id] ?? 99),
    );

    for (const bucket of policy.buckets) {
      bucket.groups.sort((left, right) => {
        const leftOrder = left.contents[0]?.display_order ?? 9999;
        const rightOrder = right.contents[0]?.display_order ?? 9999;
        return leftOrder - rightOrder;
      });
    }
  }

  return runtimePack;
}

function buildRuntimeDashboardPack({
  rawDataset,
  policyItems,
  strategyMapRows,
  taxonomyMapRows,
  evidenceLinkRows,
  displayTextRows,
  sourceAssetRows,
  derivedToSourceAssetRows,
  strategyLabelMap,
  techDomainLabelMap,
  techSubdomainLabelMap,
}) {
  const { policyById, bucketById } = buildPolicyMetadata(rawDataset);
  const displayByItemId = new Map(
    displayTextRows
      .filter((row) => row.target_object_type === "policy_item" && row.target_object_id)
      .map((row) => [row.target_object_id, row]),
  );
  const strategyRowsByItemId = new Map();
  const taxonomyRowsByItemId = new Map();
  const evidenceRowsByItemId = new Map();
  const sourceAssetById = new Map(sourceAssetRows.map((row) => [row.source_asset_id, row]));
  const sourceAssetsByDerivedRepresentationId = new Map();
  const bucketDisplayOrders = new Map();

  for (const row of strategyMapRows) {
    pushToMapArray(strategyRowsByItemId, row.policy_item_id, row);
  }

  for (const row of taxonomyMapRows) {
    pushToMapArray(taxonomyRowsByItemId, row.policy_item_id, row);
  }

  for (const row of evidenceLinkRows) {
    pushToMapArray(evidenceRowsByItemId, row.policy_item_id, row);
  }

  for (const row of derivedToSourceAssetRows) {
    const sourceAsset = sourceAssetById.get(row.source_asset_id);
    if (!sourceAsset || !row.derived_representation_id) {
      continue;
    }

    pushToMapArray(sourceAssetsByDerivedRepresentationId, row.derived_representation_id, {
      ...sourceAsset,
      derived_representation_id: row.derived_representation_id,
    });
  }

  const runtimePolicies = new Map();

  for (const item of policyItems) {
    const bucketMeta = bucketById.get(item.policy_bucket_id);
    if (!bucketMeta) {
      continue;
    }

    const policyMeta = policyById.get(bucketMeta.policy_id);
    if (!policyMeta) {
      continue;
    }

    const policyEntry =
      runtimePolicies.get(policyMeta.policy_id) ??
      {
        policy_id: policyMeta.policy_id,
        policy_name: policyMeta.policy_name,
        policy_order: policyMeta.policy_order,
        buckets: [],
      };
    runtimePolicies.set(policyMeta.policy_id, policyEntry);

    let bucketEntry = policyEntry.buckets.find((bucket) => bucket.policy_bucket_id === bucketMeta.policy_bucket_id);
    if (!bucketEntry) {
      bucketEntry = {
        policy_bucket_id: bucketMeta.policy_bucket_id,
        resource_category_id: bucketMeta.resource_category_id,
        resource_category_label: bucketMeta.resource_category_label,
        groups: [],
      };
      policyEntry.buckets.push(bucketEntry);
    }

    const displayOrder = (bucketDisplayOrders.get(bucketMeta.policy_bucket_id) ?? 0) + 1;
    bucketDisplayOrders.set(bucketMeta.policy_bucket_id, displayOrder);

    const display = displayByItemId.get(item.policy_item_id) ?? null;
    const strategyTerms = (strategyRowsByItemId.get(item.policy_item_id) ?? []).map((row) => ({
      taxonomy_type: "strategy",
      term_id: row.term_id,
      label: strategyLabelMap.get(row.term_id) ?? row.term_id,
      is_primary: toBooleanFlag(row.is_primary),
    }));
    const taxonomyRows = taxonomyRowsByItemId.get(item.policy_item_id) ?? [];
    const techTerms = taxonomyRows
      .filter((row) => row.taxonomy_type === "tech_domain")
      .map((row) => ({
        taxonomy_type: "tech_domain",
        term_id: row.term_id,
        label: techDomainLabelMap.get(row.term_id) ?? row.term_id,
        is_primary: toBooleanFlag(row.is_primary),
      }));
    const techSubterms = taxonomyRows
      .filter((row) => row.taxonomy_type === "tech_subdomain")
      .map((row) => ({
        taxonomy_type: "tech_subdomain",
        term_id: row.term_id,
        label: techSubdomainLabelMap.get(row.term_id) ?? row.term_id,
        is_primary: toBooleanFlag(row.is_primary),
      }));
    const evidence = (evidenceRowsByItemId.get(item.policy_item_id) ?? []).map((row) => {
      const sourceAssets = uniqueBy(
        (sourceAssetsByDerivedRepresentationId.get(row.derived_representation_id) ?? []).map(normalizeSourceAsset),
        (asset) => asset.source_asset_id,
      );
      const location = getLocationMeta(sourceAssets);
      const documentId =
        sourceAssets[0]?.source_asset_id?.startsWith("SRC-")
          ? sourceAssets[0].source_asset_id.split("-").slice(1, 4).join("-")
          : parseDocumentIdFromDerivedRepresentationId(row.derived_representation_id);

      return {
        source_policy_item_id: item.policy_item_id,
        source_policy_item_label: display?.title_text || item.item_label || item.policy_item_id,
        derived_representation_id: row.derived_representation_id,
        source_object_type: getSourceObjectType(row.derived_representation_id),
        source_object_id: row.derived_representation_id,
        representation_type: getRepresentationType(row.derived_representation_id),
        document_id: documentId,
        location_type: location.location_type,
        location_value: location.location_value,
        evidence_text: item.item_statement || display?.summary_text || item.item_description || item.item_label || "",
        evidence_label: row.link_role || row.evidence_strength || "primary_support",
        structured_payload_path: "",
        table_json_path: "",
        source_assets: sourceAssets,
      };
    });

    bucketEntry.groups.push({
      policy_item_group_id: runtimeGroupId(item.policy_item_id),
      group_label: display?.title_text || item.item_label || item.policy_item_id,
      group_summary: display?.summary_text || item.item_statement || item.item_description || "",
      group_description: display?.description_text || item.item_description || item.item_statement || "",
      taxonomies: [...strategyTerms, ...techTerms, ...techSubterms],
      member_items: [
        {
          policy_item_id: item.policy_item_id,
          item_label: item.item_label || display?.title_text || item.policy_item_id,
          item_statement: item.item_statement || display?.summary_text || "",
          member_role: item.item_status || "auto_candidate",
          is_representative: true,
          derived_representation_id: evidence[0]?.derived_representation_id ?? `DRV-AUTO-${item.policy_item_id}`,
        },
      ],
      contents: [
        {
          policy_item_content_id: runtimeContentId(item.policy_item_id),
          content_label: display?.title_text || item.item_label || item.policy_item_id,
          content_statement: item.item_statement || display?.summary_text || "",
          content_summary: display?.summary_text || item.item_description || item.item_statement || "",
          content_type: item.item_status || "auto_candidate",
          display_order: displayOrder,
          evidence,
        },
      ],
    });
  }

  const runtimePack = {
    sample_scope: {
      pack_id: "mapping-workbench-auto-v1",
      generated_from: "work/04_ontology/sample_build/*_auto.csv",
      purpose: "Broader runtime pack for the mapping-first dashboard",
      policy_count: 0,
      group_count: 0,
      content_count: 0,
    },
    policies: [...runtimePolicies.values()].map((policy) => ({
      policy_id: policy.policy_id,
      policy_name: policy.policy_name,
      buckets: policy.buckets,
    })),
  };

  sortRuntimePack(runtimePack);

  runtimePack.sample_scope.policy_count = runtimePack.policies.length;
  runtimePack.sample_scope.group_count = runtimePack.policies.reduce(
    (sum, policy) => sum + policy.buckets.reduce((bucketSum, bucket) => bucketSum + bucket.groups.length, 0),
    0,
  );
  runtimePack.sample_scope.content_count = runtimePack.policies.reduce(
    (sum, policy) =>
      sum +
      policy.buckets.reduce(
        (bucketSum, bucket) =>
          bucketSum + bucket.groups.reduce((groupSum, group) => groupSum + group.contents.length, 0),
        0,
      ),
    0,
  );

  return runtimePack;
}

function buildRuntimeDashboardSummary(runtimePack, displayTextCount) {
  const stats = {
    policy_count: runtimePack.policies.length,
    group_count: 0,
    content_count: 0,
    group_member_count: 0,
    content_evidence_count: 0,
    group_taxonomy_count: 0,
    display_text_count: displayTextCount,
    policies: [],
  };

  for (const policy of runtimePack.policies) {
    let bucketCount = 0;

    for (const bucket of policy.buckets) {
      bucketCount += 1;
      stats.group_count += bucket.groups.length;

      for (const group of bucket.groups) {
        stats.group_member_count += group.member_items.length;
        stats.group_taxonomy_count += group.taxonomies.length;
        stats.content_count += group.contents.length;

        for (const content of group.contents) {
          stats.content_evidence_count += content.evidence.length;
        }
      }
    }

    stats.policies.push({
      policy_id: policy.policy_id,
      policy_name: policy.policy_name,
      bucket_count: bucketCount,
    });
  }

  return stats;
}

function buildRuntimeMappingSupport(policyItems, displayTextRows, taxonomyMapRows) {
  const displayByItemId = new Map(
    displayTextRows
      .filter((row) => row.target_object_type === "policy_item" && row.target_object_id)
      .map((row) => [row.target_object_id, row]),
  );
  const groupTechReviewStatusByKey = {};
  const contentReviewStatusById = {};
  const groupReviewStatusById = {};

  for (const item of policyItems) {
    const reviewStatus = normalizeReviewStatus(displayByItemId.get(item.policy_item_id)?.review_status);
    contentReviewStatusById[runtimeContentId(item.policy_item_id)] = reviewStatus;
    groupReviewStatusById[runtimeGroupId(item.policy_item_id)] = reviewStatus;
  }

  for (const row of taxonomyMapRows) {
    if (row.taxonomy_type !== "tech_domain" || !row.policy_item_id || !row.term_id) {
      continue;
    }

    groupTechReviewStatusByKey[`${runtimeGroupId(row.policy_item_id)}::${row.term_id}`] = normalizeReviewStatus(row.review_status);
  }

  return {
    content_review_status_by_id: contentReviewStatusById,
    group_review_status_by_id: groupReviewStatusById,
    group_tech_review_status_by_key: groupTechReviewStatusByKey,
  };
}

function collectRawDatasetAssets(dataset, targetSet) {
  for (const policy of dataset.policies ?? []) {
    for (const bucket of policy.buckets ?? []) {
      for (const item of bucket.items ?? []) {
        for (const evidence of item.evidence ?? []) {
          const sanitizedPath = sanitizeAssetPath(evidence.asset_path_or_url);
          if (sanitizedPath) {
            targetSet.add(sanitizedPath);
          }
        }
      }
    }
  }
}

function collectPackAssets(dataset, targetSet) {
  for (const policy of dataset.policies ?? []) {
    for (const bucket of policy.buckets ?? []) {
      for (const group of bucket.groups ?? []) {
        for (const content of group.contents ?? []) {
          for (const evidence of content.evidence ?? []) {
            for (const sourceAsset of evidence.source_assets ?? []) {
              const sanitizedPath = sanitizeAssetPath(sourceAsset.asset_path_or_url);
              if (sanitizedPath) {
                targetSet.add(sanitizedPath);
              }
            }
          }
        }
      }
    }
  }
}

copyJsonFile(rawDatasetSourcePath, rawDatasetTargetPath);
copyJsonFile(curatedPackSourcePath, curatedPackTargetPath);
copyJsonFile(curatedSummarySourcePath, curatedSummaryTargetPath);
copyJsonFile(technologyLensSourcePath, technologyLensTargetPath);

const rawDataset = JSON.parse(readFileSync(rawDatasetSourcePath, "utf8"));
const curatedPack = JSON.parse(readFileSync(curatedPackSourcePath, "utf8"));
const technologyLens = JSON.parse(readFileSync(technologyLensSourcePath, "utf8"));

const curatedDisplayTexts = parseCsvFile(curatedDisplayTextsSourcePath);
const curatedGroupTaxonomyMap = parseCsvFile(curatedGroupTaxonomyMapSourcePath);
const curatedMappingSupport = buildCuratedMappingSupport(curatedDisplayTexts, curatedGroupTaxonomyMap);
writeJsonFile(curatedMappingSupportTargetPath, curatedMappingSupport);

const runtimePack = buildRuntimeDashboardPackFromTechnologyLens(technologyLens);
const runtimeSummary = buildRuntimeDashboardSummary(runtimePack, 0);
const runtimeMappingSupport = buildRuntimeMappingSupportFromTechnologyLens(technologyLens);

writeJsonFile(runtimePackTargetPath, runtimePack);
writeJsonFile(runtimeSummaryTargetPath, runtimeSummary);
writeJsonFile(runtimeSupportTargetPath, runtimeMappingSupport);

const assetPaths = new Set();
collectRawDatasetAssets(rawDataset, assetPaths);
collectPackAssets(curatedPack, assetPaths);
collectPackAssets(runtimePack, assetPaths);

let copiedAssetCount = 0;
let missingAssetCount = 0;

for (const assetPath of assetPaths) {
  const sourceAssetPath = resolve(repoRoot, assetPath);
  if (!existsSync(sourceAssetPath)) {
    missingAssetCount += 1;
    continue;
  }

  const targetAssetPath = resolve(assetTargetRoot, assetPath);
  mkdirSync(dirname(targetAssetPath), { recursive: true });
  copyFileSync(sourceAssetPath, targetAssetPath);
  copiedAssetCount += 1;
}

console.log(`Copied raw dashboard dataset to ${rawDatasetTargetPath}`);
console.log(`Copied curated pack to ${curatedPackTargetPath}`);
console.log(`Copied curated summary to ${curatedSummaryTargetPath}`);
console.log(`Copied technology lens projection to ${technologyLensTargetPath}`);
console.log(`Generated curated mapping support to ${curatedMappingSupportTargetPath}`);
console.log(`Generated runtime pack to ${runtimePackTargetPath}`);
console.log(`Generated runtime summary to ${runtimeSummaryTargetPath}`);
console.log(`Generated runtime mapping support to ${runtimeSupportTargetPath}`);
console.log(`Copied ${copiedAssetCount} source assets to ${assetTargetRoot}`);

if (missingAssetCount > 0) {
  console.log(`Skipped ${missingAssetCount} missing source assets`);
}
