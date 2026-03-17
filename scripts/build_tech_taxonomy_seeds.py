#!/usr/bin/env python3
"""Build tech domain and subdomain seed CSVs and load them into SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--db-path")
    args = parser.parse_args()

    rows = read_csv_rows(Path(args.taxonomy_csv))
    domain_order: list[str] = []
    subdomains_by_domain: dict[str, list[str]] = {}

    for row in rows:
        domain = row["tech_domain"].strip()
        subdomain = row["tech_subdomain"].strip()
        if domain not in subdomains_by_domain:
            domain_order.append(domain)
            subdomains_by_domain[domain] = []
        if subdomain not in subdomains_by_domain[domain]:
            subdomains_by_domain[domain].append(subdomain)

    domain_rows = []
    subdomain_rows = []
    domain_id_map: dict[str, str] = {}

    for domain_index, domain in enumerate(domain_order, start=1):
        tech_domain_id = f"TD-{domain_index:03d}"
        domain_id_map[domain] = tech_domain_id
        domain_rows.append(
            {
                "tech_domain_id": tech_domain_id,
                "tech_domain_label": domain,
                "source_basis": "DOC-TAX-001",
                "display_order": domain_index,
                "is_active": 1,
            }
        )
        for sub_index, subdomain in enumerate(subdomains_by_domain[domain], start=1):
            subdomain_rows.append(
                {
                    "tech_subdomain_id": f"TSD-{domain_index:03d}-{sub_index:03d}",
                    "tech_domain_id": tech_domain_id,
                    "tech_subdomain_label": subdomain,
                    "source_basis": "DOC-TAX-001",
                    "display_order": sub_index,
                    "is_active": 1,
                }
            )

    out_dir = Path(args.out_dir)
    write_csv(
        out_dir / "tech_domains_seed.csv",
        domain_rows,
        ["tech_domain_id", "tech_domain_label", "source_basis", "display_order", "is_active"],
    )
    write_csv(
        out_dir / "tech_subdomains_seed.csv",
        subdomain_rows,
        ["tech_subdomain_id", "tech_domain_id", "tech_subdomain_label", "source_basis", "display_order", "is_active"],
    )

    if args.db_path:
        connection = sqlite3.connect(args.db_path)
        try:
            connection.executemany(
                """
                INSERT OR REPLACE INTO tech_domains (
                    tech_domain_id,
                    tech_domain_label,
                    source_basis,
                    display_order,
                    is_active
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["tech_domain_id"],
                        row["tech_domain_label"],
                        row["source_basis"],
                        row["display_order"],
                        row["is_active"],
                    )
                    for row in domain_rows
                ],
            )
            connection.executemany(
                """
                INSERT OR REPLACE INTO tech_subdomains (
                    tech_subdomain_id,
                    tech_domain_id,
                    tech_subdomain_label,
                    source_basis,
                    display_order,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["tech_subdomain_id"],
                        row["tech_domain_id"],
                        row["tech_subdomain_label"],
                        row["source_basis"],
                        row["display_order"],
                        row["is_active"],
                    )
                    for row in subdomain_rows
                ],
            )
            connection.commit()
        finally:
            connection.close()

    print(f"Tech domains: {len(domain_rows)}")
    print(f"Tech subdomains: {len(subdomain_rows)}")


if __name__ == "__main__":
    main()
