PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS resource_categories (
    resource_category_id TEXT PRIMARY KEY,
    display_label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    policy_name TEXT NOT NULL,
    policy_order INTEGER NOT NULL,
    policy_status TEXT NOT NULL DEFAULT 'active',
    primary_document_id TEXT,
    has_source_document INTEGER NOT NULL DEFAULT 0 CHECK (has_source_document IN (0, 1)),
    source_document_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    registry_id TEXT NOT NULL UNIQUE,
    policy_id TEXT,
    doc_role TEXT NOT NULL,
    scope_track TEXT NOT NULL,
    include_status TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    source_rel_path TEXT NOT NULL DEFAULT '',
    internal_path TEXT NOT NULL DEFAULT '',
    source_format TEXT NOT NULL,
    issuing_org TEXT NOT NULL DEFAULT '',
    issued_date TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    location_granularity TEXT NOT NULL DEFAULT 'unknown',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE IF NOT EXISTS policy_buckets (
    policy_bucket_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    resource_category_id TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    bucket_summary TEXT NOT NULL DEFAULT '',
    bucket_status TEXT NOT NULL DEFAULT 'planned',
    UNIQUE (policy_id, resource_category_id),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id),
    FOREIGN KEY (resource_category_id) REFERENCES resource_categories(resource_category_id)
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    strategy_label TEXT NOT NULL,
    strategy_description TEXT NOT NULL DEFAULT '',
    source_basis TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS tech_domains (
    tech_domain_id TEXT PRIMARY KEY,
    tech_domain_label TEXT NOT NULL,
    source_basis TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS tech_subdomains (
    tech_subdomain_id TEXT PRIMARY KEY,
    tech_domain_id TEXT NOT NULL,
    tech_subdomain_label TEXT NOT NULL,
    source_basis TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    UNIQUE (tech_domain_id, tech_subdomain_label),
    FOREIGN KEY (tech_domain_id) REFERENCES tech_domains(tech_domain_id)
);

CREATE TABLE IF NOT EXISTS source_assets (
    source_asset_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT '',
    asset_path_or_url TEXT NOT NULL,
    page_no TEXT NOT NULL DEFAULT '',
    section_id TEXT NOT NULL DEFAULT '',
    bbox_json TEXT NOT NULL DEFAULT '',
    thumbnail_path TEXT NOT NULL DEFAULT '',
    quality_status TEXT NOT NULL DEFAULT 'unreviewed',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS derived_representations (
    derived_representation_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    source_asset_id TEXT,
    representation_type TEXT NOT NULL,
    source_object_type TEXT NOT NULL DEFAULT '',
    source_object_id TEXT NOT NULL DEFAULT '',
    location_type TEXT NOT NULL DEFAULT '',
    location_value TEXT NOT NULL DEFAULT '',
    plain_text TEXT NOT NULL DEFAULT '',
    structured_payload_path TEXT NOT NULL DEFAULT '',
    table_json_path TEXT NOT NULL DEFAULT '',
    normalization_version TEXT NOT NULL DEFAULT '',
    quality_status TEXT NOT NULL DEFAULT 'unreviewed',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (source_asset_id) REFERENCES source_assets(source_asset_id),
    UNIQUE (source_object_type, source_object_id)
);

CREATE TABLE IF NOT EXISTS display_texts (
    display_text_id TEXT PRIMARY KEY,
    target_object_type TEXT NOT NULL,
    target_object_id TEXT NOT NULL,
    display_role TEXT NOT NULL,
    title_text TEXT NOT NULL DEFAULT '',
    summary_text TEXT NOT NULL DEFAULT '',
    description_text TEXT NOT NULL DEFAULT '',
    generated_by TEXT NOT NULL DEFAULT 'manual',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    source_basis_type TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS evidence_paragraphs (
    evidence_paragraph_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    paragraph_id TEXT NOT NULL UNIQUE,
    page_no TEXT NOT NULL DEFAULT '',
    page_block_order INTEGER NOT NULL DEFAULT 0,
    block_type TEXT NOT NULL,
    text TEXT NOT NULL,
    source_mode TEXT NOT NULL DEFAULT '',
    source_line_count INTEGER NOT NULL DEFAULT 0,
    merged_block_count INTEGER NOT NULL DEFAULT 1,
    review_status TEXT NOT NULL DEFAULT 'review_required',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS evidence_tables (
    evidence_table_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    canonical_table_id TEXT NOT NULL UNIQUE,
    title_hint TEXT NOT NULL DEFAULT '',
    page_start TEXT NOT NULL DEFAULT '',
    page_end TEXT NOT NULL DEFAULT '',
    preferred_candidate_source TEXT NOT NULL DEFAULT '',
    preferred_candidate_id TEXT NOT NULL DEFAULT '',
    canonical_status TEXT NOT NULL DEFAULT 'needs_review',
    dashboard_ready INTEGER NOT NULL DEFAULT 0 CHECK (dashboard_ready IN (0, 1)),
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS evidence_figures (
    evidence_figure_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    figure_id TEXT NOT NULL UNIQUE,
    figure_type TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    page_no TEXT NOT NULL DEFAULT '',
    asset_path TEXT NOT NULL DEFAULT '',
    summary_text TEXT NOT NULL DEFAULT '',
    quality_status TEXT NOT NULL DEFAULT 'unreviewed',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS policy_items (
    policy_item_id TEXT PRIMARY KEY,
    policy_bucket_id TEXT NOT NULL,
    item_label TEXT NOT NULL,
    item_statement TEXT NOT NULL DEFAULT '',
    item_description TEXT NOT NULL DEFAULT '',
    item_status TEXT NOT NULL DEFAULT 'draft',
    source_basis_type TEXT NOT NULL DEFAULT 'source_document_only',
    curation_priority INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_bucket_id) REFERENCES policy_buckets(policy_bucket_id)
);

CREATE TABLE IF NOT EXISTS policy_item_groups (
    policy_item_group_id TEXT PRIMARY KEY,
    policy_bucket_id TEXT NOT NULL,
    group_label TEXT NOT NULL,
    group_summary TEXT NOT NULL DEFAULT '',
    group_description TEXT NOT NULL DEFAULT '',
    group_status TEXT NOT NULL DEFAULT 'draft',
    source_basis_type TEXT NOT NULL DEFAULT 'mixed',
    display_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_bucket_id) REFERENCES policy_buckets(policy_bucket_id)
);

CREATE TABLE IF NOT EXISTS policy_item_group_members (
    policy_item_group_member_id TEXT PRIMARY KEY,
    policy_item_group_id TEXT NOT NULL,
    policy_item_id TEXT NOT NULL,
    member_role TEXT NOT NULL DEFAULT 'supporting_item',
    is_representative INTEGER NOT NULL DEFAULT 0 CHECK (is_representative IN (0, 1)),
    confidence TEXT NOT NULL DEFAULT 'medium',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_group_id) REFERENCES policy_item_groups(policy_item_group_id),
    FOREIGN KEY (policy_item_id) REFERENCES policy_items(policy_item_id),
    UNIQUE (policy_item_group_id, policy_item_id)
);

CREATE TABLE IF NOT EXISTS policy_item_contents (
    policy_item_content_id TEXT PRIMARY KEY,
    policy_item_group_id TEXT NOT NULL,
    content_label TEXT NOT NULL,
    content_statement TEXT NOT NULL DEFAULT '',
    content_summary TEXT NOT NULL DEFAULT '',
    content_type TEXT NOT NULL DEFAULT 'policy_action',
    content_status TEXT NOT NULL DEFAULT 'draft',
    display_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_group_id) REFERENCES policy_item_groups(policy_item_group_id)
);

CREATE TABLE IF NOT EXISTS policy_item_evidence_links (
    policy_item_evidence_link_id TEXT PRIMARY KEY,
    policy_item_id TEXT NOT NULL,
    derived_representation_id TEXT NOT NULL,
    link_role TEXT NOT NULL DEFAULT 'primary_support',
    evidence_strength TEXT NOT NULL DEFAULT 'medium',
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_id) REFERENCES policy_items(policy_item_id),
    FOREIGN KEY (derived_representation_id) REFERENCES derived_representations(derived_representation_id),
    UNIQUE (policy_item_id, derived_representation_id, link_role)
);

CREATE TABLE IF NOT EXISTS policy_item_content_evidence_links (
    policy_item_content_evidence_link_id TEXT PRIMARY KEY,
    policy_item_content_id TEXT NOT NULL,
    derived_representation_id TEXT NOT NULL,
    link_role TEXT NOT NULL DEFAULT 'primary_support',
    evidence_strength TEXT NOT NULL DEFAULT 'medium',
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_content_id) REFERENCES policy_item_contents(policy_item_content_id),
    FOREIGN KEY (derived_representation_id) REFERENCES derived_representations(derived_representation_id),
    UNIQUE (policy_item_content_id, derived_representation_id, link_role)
);

CREATE TABLE IF NOT EXISTS policy_item_group_taxonomy_map (
    policy_item_group_taxonomy_map_id TEXT PRIMARY KEY,
    policy_item_group_id TEXT NOT NULL,
    taxonomy_type TEXT NOT NULL,
    term_id TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    confidence TEXT NOT NULL DEFAULT 'medium',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_group_id) REFERENCES policy_item_groups(policy_item_group_id)
);

