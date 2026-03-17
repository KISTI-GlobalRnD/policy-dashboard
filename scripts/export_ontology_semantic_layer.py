#!/usr/bin/env python3
"""Export the relational ontology store to JSON-LD and Turtle."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote


BASE = "https://example.org/kr-msit-policy"
ONTOLOGY = f"{BASE}/ontology#"
RESOURCE = f"{BASE}/resource"


def resource_iri(kind: str, object_id: str) -> str:
    return f"{RESOURCE}/{kind}/{quote(object_id)}"


def literal(value: object) -> str:
    text = str(value)
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f"\"{escaped}\""


def iri_line(predicate: str, iri: str) -> str:
    return f"  {predicate} <{iri}> ;"


def lit_line(predicate: str, value: object) -> str:
    return f"  {predicate} {literal(value)} ;"


def append_block(lines: list[str], subject: str, statements: list[str]) -> None:
    if not statements:
        return
    lines.append(f"<{subject}>")
    trimmed = statements[:-1] + [statements[-1].rstrip(" ;") + " ."]
    lines.extend(trimmed)
    lines.append("")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-jsonld", required=True)
    parser.add_argument("--out-turtle", required=True)
    args = parser.parse_args()

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        policies = connection.execute("SELECT * FROM policies ORDER BY policy_order").fetchall()
        documents = connection.execute("SELECT * FROM documents ORDER BY document_id").fetchall()
        resource_categories = connection.execute("SELECT * FROM resource_categories ORDER BY display_order").fetchall()
        policy_buckets = connection.execute("SELECT * FROM policy_buckets ORDER BY policy_id, display_order").fetchall()
        strategies = connection.execute("SELECT * FROM strategies ORDER BY display_order").fetchall()
        policy_items = connection.execute("SELECT * FROM policy_items ORDER BY policy_item_id").fetchall()
        display_texts = connection.execute("SELECT * FROM display_texts ORDER BY display_text_id").fetchall()
        derived_reps = connection.execute("SELECT * FROM derived_representations ORDER BY derived_representation_id").fetchall()
        source_assets = connection.execute("SELECT * FROM source_assets ORDER BY source_asset_id").fetchall()
        evidence_paragraphs = connection.execute("SELECT * FROM evidence_paragraphs ORDER BY evidence_paragraph_id").fetchall()
        evidence_tables = connection.execute("SELECT * FROM evidence_tables ORDER BY evidence_table_id").fetchall()
        evidence_figures = connection.execute("SELECT * FROM evidence_figures ORDER BY evidence_figure_id").fetchall()
        policy_item_groups = connection.execute("SELECT * FROM policy_item_groups ORDER BY policy_item_group_id").fetchall()
        policy_item_group_members = connection.execute(
            "SELECT * FROM policy_item_group_members ORDER BY policy_item_group_id, is_representative DESC, policy_item_id"
        ).fetchall()
        policy_item_group_taxonomy_map = connection.execute(
            "SELECT * FROM policy_item_group_taxonomy_map ORDER BY policy_item_group_id, taxonomy_type, is_primary DESC"
        ).fetchall()
        policy_item_contents = connection.execute(
            "SELECT * FROM policy_item_contents ORDER BY policy_item_group_id, display_order, policy_item_content_id"
        ).fetchall()
        policy_item_content_evidence_links = connection.execute(
            "SELECT * FROM policy_item_content_evidence_links ORDER BY policy_item_content_id, sort_order"
        ).fetchall()
        tech_domains = connection.execute("SELECT * FROM tech_domains ORDER BY display_order").fetchall()
        tech_subdomains = connection.execute("SELECT * FROM tech_subdomains ORDER BY tech_domain_id, display_order").fetchall()
        policy_item_links = connection.execute("SELECT * FROM policy_item_evidence_links ORDER BY policy_item_id, sort_order").fetchall()
        derived_source_map = connection.execute("SELECT * FROM derived_to_source_asset_map ORDER BY derived_representation_id").fetchall()
        derived_display_map = connection.execute("SELECT * FROM derived_to_display_map ORDER BY derived_representation_id").fetchall()
        policy_item_taxonomy_map = connection.execute("SELECT * FROM policy_item_taxonomy_map ORDER BY policy_item_id, taxonomy_type, is_primary DESC").fetchall()
    finally:
        connection.close()

    document_iri_map = {row["document_id"]: resource_iri("document", row["document_id"]) for row in documents}
    policy_iri_map = {row["policy_id"]: resource_iri("policy", row["policy_id"]) for row in policies}
    bucket_iri_map = {row["policy_bucket_id"]: resource_iri("bucket", row["policy_bucket_id"]) for row in policy_buckets}
    item_iri_map = {row["policy_item_id"]: resource_iri("policy-item", row["policy_item_id"]) for row in policy_items}
    group_iri_map = {row["policy_item_group_id"]: resource_iri("policy-item-group", row["policy_item_group_id"]) for row in policy_item_groups}
    content_iri_map = {row["policy_item_content_id"]: resource_iri("policy-item-content", row["policy_item_content_id"]) for row in policy_item_contents}
    display_iri_map = {row["display_text_id"]: resource_iri("display-text", row["display_text_id"]) for row in display_texts}
    rep_iri_map = {row["derived_representation_id"]: resource_iri("derived-representation", row["derived_representation_id"]) for row in derived_reps}
    asset_iri_map = {row["source_asset_id"]: resource_iri("source-asset", row["source_asset_id"]) for row in source_assets}
    rc_iri_map = {row["resource_category_id"]: resource_iri("resource-category", row["resource_category_id"]) for row in resource_categories}
    strategy_iri_map = {row["strategy_id"]: resource_iri("strategy", row["strategy_id"]) for row in strategies}
    td_iri_map = {row["tech_domain_id"]: resource_iri("tech-domain", row["tech_domain_id"]) for row in tech_domains}
    ts_iri_map = {row["tech_subdomain_id"]: resource_iri("tech-subdomain", row["tech_subdomain_id"]) for row in tech_subdomains}
    paragraph_iri_map = {row["evidence_paragraph_id"]: resource_iri("evidence-paragraph", row["evidence_paragraph_id"]) for row in evidence_paragraphs}
    table_iri_map = {row["evidence_table_id"]: resource_iri("evidence-table", row["evidence_table_id"]) for row in evidence_tables}
    figure_iri_map = {row["evidence_figure_id"]: resource_iri("evidence-figure", row["evidence_figure_id"]) for row in evidence_figures}

    context = {
        "po": ONTOLOGY,
        "dct": "http://purl.org/dc/terms/",
        "prov": "http://www.w3.org/ns/prov#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "identifier": "dct:identifier",
        "title": "dct:title",
        "label": "skos:prefLabel",
        "broader": {"@id": "skos:broader", "@type": "@id"},
        "inScheme": {"@id": "skos:inScheme", "@type": "@id"},
        "hasDocument": {"@id": "po:hasDocument", "@type": "@id"},
        "forPolicy": {"@id": "po:forPolicy", "@type": "@id"},
        "hasBucket": {"@id": "po:hasBucket", "@type": "@id"},
        "belongsToPolicy": {"@id": "po:belongsToPolicy", "@type": "@id"},
        "hasResourceCategory": {"@id": "po:hasResourceCategory", "@type": "@id"},
        "hasPolicyItem": {"@id": "po:hasPolicyItem", "@type": "@id"},
        "hasPolicyItemGroup": {"@id": "po:hasPolicyItemGroup", "@type": "@id"},
        "belongsToBucket": {"@id": "po:belongsToBucket", "@type": "@id"},
        "belongsToPolicyBucket": {"@id": "po:belongsToPolicyBucket", "@type": "@id"},
        "hasPolicyItemContent": {"@id": "po:hasPolicyItemContent", "@type": "@id"},
        "belongsToPolicyItemGroup": {"@id": "po:belongsToPolicyItemGroup", "@type": "@id"},
        "groupsPolicyItem": {"@id": "po:groupsPolicyItem", "@type": "@id"},
        "groupedInPolicyItemGroup": {"@id": "po:groupedInPolicyItemGroup", "@type": "@id"},
        "primaryDocument": {"@id": "po:primaryDocument", "@type": "@id"},
        "hasEvidence": {"@id": "po:hasEvidence", "@type": "@id"},
        "hasContentEvidence": {"@id": "po:hasContentEvidence", "@type": "@id"},
        "hasDisplayText": {"@id": "po:hasDisplayText", "@type": "@id"},
        "hasGroupDisplayText": {"@id": "po:hasGroupDisplayText", "@type": "@id"},
        "hasContentDisplayText": {"@id": "po:hasContentDisplayText", "@type": "@id"},
        "representsEvidenceObject": {"@id": "po:representsEvidenceObject", "@type": "@id"},
        "displayFor": {"@id": "po:displayFor", "@type": "@id"},
        "wasDerivedFrom": {"@id": "prov:wasDerivedFrom", "@type": "@id"},
        "hasStrategy": {"@id": "po:hasStrategy", "@type": "@id"},
        "hasTechDomain": {"@id": "po:hasTechDomain", "@type": "@id"},
        "hasTechSubdomain": {"@id": "po:hasTechSubdomain", "@type": "@id"},
        "hasRepresentativeStrategy": {"@id": "po:hasRepresentativeStrategy", "@type": "@id"},
        "hasRepresentativeTechDomain": {"@id": "po:hasRepresentativeTechDomain", "@type": "@id"},
        "hasRepresentativeTechSubdomain": {"@id": "po:hasRepresentativeTechSubdomain", "@type": "@id"},
        "policyStatus": "po:policyStatus",
        "bucketStatus": "po:bucketStatus",
        "itemStatus": "po:itemStatus",
        "groupStatus": "po:groupStatus",
        "contentStatus": "po:contentStatus",
        "contentType": "po:contentType",
        "statementText": "po:statementText",
        "contentStatementText": "po:contentStatementText",
        "summaryText": "po:summaryText",
        "descriptionText": "po:descriptionText",
        "displayRole": "po:displayRole",
        "representationType": "po:representationType",
        "locationType": "po:locationType",
        "locationValue": "po:locationValue",
        "assetPathOrUrl": "po:assetPathOrUrl",
        "pageNo": "po:pageNo",
        "sectionId": "po:sectionId",
    }

    graph: list[dict] = []

    resource_scheme_iri = resource_iri("scheme", "resource-categories")
    strategy_scheme_iri = resource_iri("scheme", "strategies")
    tech_domain_scheme_iri = resource_iri("scheme", "tech-domains")
    tech_subdomain_scheme_iri = resource_iri("scheme", "tech-subdomains")

    graph.extend(
        [
            {"@id": resource_scheme_iri, "@type": "skos:ConceptScheme", "label": "Resource Categories"},
            {"@id": strategy_scheme_iri, "@type": "skos:ConceptScheme", "label": "Strategies"},
            {"@id": tech_domain_scheme_iri, "@type": "skos:ConceptScheme", "label": "Technology Domains"},
            {"@id": tech_subdomain_scheme_iri, "@type": "skos:ConceptScheme", "label": "Technology Subdomains"},
        ]
    )

    for row in resource_categories:
        graph.append(
            {
                "@id": rc_iri_map[row["resource_category_id"]],
                "@type": ["po:ResourceCategory", "skos:Concept"],
                "identifier": row["resource_category_id"],
                "label": row["display_label"],
                "descriptionText": row["description"],
                "inScheme": resource_scheme_iri,
            }
        )

    for row in strategies:
        graph.append(
            {
                "@id": strategy_iri_map[row["strategy_id"]],
                "@type": ["po:Strategy", "skos:Concept"],
                "identifier": row["strategy_id"],
                "label": row["strategy_label"],
                "descriptionText": row["strategy_description"],
                "inScheme": strategy_scheme_iri,
            }
        )

    for row in tech_domains:
        graph.append(
            {
                "@id": td_iri_map[row["tech_domain_id"]],
                "@type": ["po:TechnologyDomain", "skos:Concept"],
                "identifier": row["tech_domain_id"],
                "label": row["tech_domain_label"],
                "inScheme": tech_domain_scheme_iri,
            }
        )

    for row in tech_subdomains:
        graph.append(
            {
                "@id": ts_iri_map[row["tech_subdomain_id"]],
                "@type": ["po:TechnologySubdomain", "skos:Concept"],
                "identifier": row["tech_subdomain_id"],
                "label": row["tech_subdomain_label"],
                "inScheme": tech_subdomain_scheme_iri,
                "broader": td_iri_map[row["tech_domain_id"]],
            }
        )

    documents_by_policy: dict[str, list[str]] = {}
    for row in documents:
        iri = document_iri_map[row["document_id"]]
        if row["policy_id"]:
            documents_by_policy.setdefault(row["policy_id"], []).append(iri)
        document_graph = {
            "@id": iri,
            "@type": "po:PolicyDocument",
            "identifier": row["document_id"],
            "title": row["normalized_title"],
            "descriptionText": row["notes"],
            "locationValue": row["location_granularity"],
        }
        if row["policy_id"]:
            document_graph["forPolicy"] = policy_iri_map[row["policy_id"]]
        graph.append(document_graph)

    items_by_bucket: dict[str, list[str]] = {}
    for row in policy_items:
        items_by_bucket.setdefault(row["policy_bucket_id"], []).append(item_iri_map[row["policy_item_id"]])

    groups_by_bucket: dict[str, list[str]] = {}
    for row in policy_item_groups:
        groups_by_bucket.setdefault(row["policy_bucket_id"], []).append(group_iri_map[row["policy_item_group_id"]])

    buckets_by_policy: dict[str, list[str]] = {}
    for row in policy_buckets:
        iri = bucket_iri_map[row["policy_bucket_id"]]
        buckets_by_policy.setdefault(row["policy_id"], []).append(iri)
        graph.append(
            {
                "@id": iri,
                "@type": "po:PolicyBucket",
                "identifier": row["policy_bucket_id"],
                "belongsToPolicy": policy_iri_map[row["policy_id"]],
                "hasResourceCategory": rc_iri_map[row["resource_category_id"]],
                "hasPolicyItem": items_by_bucket.get(row["policy_bucket_id"], []),
                "hasPolicyItemGroup": groups_by_bucket.get(row["policy_bucket_id"], []),
                "bucketStatus": row["bucket_status"],
                "summaryText": row["bucket_summary"],
            }
        )

    item_links_by_item: dict[str, list[str]] = {}
    for row in policy_item_links:
        item_links_by_item.setdefault(row["policy_item_id"], []).append(rep_iri_map[row["derived_representation_id"]])

    items_by_group: dict[str, list[str]] = {}
    groups_by_item: dict[str, list[str]] = {}
    for row in policy_item_group_members:
        group_iri = group_iri_map[row["policy_item_group_id"]]
        item_iri = item_iri_map[row["policy_item_id"]]
        items_by_group.setdefault(row["policy_item_group_id"], []).append(item_iri)
        groups_by_item.setdefault(row["policy_item_id"], []).append(group_iri)

    contents_by_group: dict[str, list[str]] = {}
    for row in policy_item_contents:
        contents_by_group.setdefault(row["policy_item_group_id"], []).append(content_iri_map[row["policy_item_content_id"]])

    content_evidence_by_content: dict[str, list[str]] = {}
    for row in policy_item_content_evidence_links:
        content_evidence_by_content.setdefault(row["policy_item_content_id"], []).append(rep_iri_map[row["derived_representation_id"]])

    display_by_item: dict[str, list[str]] = {}
    display_by_group: dict[str, list[str]] = {}
    display_by_content: dict[str, list[str]] = {}
    for row in display_texts:
        if row["target_object_type"] == "policy_item":
            display_by_item.setdefault(row["target_object_id"], []).append(display_iri_map[row["display_text_id"]])
        elif row["target_object_type"] == "policy_item_group":
            display_by_group.setdefault(row["target_object_id"], []).append(display_iri_map[row["display_text_id"]])
        elif row["target_object_type"] == "policy_item_content":
            display_by_content.setdefault(row["target_object_id"], []).append(display_iri_map[row["display_text_id"]])

    strategies_by_item: dict[str, list[str]] = {}
    tech_domains_by_item: dict[str, list[str]] = {}
    tech_subdomains_by_item: dict[str, list[str]] = {}
    for row in policy_item_taxonomy_map:
        if row["taxonomy_type"] == "strategy":
            strategies_by_item.setdefault(row["policy_item_id"], []).append(strategy_iri_map[row["term_id"]])
        elif row["taxonomy_type"] == "tech_domain":
            tech_domains_by_item.setdefault(row["policy_item_id"], []).append(td_iri_map[row["term_id"]])
        elif row["taxonomy_type"] == "tech_subdomain":
            tech_subdomains_by_item.setdefault(row["policy_item_id"], []).append(ts_iri_map[row["term_id"]])

    strategies_by_group: dict[str, list[str]] = {}
    tech_domains_by_group: dict[str, list[str]] = {}
    tech_subdomains_by_group: dict[str, list[str]] = {}
    for row in policy_item_group_taxonomy_map:
        if row["taxonomy_type"] == "strategy":
            strategies_by_group.setdefault(row["policy_item_group_id"], []).append(strategy_iri_map[row["term_id"]])
        elif row["taxonomy_type"] == "tech_domain":
            tech_domains_by_group.setdefault(row["policy_item_group_id"], []).append(td_iri_map[row["term_id"]])
        elif row["taxonomy_type"] == "tech_subdomain":
            tech_subdomains_by_group.setdefault(row["policy_item_group_id"], []).append(ts_iri_map[row["term_id"]])

    for row in policies:
        policy_graph = {
            "@id": policy_iri_map[row["policy_id"]],
            "@type": "po:Policy",
            "identifier": row["policy_id"],
            "label": row["policy_name"],
            "policyStatus": row["policy_status"],
            "hasDocument": documents_by_policy.get(row["policy_id"], []),
            "hasBucket": buckets_by_policy.get(row["policy_id"], []),
        }
        if row["primary_document_id"]:
            policy_graph["primaryDocument"] = document_iri_map.get(row["primary_document_id"])
        graph.append(policy_graph)

    for row in policy_items:
        graph.append(
            {
                "@id": item_iri_map[row["policy_item_id"]],
                "@type": "po:PolicyItem",
                "identifier": row["policy_item_id"],
                "label": row["item_label"],
                "statementText": row["item_statement"],
                "descriptionText": row["item_description"],
                "itemStatus": row["item_status"],
                "belongsToBucket": bucket_iri_map[row["policy_bucket_id"]],
                "groupedInPolicyItemGroup": groups_by_item.get(row["policy_item_id"], []),
                "hasEvidence": item_links_by_item.get(row["policy_item_id"], []),
                "hasDisplayText": display_by_item.get(row["policy_item_id"], []),
                "hasStrategy": strategies_by_item.get(row["policy_item_id"], []),
                "hasTechDomain": tech_domains_by_item.get(row["policy_item_id"], []),
                "hasTechSubdomain": tech_subdomains_by_item.get(row["policy_item_id"], []),
            }
        )

    for row in policy_item_groups:
        graph.append(
            {
                "@id": group_iri_map[row["policy_item_group_id"]],
                "@type": "po:PolicyItemGroup",
                "identifier": row["policy_item_group_id"],
                "label": row["group_label"],
                "summaryText": row["group_summary"],
                "descriptionText": row["group_description"],
                "groupStatus": row["group_status"],
                "belongsToPolicyBucket": bucket_iri_map[row["policy_bucket_id"]],
                "groupsPolicyItem": items_by_group.get(row["policy_item_group_id"], []),
                "hasPolicyItemContent": contents_by_group.get(row["policy_item_group_id"], []),
                "hasGroupDisplayText": display_by_group.get(row["policy_item_group_id"], []),
                "hasRepresentativeStrategy": strategies_by_group.get(row["policy_item_group_id"], []),
                "hasRepresentativeTechDomain": tech_domains_by_group.get(row["policy_item_group_id"], []),
                "hasRepresentativeTechSubdomain": tech_subdomains_by_group.get(row["policy_item_group_id"], []),
            }
        )

    for row in policy_item_contents:
        graph.append(
            {
                "@id": content_iri_map[row["policy_item_content_id"]],
                "@type": "po:PolicyItemContent",
                "identifier": row["policy_item_content_id"],
                "label": row["content_label"],
                "contentStatementText": row["content_statement"],
                "summaryText": row["content_summary"],
                "contentType": row["content_type"],
                "contentStatus": row["content_status"],
                "belongsToPolicyItemGroup": group_iri_map[row["policy_item_group_id"]],
                "hasContentEvidence": content_evidence_by_content.get(row["policy_item_content_id"], []),
                "hasContentDisplayText": display_by_content.get(row["policy_item_content_id"], []),
            }
        )

    display_target_map = {}
    for row in display_texts:
        if row["target_object_type"] == "policy_item":
            display_target_map[row["display_text_id"]] = item_iri_map.get(row["target_object_id"])
        elif row["target_object_type"] == "policy_item_group":
            display_target_map[row["display_text_id"]] = group_iri_map.get(row["target_object_id"])
        elif row["target_object_type"] == "policy_item_content":
            display_target_map[row["display_text_id"]] = content_iri_map.get(row["target_object_id"])
        else:
            display_target_map[row["display_text_id"]] = None

    for row in display_texts:
        node = {
            "@id": display_iri_map[row["display_text_id"]],
            "@type": "po:DisplayText",
            "identifier": row["display_text_id"],
            "displayRole": row["display_role"],
            "title": row["title_text"],
            "summaryText": row["summary_text"],
            "descriptionText": row["description_text"],
        }
        if display_target_map[row["display_text_id"]]:
            node["displayFor"] = display_target_map[row["display_text_id"]]
        graph.append(node)

    paragraph_object_by_rep: dict[str, str] = {}
    for row in evidence_paragraphs:
        iri = paragraph_iri_map[row["evidence_paragraph_id"]]
        paragraph_object_by_rep[row["paragraph_id"]] = iri
        graph.append(
            {
                "@id": iri,
                "@type": "po:EvidenceParagraph",
                "identifier": row["evidence_paragraph_id"],
                "descriptionText": row["text"],
                "pageNo": row["page_no"],
            }
        )

    table_object_by_rep: dict[str, str] = {}
    for row in evidence_tables:
        iri = table_iri_map[row["evidence_table_id"]]
        table_object_by_rep[row["canonical_table_id"]] = iri
        graph.append(
            {
                "@id": iri,
                "@type": "po:EvidenceTable",
                "identifier": row["evidence_table_id"],
                "title": row["title_hint"],
                "pageNo": row["page_start"],
            }
        )

    figure_object_by_rep: dict[str, str] = {}
    for row in evidence_figures:
        iri = figure_iri_map[row["evidence_figure_id"]]
        figure_object_by_rep[row["figure_id"]] = iri
        graph.append(
            {
                "@id": iri,
                "@type": "po:EvidenceFigure",
                "identifier": row["evidence_figure_id"],
                "title": row["caption"],
                "summaryText": row["summary_text"],
                "pageNo": row["page_no"],
                "assetPathOrUrl": row["asset_path"],
                "descriptionText": row["notes"],
            }
        )

    source_map_by_rep: dict[str, list[str]] = {}
    for row in derived_source_map:
        source_map_by_rep.setdefault(row["derived_representation_id"], []).append(asset_iri_map[row["source_asset_id"]])

    for row in source_assets:
        graph.append(
            {
                "@id": asset_iri_map[row["source_asset_id"]],
                "@type": "po:SourceAsset",
                "identifier": row["source_asset_id"],
                "assetPathOrUrl": row["asset_path_or_url"],
                "pageNo": row["page_no"],
                "sectionId": row["section_id"],
                "descriptionText": row["notes"],
            }
        )

    for row in derived_reps:
        evidence_object_iri = None
        if row["source_object_type"] == "paragraph":
            evidence_object_iri = paragraph_object_by_rep.get(row["source_object_id"])
        elif row["source_object_type"] == "canonical_table":
            evidence_object_iri = table_object_by_rep.get(row["source_object_id"])
        elif row["source_object_type"] == "figure":
            evidence_object_iri = figure_object_by_rep.get(row["source_object_id"])
        node = {
            "@id": rep_iri_map[row["derived_representation_id"]],
            "@type": "po:DerivedRepresentation",
            "identifier": row["derived_representation_id"],
            "representationType": row["representation_type"],
            "locationType": row["location_type"],
            "locationValue": row["location_value"],
            "summaryText": row["plain_text"],
            "wasDerivedFrom": source_map_by_rep.get(row["derived_representation_id"], []),
        }
        if evidence_object_iri:
            node["representsEvidenceObject"] = evidence_object_iri
        graph.append(node)

    jsonld_payload = {"@context": context, "@graph": graph}
    write_text(Path(args.out_jsonld), json.dumps(jsonld_payload, ensure_ascii=False, indent=2))

    turtle_lines = [
        f"@prefix po: <{ONTOLOGY}> .",
        f"@prefix res: <{RESOURCE}/> .",
        "@prefix dct: <http://purl.org/dc/terms/> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "",
    ]

    append_block(
        turtle_lines,
        resource_scheme_iri,
        ["  a skos:ConceptScheme ;", lit_line("  skos:prefLabel", "Resource Categories")],
    )
    append_block(
        turtle_lines,
        strategy_scheme_iri,
        ["  a skos:ConceptScheme ;", lit_line("  skos:prefLabel", "Strategies")],
    )
    append_block(
        turtle_lines,
        tech_domain_scheme_iri,
        ["  a skos:ConceptScheme ;", lit_line("  skos:prefLabel", "Technology Domains")],
    )
    append_block(
        turtle_lines,
        tech_subdomain_scheme_iri,
        ["  a skos:ConceptScheme ;", lit_line("  skos:prefLabel", "Technology Subdomains")],
    )

    for row in resource_categories:
        append_block(
            turtle_lines,
            rc_iri_map[row["resource_category_id"]],
            [
                "  a po:ResourceCategory, skos:Concept ;",
                lit_line("  dct:identifier", row["resource_category_id"]),
                lit_line("  skos:prefLabel", row["display_label"]),
                lit_line("  po:descriptionText", row["description"]),
                iri_line("  skos:inScheme", resource_scheme_iri),
            ],
        )

    for row in strategies:
        append_block(
            turtle_lines,
            strategy_iri_map[row["strategy_id"]],
            [
                "  a po:Strategy, skos:Concept ;",
                lit_line("  dct:identifier", row["strategy_id"]),
                lit_line("  skos:prefLabel", row["strategy_label"]),
                lit_line("  po:descriptionText", row["strategy_description"]),
                iri_line("  skos:inScheme", strategy_scheme_iri),
            ],
        )

    for row in tech_domains:
        append_block(
            turtle_lines,
            td_iri_map[row["tech_domain_id"]],
            [
                "  a po:TechnologyDomain, skos:Concept ;",
                lit_line("  dct:identifier", row["tech_domain_id"]),
                lit_line("  skos:prefLabel", row["tech_domain_label"]),
                iri_line("  skos:inScheme", tech_domain_scheme_iri),
            ],
        )

    for row in tech_subdomains:
        append_block(
            turtle_lines,
            ts_iri_map[row["tech_subdomain_id"]],
            [
                "  a po:TechnologySubdomain, skos:Concept ;",
                lit_line("  dct:identifier", row["tech_subdomain_id"]),
                lit_line("  skos:prefLabel", row["tech_subdomain_label"]),
                iri_line("  skos:inScheme", tech_subdomain_scheme_iri),
                iri_line("  skos:broader", td_iri_map[row["tech_domain_id"]]),
            ],
        )

    for row in documents:
        statements = [
            "  a po:PolicyDocument ;",
            lit_line("  dct:identifier", row["document_id"]),
            lit_line("  dct:title", row["normalized_title"]),
        ]
        if row["policy_id"]:
            statements.append(iri_line("  po:forPolicy", policy_iri_map[row["policy_id"]]))
        if row["notes"]:
            statements.append(lit_line("  po:descriptionText", row["notes"]))
        if row["location_granularity"]:
            statements.append(lit_line("  po:locationValue", row["location_granularity"]))
        append_block(turtle_lines, document_iri_map[row["document_id"]], statements)

    for row in policies:
        statements = [
            "  a po:Policy ;",
            lit_line("  dct:identifier", row["policy_id"]),
            lit_line("  skos:prefLabel", row["policy_name"]),
            lit_line("  po:policyStatus", row["policy_status"]),
        ]
        for document_iri in documents_by_policy.get(row["policy_id"], []):
            statements.append(iri_line("  po:hasDocument", document_iri))
        for bucket_iri in buckets_by_policy.get(row["policy_id"], []):
            statements.append(iri_line("  po:hasBucket", bucket_iri))
        if row["primary_document_id"]:
            statements.append(iri_line("  po:primaryDocument", document_iri_map[row["primary_document_id"]]))
        append_block(turtle_lines, policy_iri_map[row["policy_id"]], statements)

    for row in policy_buckets:
        statements = [
            "  a po:PolicyBucket ;",
            lit_line("  dct:identifier", row["policy_bucket_id"]),
            iri_line("  po:belongsToPolicy", policy_iri_map[row["policy_id"]]),
            iri_line("  po:hasResourceCategory", rc_iri_map[row["resource_category_id"]]),
            lit_line("  po:bucketStatus", row["bucket_status"]),
        ]
        for iri in items_by_bucket.get(row["policy_bucket_id"], []):
            statements.append(iri_line("  po:hasPolicyItem", iri))
        for iri in groups_by_bucket.get(row["policy_bucket_id"], []):
            statements.append(iri_line("  po:hasPolicyItemGroup", iri))
        append_block(turtle_lines, bucket_iri_map[row["policy_bucket_id"]], statements)

    for row in policy_items:
        statements = [
            "  a po:PolicyItem ;",
            lit_line("  dct:identifier", row["policy_item_id"]),
            lit_line("  skos:prefLabel", row["item_label"]),
            lit_line("  po:statementText", row["item_statement"]),
            lit_line("  po:descriptionText", row["item_description"]),
            lit_line("  po:itemStatus", row["item_status"]),
            iri_line("  po:belongsToBucket", bucket_iri_map[row["policy_bucket_id"]]),
        ]
        for iri in groups_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:groupedInPolicyItemGroup", iri))
        for iri in item_links_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:hasEvidence", iri))
        for iri in display_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:hasDisplayText", iri))
        for iri in strategies_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:hasStrategy", iri))
        for iri in tech_domains_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:hasTechDomain", iri))
        for iri in tech_subdomains_by_item.get(row["policy_item_id"], []):
            statements.append(iri_line("  po:hasTechSubdomain", iri))
        append_block(turtle_lines, item_iri_map[row["policy_item_id"]], statements)

    for row in policy_item_groups:
        statements = [
            "  a po:PolicyItemGroup ;",
            lit_line("  dct:identifier", row["policy_item_group_id"]),
            lit_line("  skos:prefLabel", row["group_label"]),
            lit_line("  po:summaryText", row["group_summary"]),
            lit_line("  po:descriptionText", row["group_description"]),
            lit_line("  po:groupStatus", row["group_status"]),
            iri_line("  po:belongsToPolicyBucket", bucket_iri_map[row["policy_bucket_id"]]),
        ]
        for iri in items_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:groupsPolicyItem", iri))
        for iri in contents_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:hasPolicyItemContent", iri))
        for iri in display_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:hasGroupDisplayText", iri))
        for iri in strategies_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:hasRepresentativeStrategy", iri))
        for iri in tech_domains_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:hasRepresentativeTechDomain", iri))
        for iri in tech_subdomains_by_group.get(row["policy_item_group_id"], []):
            statements.append(iri_line("  po:hasRepresentativeTechSubdomain", iri))
        append_block(turtle_lines, group_iri_map[row["policy_item_group_id"]], statements)

    for row in policy_item_contents:
        statements = [
            "  a po:PolicyItemContent ;",
            lit_line("  dct:identifier", row["policy_item_content_id"]),
            lit_line("  skos:prefLabel", row["content_label"]),
            lit_line("  po:contentStatementText", row["content_statement"]),
            lit_line("  po:summaryText", row["content_summary"]),
            lit_line("  po:contentType", row["content_type"]),
            lit_line("  po:contentStatus", row["content_status"]),
            iri_line("  po:belongsToPolicyItemGroup", group_iri_map[row["policy_item_group_id"]]),
        ]
        for iri in content_evidence_by_content.get(row["policy_item_content_id"], []):
            statements.append(iri_line("  po:hasContentEvidence", iri))
        for iri in display_by_content.get(row["policy_item_content_id"], []):
            statements.append(iri_line("  po:hasContentDisplayText", iri))
        append_block(turtle_lines, content_iri_map[row["policy_item_content_id"]], statements)

    for row in display_texts:
        statements = [
            "  a po:DisplayText ;",
            lit_line("  dct:identifier", row["display_text_id"]),
            lit_line("  po:displayRole", row["display_role"]),
            lit_line("  dct:title", row["title_text"]),
            lit_line("  po:summaryText", row["summary_text"]),
            lit_line("  po:descriptionText", row["description_text"]),
        ]
        target_iri = display_target_map.get(row["display_text_id"])
        if target_iri:
            statements.append(iri_line("  po:displayFor", target_iri))
        append_block(turtle_lines, display_iri_map[row["display_text_id"]], statements)

    for row in evidence_paragraphs:
        append_block(
            turtle_lines,
            paragraph_iri_map[row["evidence_paragraph_id"]],
            [
                "  a po:EvidenceParagraph ;",
                lit_line("  dct:identifier", row["evidence_paragraph_id"]),
                lit_line("  po:descriptionText", row["text"]),
                lit_line("  po:pageNo", row["page_no"]),
            ],
        )

    for row in evidence_tables:
        append_block(
            turtle_lines,
            table_iri_map[row["evidence_table_id"]],
            [
                "  a po:EvidenceTable ;",
                lit_line("  dct:identifier", row["evidence_table_id"]),
                lit_line("  dct:title", row["title_hint"]),
                lit_line("  po:pageNo", row["page_start"]),
            ],
        )

    for row in evidence_figures:
        statements = [
            "  a po:EvidenceFigure ;",
            lit_line("  dct:identifier", row["evidence_figure_id"]),
        ]
        if row["caption"]:
            statements.append(lit_line("  dct:title", row["caption"]))
        if row["summary_text"]:
            statements.append(lit_line("  po:summaryText", row["summary_text"]))
        if row["page_no"]:
            statements.append(lit_line("  po:pageNo", row["page_no"]))
        if row["asset_path"]:
            statements.append(lit_line("  po:assetPathOrUrl", row["asset_path"]))
        if row["notes"]:
            statements.append(lit_line("  po:descriptionText", row["notes"]))
        append_block(turtle_lines, figure_iri_map[row["evidence_figure_id"]], statements)

    for row in source_assets:
        statements = [
            "  a po:SourceAsset ;",
            lit_line("  dct:identifier", row["source_asset_id"]),
            lit_line("  po:assetPathOrUrl", row["asset_path_or_url"]),
        ]
        if row["page_no"]:
            statements.append(lit_line("  po:pageNo", row["page_no"]))
        if row["section_id"]:
            statements.append(lit_line("  po:sectionId", row["section_id"]))
        if row["notes"]:
            statements.append(lit_line("  po:descriptionText", row["notes"]))
        append_block(turtle_lines, asset_iri_map[row["source_asset_id"]], statements)

    for row in derived_reps:
        statements = [
            "  a po:DerivedRepresentation ;",
            lit_line("  dct:identifier", row["derived_representation_id"]),
            lit_line("  po:representationType", row["representation_type"]),
            lit_line("  po:locationType", row["location_type"]),
            lit_line("  po:locationValue", row["location_value"]),
        ]
        if row["plain_text"]:
            statements.append(lit_line("  po:summaryText", row["plain_text"]))
        for iri in source_map_by_rep.get(row["derived_representation_id"], []):
            statements.append(iri_line("  prov:wasDerivedFrom", iri))
        if row["source_object_type"] == "paragraph" and row["source_object_id"] in paragraph_object_by_rep:
            statements.append(iri_line("  po:representsEvidenceObject", paragraph_object_by_rep[row["source_object_id"]]))
        if row["source_object_type"] == "canonical_table" and row["source_object_id"] in table_object_by_rep:
            statements.append(iri_line("  po:representsEvidenceObject", table_object_by_rep[row["source_object_id"]]))
        if row["source_object_type"] == "figure" and row["source_object_id"] in figure_object_by_rep:
            statements.append(iri_line("  po:representsEvidenceObject", figure_object_by_rep[row["source_object_id"]]))
        append_block(turtle_lines, rep_iri_map[row["derived_representation_id"]], statements)

    write_text(Path(args.out_turtle), "\n".join(turtle_lines))
    print(f"JSON-LD graph nodes: {len(graph)}")
    print(f"Turtle blocks exported: {len(graph)}")


if __name__ == "__main__":
    main()