CREATE TABLE IF NOT EXISTS policy_item_taxonomy_map (
    policy_item_taxonomy_map_id TEXT PRIMARY KEY,
    policy_item_id TEXT NOT NULL,
    taxonomy_type TEXT NOT NULL,
    term_id TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    confidence TEXT NOT NULL DEFAULT 'medium',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (policy_item_id) REFERENCES policy_items(policy_item_id)
);

CREATE TABLE IF NOT EXISTS paragraph_source_map (
    paragraph_source_map_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL,
    source_evidence_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_no_or_section TEXT NOT NULL DEFAULT '',
    bbox_json TEXT NOT NULL DEFAULT '',
    source_block_order INTEGER NOT NULL DEFAULT 0,
    mapping_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (paragraph_id, source_evidence_id)
);

CREATE TABLE IF NOT EXISTS derived_to_source_asset_map (
    derived_to_source_asset_map_id TEXT PRIMARY KEY,
    derived_representation_id TEXT NOT NULL,
    source_asset_id TEXT NOT NULL,
    mapping_type TEXT NOT NULL DEFAULT 'direct',
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (derived_representation_id) REFERENCES derived_representations(derived_representation_id),
    FOREIGN KEY (source_asset_id) REFERENCES source_assets(source_asset_id),
    UNIQUE (derived_representation_id, source_asset_id, mapping_type)
);

CREATE TABLE IF NOT EXISTS derived_to_display_map (
    derived_to_display_map_id TEXT PRIMARY KEY,
    derived_representation_id TEXT NOT NULL,
    display_text_id TEXT NOT NULL,
    display_role TEXT NOT NULL DEFAULT '',
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (derived_representation_id) REFERENCES derived_representations(derived_representation_id),
    FOREIGN KEY (display_text_id) REFERENCES display_texts(display_text_id),
    UNIQUE (derived_representation_id, display_text_id, display_role)
);

CREATE TABLE IF NOT EXISTS curation_assertions (
    assertion_id TEXT PRIMARY KEY,
    target_object_type TEXT NOT NULL,
    target_object_id TEXT NOT NULL,
    assertion_type TEXT NOT NULL,
    asserted_value TEXT NOT NULL,
    confidence TEXT NOT NULL DEFAULT 'medium',
    asserted_by TEXT NOT NULL DEFAULT 'manual',
    asserted_at TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    source_note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS data_quality_flags (
    data_quality_flag_id TEXT PRIMARY KEY,
    target_object_type TEXT NOT NULL,
    target_object_id TEXT NOT NULL,
    flag_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    flag_status TEXT NOT NULL DEFAULT 'open',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_documents_policy_id ON documents(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_buckets_policy_id ON policy_buckets(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_items_bucket_id ON policy_items(policy_bucket_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_groups_bucket_id ON policy_item_groups(policy_bucket_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_group_members_group_id ON policy_item_group_members(policy_item_group_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_group_members_item_id ON policy_item_group_members(policy_item_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_contents_group_id ON policy_item_contents(policy_item_group_id);
CREATE INDEX IF NOT EXISTS idx_source_assets_document_id ON source_assets(document_id);
CREATE INDEX IF NOT EXISTS idx_derived_representations_document_id ON derived_representations(document_id);
CREATE INDEX IF NOT EXISTS idx_derived_representations_source_asset_id ON derived_representations(source_asset_id);
CREATE INDEX IF NOT EXISTS idx_display_texts_target ON display_texts(target_object_type, target_object_id);
CREATE INDEX IF NOT EXISTS idx_evidence_paragraphs_document_id ON evidence_paragraphs(document_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_evidence_links_policy_item_id ON policy_item_evidence_links(policy_item_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_content_evidence_links_content_id ON policy_item_content_evidence_links(policy_item_content_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_group_taxonomy_map_group_id ON policy_item_group_taxonomy_map(policy_item_group_id);
CREATE INDEX IF NOT EXISTS idx_policy_item_taxonomy_map_policy_item_id ON policy_item_taxonomy_map(policy_item_id);
CREATE INDEX IF NOT EXISTS idx_paragraph_source_map_paragraph_id ON paragraph_source_map(paragraph_id);
CREATE INDEX IF NOT EXISTS idx_curation_assertions_target ON curation_assertions(target_object_type, target_object_id);
