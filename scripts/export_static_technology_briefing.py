#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "work/05_dashboard/data-contracts/technology-lens.json"
OUTPUT_PATH = ROOT / "work/05_dashboard/index.html"
DETAIL_TECH_OUTPUT_PATH = ROOT / "work/05_dashboard/detail-tech.html"
DETAIL_POLICY_OUTPUT_PATH = ROOT / "work/05_dashboard/detail-policy.html"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def compact_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def clean_display_text(value: Any) -> str:
    text = compact_text(value)
    replacements = {
        "대표 묶음": "주요 과제",
        "대표 샘플": "주요 과제",
        "샘플": "과제",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return text


def humanize_label_text(value: Any) -> str:
    text = clean_display_text(value)
    text = re.sub(r"([가-힣])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9])([가-힣])", r"\1 \2", text)
    replacements = {
        "국방개혁로드맵마련": "국방개혁 로드맵 마련",
        "군사법개혁": "군사법 개혁",
        "규모국민성장펀드신설": "규모 국민성장펀드 신설",
        "특단대책강구": "특단 대책 강구",
        "디지털보안·안전확보": "디지털 보안·안전 확보",
        "초지능네트워크구축": "초지능 네트워크 구축",
        "고부가가치서비스업육성": "고부가가치 서비스업 육성",
        "전환촉진": "전환 촉진",
        "산업기반구축": "산업 기반 구축",
        "산업경쟁력강화": "산업 경쟁력 강화",
        "안전대책마련": "안전대책 마련",
        "파운드리구축": "파운드리 구축",
        "후보물질개발": "후보물질 개발",
        "보안사각지대지원강화": "보안 사각지대 지원 강화",
        "AX지도": "AX 지도",
        "인재양성": "인재 양성",
        "로드맵마련": "로드맵 마련",
        "자율주행실현": "자율주행 실현",
        "국방AI": "국방 AI",
        "AI반도체": "AI 반도체",
        "산업AI": "산업 AI",
        "우리기술로": "우리 기술로 ",
        "국가해상수송력확충": "국가 해상수송력 확충",
        "글로벌허브항만완성": "글로벌 허브항만 완성",
        "감시체계역량강화": "감시체계 역량 강화",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return compact_text(text)


def concise_label_text(value: Any) -> str:
    text = humanize_label_text(value)
    replacements = {
        "바이오 데이터 플랫폼 및 개방체계": "바이오 데이터 개방체계",
        "보안이취약한지역·중소기업등보안 사각지대 지원 강화": "보안 취약 지역·중소기업 지원 강화",
        "첨단바이오소재후보물질 개발·생산이가능한바이오파운드리 구축('25～'29)": "첨단바이오 소재 바이오파운드리 구축",
        "함정‧ 항공기정보및첨단기술(위성등) 기반광역감시·정보체계(MDA) 구축": "광역 감시·정보체계(MDA) 구축",
        "독도등관할해역감시체계 역량 강화로빈틈없는해양안보태세를구비 하고": "관할 해역 감시체계 역량 강화",
        "국가 해상수송력 확충과글로벌 허브항만 완성으로우리수출입물류를 뒷받침하고": "국가 해상수송력·허브항만 강화",
        "친환경차·소프트웨어차량(SDV)·AI 자율주행차등미래차혁신생태계조성": "미래차 혁신생태계 조성",
        "전기차·이륜차·개인이동수단(PM) 안전대책 마련": "전기차·이동수단 안전대책 마련",
        "1 단계 R&D('20~'25": "자율운항 실증",
        "6G·AI 네트워크 선도국 도약 및 글로벌 통신·네트워크 거대 시장 석권을 위해": "6G·AI 네트워크 선도",
        "고효율·친환경 기지국 인증제 도입(’26) 검토 등 저전력 통신망 구축 독려": "저전력 통신망 구축",
        "3 대위기업종(석유화학·철강·이차전지) 특단 대책 강구": "3대 위기업종 특단 대책",
        "100 조원+α 규모 국민성장펀드 신설": "국민성장펀드 신설",
    }
    return replacements.get(text, text)


def compare_key(value: Any) -> str:
    return compact_text(value).replace(" ", "")


def clean_quote_text(value: Any) -> str:
    text = compact_text(value)
    prefixes = [
        "ㅇ ",
        "○ ",
        "□ ",
        "- ",
        "➊",
        "➋",
        "①",
        "②",
        "③",
    ]
    changed = True
    while changed and text:
        changed = False
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True
    return text


def looks_raw_source_text(value: Any) -> bool:
    text = compact_text(value)
    if not text:
        return True
    raw_prefixes = (
        "ㅇ ",
        "○ ",
        "□ ",
        "- ",
        "➊",
        "➋",
        "①",
        "②",
        "③",
        "(",
    )
    if text.startswith(raw_prefixes):
        return True
    if len(text) >= 45 and text.count(" ") <= 3:
        return True
    return False


def is_readable_summary(text: str, max_length: int) -> bool:
    cleaned = compact_text(text)
    if not cleaned:
        return False
    if looks_raw_source_text(cleaned):
        return False
    return len(cleaned) <= max_length


def task_bucket_label(value: Any) -> str:
    bucket = compact_text(value)
    mapping = {
        "기술": "기술 지원",
        "technology": "기술 지원",
        "인프라·제도": "인프라·제도",
        "infrastructure_institutional": "인프라·제도",
        "인재": "인재",
        "talent": "인재",
    }
    return mapping.get(bucket, bucket or "주요")


def build_task_summary(title: Any, summary: Any, bucket_label: Any) -> str:
    clean_title = concise_label_text(title or "주요 과제")
    raw_title = clean_quote_text(humanize_label_text(title or "주요 과제"))
    clean_summary = clean_quote_text(clean_display_text(summary))
    if is_readable_summary(clean_summary, 44):
        if compare_key(clean_summary) not in {compare_key(clean_title), compare_key(raw_title)}:
            return clean_summary
    return f"{clean_title}{object_particle(clean_title)} 중심으로 한 {task_bucket_label(bucket_label)} 과제"


def build_content_summary(title: Any, summary: Any) -> str:
    clean_title = concise_label_text(title or "세부 조치")
    raw_title = clean_quote_text(humanize_label_text(title or "세부 조치"))
    clean_summary = clean_quote_text(clean_display_text(summary))
    if is_readable_summary(clean_summary, 34):
        if compare_key(clean_summary) not in {compare_key(clean_title), compare_key(raw_title)}:
            return clean_summary
    return f"{clean_title} 관련 세부 조치"


def topic_particle(text: str) -> str:
    cleaned = compact_text(text)
    if not cleaned:
        return "는"
    last = cleaned[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "는" if (code - 0xAC00) % 28 == 0 else "은"
    return "는"


def object_particle(text: str) -> str:
    cleaned = compact_text(text)
    if not cleaned:
        return "를"
    last = cleaned[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "를" if (code - 0xAC00) % 28 == 0 else "을"
    return "를"


def load_payload() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def format_generated_at(raw: str) -> str:
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return raw
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def active_domains(payload: dict[str, Any]) -> list[dict[str, Any]]:
    filter_order = {
        item["tech_domain_id"]: item.get("display_order", 999)
        for item in payload.get("tech_domain_filters", [])
    }
    domains = [
        domain
        for domain in payload.get("tech_domains", [])
        if domain.get("group_count", 0) > 0 and domain.get("content_count", 0) > 0
    ]
    return sorted(
        domains,
        key=lambda domain: (
            filter_order.get(domain["tech_domain_id"], domain.get("display_order", 999)),
            domain.get("tech_domain_label", ""),
        ),
    )


def build_policy_rows(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}

    for domain in domains:
        tech_label = domain.get("tech_domain_label", "")
        for group in domain.get("groups", []):
            policy_info = group.get("policy") or {}
            policy = policy_info.get("policy_name")
            policy_id = policy_info.get("policy_id") or policy
            if not policy or not policy_id:
                continue
            content_count = len(group.get("contents", []))
            row = rows.setdefault(
                policy_id,
                {
                    "policy_id": policy_id,
                    "policy_name": policy,
                    "policy_order": policy_info.get("policy_order", 999),
                    "group_count": 0,
                    "content_count": 0,
                    "cells": {},
                },
            )
            cell = row["cells"].setdefault(
                tech_label,
                {"group_count": 0, "content_count": 0},
            )
            cell["group_count"] += 1
            cell["content_count"] += content_count
            row["group_count"] += 1
            row["content_count"] += content_count

    result = []
    for row in rows.values():
        row["tech_count"] = len(row["cells"])
        row["max_group_count"] = max(
            (cell["group_count"] for cell in row["cells"].values()),
            default=0,
        )
        row["top_techs"] = sorted(
            row["cells"].items(),
            key=lambda item: (
                -item[1]["group_count"],
                -item[1]["content_count"],
                item[0],
            ),
        )[:3]
        result.append(row)

    return sorted(
        result,
        key=lambda row: (-row["group_count"], -row["tech_count"], row["policy_order"], row["policy_name"]),
    )


def build_tech_rows(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in domains:
        policies = {}
        for group in domain.get("groups", []):
            policy_name = (group.get("policy") or {}).get("policy_name")
            if not policy_name:
                continue
            stats = policies.setdefault(policy_name, {"group_count": 0, "content_count": 0})
            stats["group_count"] += 1
            stats["content_count"] += len(group.get("contents", []))
        top_policies = sorted(
            policies.items(),
            key=lambda item: (-item[1]["group_count"], -item[1]["content_count"], item[0]),
        )[:3]
        rows.append(
            {
                "tech_domain_id": domain.get("tech_domain_id", ""),
                "tech_domain_label": domain.get("tech_domain_label", ""),
                "policy_count": len(policies),
                "group_count": domain.get("group_count", 0),
                "content_count": domain.get("content_count", 0),
                "top_policies": top_policies,
            }
        )
    return sorted(
        rows,
        key=lambda row: (-row["policy_count"], -row["group_count"], row["tech_domain_label"]),
    )


def summary_text(domains: list[dict[str, Any]], policy_rows: list[dict[str, Any]], tech_rows: list[dict[str, Any]]) -> str:
    widest_policy = policy_rows[0]["policy_name"] if policy_rows else ""
    widest_policy_techs = policy_rows[0]["tech_count"] if policy_rows else 0
    densest_tech = tech_rows[0]["tech_domain_label"] if tech_rows else ""
    densest_tech_policies = tech_rows[0]["policy_count"] if tech_rows else 0
    return (
        f"현재 활성 기술은 {len(domains)}개, 정책은 {len(policy_rows)}개다. "
        f"가장 넓게 분산된 정책은 {widest_policy}({widest_policy_techs}개 기술)이고, "
        f"가장 많은 정책이 겹치는 기술은 {densest_tech}({densest_tech_policies}개 정책)다."
    )


def total_group_count(policy_rows: list[dict[str, Any]]) -> int:
    return sum(row["group_count"] for row in policy_rows)


def total_content_count(policy_rows: list[dict[str, Any]]) -> int:
    return sum(row["content_count"] for row in policy_rows)


def policy_tech_anchor(policy_id: str, tech_domain_id: str) -> str:
    return f"{policy_id}-{tech_domain_id}"


def strength_class(group_count: int, max_group_count: int) -> str:
    if group_count <= 0:
        return "empty"
    if max_group_count <= 1:
        return "tone-1"
    ratio = group_count / max_group_count
    if ratio >= 1:
        return "tone-4"
    if ratio >= 0.66:
        return "tone-3"
    if ratio >= 0.33:
        return "tone-2"
    return "tone-1"


def render_summary_pills(domains: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> str:
    items = [
        f'<span class="summary-pill highlight">활성 기술 {esc(len(domains))}개</span>',
        f'<span class="summary-pill">정책 {esc(len(policy_rows))}개</span>',
        f'<span class="summary-pill">주요 과제 {esc(total_group_count(policy_rows))}개</span>',
        f'<span class="summary-pill">세부 조치 {esc(total_content_count(policy_rows))}개</span>',
    ]
    return "\n          ".join(items)


def render_matrix(domains: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> str:
    header_cells = "\n".join(
        f"""              <th scope="col">
                <strong><a class="matrix-link" href="./detail-tech.html#{esc(domain.get('tech_domain_id', ''))}">{esc(domain.get('tech_domain_label', ''))}</a></strong>
                <span>{esc(domain.get('policy_count', 0))}개 정책</span>
              </th>"""
        for domain in domains
    )

    body_rows = []
    for row in policy_rows:
        cells = []
        for domain in domains:
            tech_label = domain.get("tech_domain_label", "")
            cell = row["cells"].get(tech_label)
            if not cell:
                cells.append('<td class="matrix-cell empty"><span> </span></td>')
                continue
            tone = strength_class(cell["group_count"], row["max_group_count"])
            peak = " peak" if cell["group_count"] == row["max_group_count"] else ""
            target = policy_tech_anchor(row["policy_id"], domain.get("tech_domain_id", ""))
            cells.append(
                f"""<td class="matrix-cell {tone}{peak}">
                  <a class="cell-link" href="./detail-policy.html#{esc(target)}">
                    <strong>{esc(cell['group_count'])} / {esc(cell['content_count'])}</strong>
                    <span>과제 / 조치</span>
                  </a>
                </td>"""
            )

        body_rows.append(
            f"""            <tr>
              <th scope="row" class="row-header">
                <strong><a class="matrix-link" href="./detail-policy.html#{esc(row['policy_id'])}">{esc(row['policy_name'])}</a></strong>
                <span>{esc(row['tech_count'])}개 기술 · {esc(row['group_count'])}개 과제</span>
              </th>
              {' '.join(cells)}
            </tr>"""
        )

    return f"""        <div class="panel matrix-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">집중도 매트릭스</p>
              <h2>정책 x 기술 매트릭스</h2>
            </div>
            <p class="panel-copy">셀 숫자는 주요 과제 수와 세부 조치 수를 함께 보여준다. 셀이 진할수록 해당 정책이 그 기술에 더 집중돼 있다.</p>
          </div>
          <div class="matrix-wrap">
            <table class="matrix-table" aria-label="정책 x 기술 매트릭스">
              <thead>
                <tr>
                  <th class="corner-cell">정책</th>
{header_cells}
                </tr>
              </thead>
              <tbody>
{chr(10).join(body_rows)}
              </tbody>
            </table>
          </div>
        </div>"""


def render_policy_focus(policy_rows: list[dict[str, Any]]) -> str:
    items = []
    for row in policy_rows:
        summary = " · ".join(
            f"{tech} {stats['group_count']}"
            for tech, stats in row["top_techs"]
        )
        items.append(
            f"""            <li>
              <strong><a class="matrix-link" href="./detail-policy.html#{esc(row['policy_id'])}">{esc(row['policy_name'])}</a></strong>
              <span>{esc(summary)}</span>
            </li>"""
        )
    return f"""        <article class="panel insight-card">
          <div class="panel-head compact">
            <div>
              <p class="eyebrow">정책 요약</p>
              <h3>정책별 상위 집중 기술</h3>
            </div>
          </div>
          <ul class="insight-list">
{chr(10).join(items)}
          </ul>
        </article>"""


def render_tech_focus(tech_rows: list[dict[str, Any]]) -> str:
    items = []
    for row in tech_rows:
        summary = " · ".join(
            f"{policy} {stats['group_count']}"
            for policy, stats in row["top_policies"]
        )
        items.append(
            f"""            <li>
              <strong><a class="matrix-link" href="./detail-tech.html#{esc(row['tech_domain_id'])}">{esc(row['tech_domain_label'])}</a></strong>
              <span>{esc(row['policy_count'])}개 정책 · {esc(row['group_count'])}개 과제</span>
              <small>{esc(summary)}</small>
            </li>"""
        )
    return f"""        <article class="panel insight-card">
          <div class="panel-head compact">
            <div>
              <p class="eyebrow">기술 요약</p>
              <h3>기술별 연결 정책 수</h3>
            </div>
          </div>
          <ul class="insight-list">
{chr(10).join(items)}
          </ul>
        </article>"""


def humanize_location(value: str) -> str:
    raw = compact_text(value)
    if not raw:
        return "위치 정보 확인"
    if raw.isdigit():
        return f"{raw}쪽"
    lower = raw.lower()
    if lower.startswith("section"):
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            return "문서 위치"
        section_no = int(digits)
        if section_no <= 1:
            return "문서 앞부분"
        if section_no <= 3:
            return "문서 중간"
        return "문서 후반부"
    if lower.startswith("page"):
        digits = "".join(ch for ch in raw if ch.isdigit())
        return f"{digits}쪽" if digits else "페이지"
    return raw


def sorted_groups(domain: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        domain.get("groups", []),
        key=lambda group: (
            (group.get("bucket") or {}).get("bucket_display_order", 999),
            (group.get("policy") or {}).get("policy_order", 999),
            group.get("display_order", 999),
            group.get("group_label", ""),
        ),
    )


def summarize_resource_mix(resource_counts: dict[str, int]) -> str:
    labels = [
        ("technology", "기술 지원"),
        ("infrastructure_institutional", "인프라·제도"),
        ("talent", "인재"),
    ]
    parts = [
        f"{label} {resource_counts.get(key, 0)}건"
        for key, label in labels
        if resource_counts.get(key, 0) > 0
    ]
    return " · ".join(parts) if parts else "구성 정보 없음"


def top_subdomains(domain: dict[str, Any]) -> str:
    items = sorted(
        domain.get("subdomains", []),
        key=lambda item: (-item.get("group_count", 0), item.get("tech_subdomain_label", "")),
    )[:3]
    if not items:
        return "세부 기술 정보 없음"
    return " · ".join(
        f"{item.get('tech_subdomain_label', '')} {item.get('group_count', 0)}"
        for item in items
    )


def top_strategies(domain: dict[str, Any]) -> str:
    items = (domain.get("strategies") or [])[:3]
    if not items:
        return "연결 전략 정보 없음"
    return " · ".join(item.get("label", "") for item in items)


def build_policy_summary(domain: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for group in sorted_groups(domain):
        policy = group.get("policy") or {}
        name = policy.get("policy_name")
        if not name:
            continue
        row = rows.setdefault(
            name,
            {
                "policy_id": policy.get("policy_id", name),
                "policy_name": name,
                "policy_order": policy.get("policy_order", 999),
                "group_count": 0,
                "content_count": 0,
                "buckets": set(),
            },
        )
        row["group_count"] += 1
        row["content_count"] += len(group.get("contents", []))
        bucket_label = (group.get("bucket") or {}).get("resource_category_label")
        if bucket_label:
            row["buckets"].add(bucket_label)
    result = []
    for row in rows.values():
        row["bucket_summary"] = " · ".join(sorted(row["buckets"]))
        result.append(row)
    return sorted(
        result,
        key=lambda row: (-row["group_count"], -row["content_count"], row["policy_order"], row["policy_name"]),
    )


def pick_group_evidence(group: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    contents = sorted(group.get("contents", []), key=lambda item: (item.get("display_order", 999), item.get("content_label", "")))
    if not contents:
        return None, None

    strength_rank = {"high": 3, "medium": 2, "low": 1}
    scored: list[tuple[tuple[int, int, int, int, int], dict[str, Any], dict[str, Any] | None]] = []

    for content in contents:
        evidence = content.get("primary_policy_evidence")
        quote = clean_quote_text((evidence or {}).get("plain_text"))
        summary = clean_display_text(
            (content.get("display") or {}).get("summary_text")
            or content.get("content_summary")
            or ""
        )
        has_primary = 1 if evidence and quote else 0
        evidence_count = int(content.get("evidence_count") or 0)
        strength = strength_rank.get((evidence or {}).get("evidence_strength"), 0)
        quote_len = len(quote)
        summary_len = len(summary)
        display_order = int(content.get("display_order") or 999)
        score = (has_primary, evidence_count, strength, quote_len + summary_len, -display_order)
        scored.append((score, content, evidence if has_primary else None))

    scored.sort(key=lambda item: item[0], reverse=True)
    _, picked_content, picked_evidence = scored[0]
    return picked_content, picked_evidence


def render_tech_nav(domains: list[dict[str, Any]]) -> str:
    items = []
    for domain in domains:
        items.append(
            f"""          <a class="tech-chip" href="#{esc(domain.get('tech_domain_id', ''))}">
            <strong>{esc(domain.get('tech_domain_label', ''))}</strong>
            <span>{esc(domain.get('policy_count', 0))}개 정책 · {esc(domain.get('group_count', 0))}개 과제</span>
          </a>"""
        )
    return "\n".join(items)


def render_policy_summary_list(domain: dict[str, Any]) -> str:
    items = []
    for row in build_policy_summary(domain):
        bucket_text = f" · {row['bucket_summary']}" if row["bucket_summary"] else ""
        items.append(
            f"""            <li>
              <strong><a class="matrix-link" href="./detail-policy.html#{esc(row['policy_id'])}">{esc(row['policy_name'])}</a></strong>
              <span>{esc(row['group_count'])}개 과제 · {esc(row['content_count'])}개 세부 조치{esc(bucket_text)}</span>
            </li>"""
        )
    return "\n".join(items)


def render_group_cards(domain: dict[str, Any]) -> str:
    cards = []
    for group in sorted_groups(domain):
        display = group.get("display") or {}
        policy = group.get("policy") or {}
        policy_id = policy.get("policy_id", "")
        bucket = group.get("bucket") or {}
        taxonomy = group.get("taxonomy") or {}
        subdomain = ((taxonomy.get("primary_tech_subdomain") or {}).get("label")) or "세부 기술 미기재"
        raw_title = display.get("title_text") or group.get("group_label") or "제목 없음"
        title = concise_label_text(raw_title)
        summary = build_task_summary(
            raw_title,
            display.get("summary_text") or group.get("group_summary") or "",
            bucket.get("resource_category_label"),
        )
        contents = sorted(
            group.get("contents", []),
            key=lambda item: (item.get("display_order", 999), item.get("content_label", "")),
        )
        content_items = []
        for content in contents[:2]:
            content_display = content.get("display") or {}
            raw_content_title = content_display.get("title_text") or content.get("content_label") or "세부 조치"
            content_title = concise_label_text(raw_content_title)
            content_summary = build_content_summary(
                raw_content_title,
                content_display.get("summary_text") or content.get("content_summary") or "",
            )
            content_items.append(
                f"""                <li>
                  <strong>{esc(content_title)}</strong>
                  <span>{esc(compact_text(content_summary))}</span>
                </li>"""
            )

        picked_content, evidence = pick_group_evidence(group)
        if evidence:
            quote = clean_quote_text(evidence.get("plain_text"))
            document = evidence.get("document") or {}
            source_line = (
                f"출처 · {document.get('normalized_title', policy.get('policy_name', '정책 문서'))} · "
                f"{humanize_location(evidence.get('location_value', ''))} · "
                f"{document.get('issued_date', '')}"
            )
        else:
            picked_display = (picked_content or {}).get("display") or {}
            quote = clean_quote_text(
                picked_display.get("summary_text")
                or (picked_content or {}).get("content_summary")
                or summary
            )
            source_line = f"출처 · {policy.get('policy_name', '정책 문서')}"

        cards.append(
            f"""          <article class="task-card">
            <div class="task-head">
              <div>
                <h3><a class="matrix-link" href="./detail-policy.html#{esc(policy_tech_anchor(policy_id, domain.get('tech_domain_id', '')))}">{esc(title)}</a></h3>
                <p class="task-meta"><a class="matrix-link" href="./detail-policy.html#{esc(policy_id)}">{esc(policy.get('policy_name', ''))}</a> · {esc(bucket.get('resource_category_label', ''))} · {esc(subdomain)}</p>
              </div>
              <span class="task-count">{esc(len(contents))}개 세부 조치</span>
            </div>
            <p class="task-summary">{esc(compact_text(summary))}</p>
            <div class="evidence-block">
              <p class="evidence-label">대표 근거</p>
              <blockquote class="evidence-quote">{esc(quote)}</blockquote>
              <p class="source-caption">{esc(source_line)}</p>
            </div>
            <ul class="content-list">
{chr(10).join(content_items)}
            </ul>
          </article>"""
        )
    return "\n".join(cards)


def render_tech_section(domain: dict[str, Any]) -> str:
    mix_text = summarize_resource_mix(domain.get("resource_category_counts") or {})
    summary = (
        f"{domain.get('policy_count', 0)}개 정책이 연결돼 있고 "
        f"{domain.get('group_count', 0)}개 주요 과제와 {domain.get('content_count', 0)}개 세부 조치가 이 기술에 매핑돼 있다. "
        f"지원 유형 구성: {mix_text}."
    )
    return f"""      <section id="{esc(domain.get('tech_domain_id', ''))}" class="panel tech-section">
        <div class="tech-section-head">
          <div class="title-stack">
            <p class="eyebrow">기술 영역</p>
            <h2>{esc(domain.get('tech_domain_label', ''))}</h2>
            <p class="page-summary">{esc(summary)}</p>
          </div>
          <div class="tech-metrics" aria-label="{esc(domain.get('tech_domain_label', ''))} 집계">
            <div class="metric-box">
              <strong>{esc(domain.get('policy_count', 0))}</strong>
              <span>연결 정책</span>
            </div>
            <div class="metric-box">
              <strong>{esc(domain.get('group_count', 0))}</strong>
              <span>주요 과제</span>
            </div>
            <div class="metric-box">
              <strong>{esc(domain.get('content_count', 0))}</strong>
              <span>세부 조치</span>
            </div>
          </div>
        </div>

        <div class="detail-pill-row">
          <span class="summary-pill">{esc(mix_text)}</span>
          <span class="summary-pill">{esc(top_subdomains(domain))}</span>
          <span class="summary-pill">{esc(top_strategies(domain))}</span>
        </div>

        <div class="detail-grid">
          <article class="detail-card">
            <div class="panel-head compact">
              <div>
                <p class="eyebrow">정책 분포</p>
                <h3>연결 정책</h3>
              </div>
            </div>
            <ul class="insight-list">
{render_policy_summary_list(domain)}
            </ul>
          </article>
          <article class="detail-card">
            <div class="panel-head compact">
              <div>
                <p class="eyebrow">핵심 포인트</p>
                <h3>우선 확인할 내용</h3>
              </div>
            </div>
            <ul class="signal-list">
              <li><strong>지원 유형</strong><span>{esc(mix_text)}</span></li>
              <li><strong>세부 기술</strong><span>{esc(top_subdomains(domain))}</span></li>
              <li><strong>연결 전략</strong><span>{esc(top_strategies(domain))}</span></li>
            </ul>
          </article>
        </div>

        <div class="task-grid">
{render_group_cards(domain)}
        </div>
      </section>"""


def summarize_bucket_labels(bucket_counts: dict[str, int]) -> str:
    ordered_labels = ["기술", "인프라·제도", "인재"]
    parts = [
        f"{label} {bucket_counts.get(label, 0)}건"
        for label in ordered_labels
        if bucket_counts.get(label, 0) > 0
    ]
    return " · ".join(parts) if parts else "지원 유형 정보 없음"


def build_policy_sections(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domain_order = {domain.get("tech_domain_id"): index for index, domain in enumerate(domains)}
    rows: dict[str, dict[str, Any]] = {}

    for domain in domains:
        for group in sorted_groups(domain):
            policy = group.get("policy") or {}
            policy_id = policy.get("policy_id")
            policy_name = policy.get("policy_name")
            if not policy_id or not policy_name:
                continue
            row = rows.setdefault(
                policy_id,
                {
                    "policy_id": policy_id,
                    "policy_name": policy_name,
                    "policy_order": policy.get("policy_order", 999),
                    "group_count": 0,
                    "content_count": 0,
                    "techs": {},
                    "bucket_counts": {},
                },
            )
            tech = row["techs"].setdefault(
                domain.get("tech_domain_id"),
                {
                    "tech_domain_id": domain.get("tech_domain_id"),
                    "tech_domain_label": domain.get("tech_domain_label"),
                    "display_order": domain_order.get(domain.get("tech_domain_id"), 999),
                    "group_count": 0,
                    "content_count": 0,
                    "groups": [],
                    "subdomains": {},
                },
            )
            tech["groups"].append(group)
            tech["group_count"] += 1
            tech["content_count"] += len(group.get("contents", []))
            row["group_count"] += 1
            row["content_count"] += len(group.get("contents", []))

            bucket_label = (group.get("bucket") or {}).get("resource_category_label")
            if bucket_label:
                row["bucket_counts"][bucket_label] = row["bucket_counts"].get(bucket_label, 0) + 1

            subdomain_label = ((group.get("taxonomy") or {}).get("primary_tech_subdomain") or {}).get("label")
            if subdomain_label:
                tech["subdomains"][subdomain_label] = tech["subdomains"].get(subdomain_label, 0) + 1

    result = []
    for row in rows.values():
        tech_list = []
        for tech in row["techs"].values():
            subdomain_items = sorted(
                tech["subdomains"].items(),
                key=lambda item: (-item[1], item[0]),
            )[:3]
            tech["top_subdomains"] = " · ".join(
                f"{label} {count}" for label, count in subdomain_items
            ) if subdomain_items else "세부 기술 정보 없음"
            tech_list.append(tech)
        tech_list.sort(
            key=lambda tech: (
                -tech["group_count"],
                -tech["content_count"],
                tech["display_order"],
                tech["tech_domain_label"],
            )
        )
        row["tech_list"] = tech_list
        row["tech_count"] = len(tech_list)
        row["mix_text"] = summarize_bucket_labels(row["bucket_counts"])
        result.append(row)

    return sorted(result, key=lambda row: (row["policy_order"], row["policy_name"]))


def policy_lead_text(row: dict[str, Any]) -> str:
    tech_list = row.get("tech_list", [])
    name = row.get("policy_name", "정책")
    particle = topic_particle(name)
    if not tech_list:
        return f"{name}{particle} 현재 연결된 기술이 확인되지 않는다."
    first = tech_list[0]["tech_domain_label"]
    if len(tech_list) == 1:
        return f"{name}{particle} {first}에 집중된다."
    if len(tech_list) == 2:
        second = tech_list[1]["tech_domain_label"]
        return f"{name}{particle} {first}에 가장 강하게 연결되며, {second}까지 확장된다."
    second = tech_list[1]["tech_domain_label"]
    third = tech_list[2]["tech_domain_label"]
    return f"{name}{particle} {first}을 중심으로 {second}·{third} 등 {len(tech_list)}개 기술에 분산된다."


def render_policy_nav(policy_rows: list[dict[str, Any]]) -> str:
    items = []
    for row in policy_rows:
        items.append(
            f"""          <a class="tech-chip" href="#{esc(row.get('policy_id', ''))}">
            <strong>{esc(row.get('policy_name', ''))}</strong>
            <span>{esc(row.get('tech_count', 0))}개 기술 · {esc(row.get('group_count', 0))}개 과제</span>
          </a>"""
        )
    return "\n".join(items)


def render_policy_distribution(row: dict[str, Any]) -> str:
    items = []
    for tech in row.get("tech_list", []):
        items.append(
            f"""            <li>
              <strong><a class="matrix-link" href="./detail-tech.html#{esc(tech.get('tech_domain_id', ''))}">{esc(tech.get('tech_domain_label', ''))}</a></strong>
              <span>{esc(tech.get('group_count', 0))}개 과제 · {esc(tech.get('content_count', 0))}개 세부 조치</span>
            </li>"""
        )
    return "\n".join(items)


def render_policy_clusters(row: dict[str, Any]) -> str:
    clusters = []
    for tech in row.get("tech_list", []):
        cards = []
        for group in tech.get("groups", []):
            display = group.get("display") or {}
            bucket = group.get("bucket") or {}
            taxonomy = group.get("taxonomy") or {}
            subdomain = ((taxonomy.get("primary_tech_subdomain") or {}).get("label")) or "세부 기술 미기재"
            raw_title = display.get("title_text") or group.get("group_label") or "제목 없음"
            title = concise_label_text(raw_title)
            summary = build_task_summary(
                raw_title,
                display.get("summary_text") or group.get("group_summary") or "",
                bucket.get("resource_category_label"),
            )
            contents = sorted(
                group.get("contents", []),
                key=lambda item: (item.get("display_order", 999), item.get("content_label", "")),
            )
            content_items = []
            for content in contents[:2]:
                content_display = content.get("display") or {}
                raw_content_title = content_display.get("title_text") or content.get("content_label") or "세부 조치"
                content_title = concise_label_text(raw_content_title)
                content_summary = build_content_summary(
                    raw_content_title,
                    content_display.get("summary_text") or content.get("content_summary") or "",
                )
                content_items.append(
                    f"""                  <li>
                    <strong>{esc(content_title)}</strong>
                    <span>{esc(compact_text(content_summary))}</span>
                  </li>"""
                )

            picked_content, evidence = pick_group_evidence(group)
            if evidence:
                quote = clean_quote_text(evidence.get("plain_text"))
                document = evidence.get("document") or {}
                source_line = (
                    f"출처 · {document.get('normalized_title', row.get('policy_name', '정책 문서'))} · "
                    f"{humanize_location(evidence.get('location_value', ''))} · "
                    f"{document.get('issued_date', '')}"
                )
            else:
                picked_display = (picked_content or {}).get("display") or {}
                quote = clean_quote_text(
                    picked_display.get("summary_text")
                    or (picked_content or {}).get("content_summary")
                    or summary
                )
                source_line = f"출처 · {row.get('policy_name', '정책 문서')}"

            cards.append(
                f"""            <article class="task-card">
              <div class="task-head">
                <div>
                  <h4>{esc(title)}</h4>
                  <p class="task-meta">{esc(bucket.get('resource_category_label', ''))} · {esc(subdomain)}</p>
                </div>
                <span class="task-count">{esc(len(contents))}개 세부 조치</span>
              </div>
              <p class="task-summary">{esc(compact_text(summary))}</p>
              <div class="evidence-block">
                <p class="evidence-label">대표 근거</p>
                <blockquote class="evidence-quote">{esc(quote)}</blockquote>
                <p class="source-caption">{esc(source_line)}</p>
              </div>
              <ul class="content-list">
{chr(10).join(content_items)}
              </ul>
            </article>"""
            )

        clusters.append(
            f"""        <section id="{esc(policy_tech_anchor(row.get('policy_id', ''), tech.get('tech_domain_id', '')))}" class="detail-card policy-cluster">
          <div class="cluster-head">
            <div>
              <p class="eyebrow">기술 분야</p>
              <h3><a class="matrix-link" href="./detail-tech.html#{esc(tech.get('tech_domain_id', ''))}">{esc(tech.get('tech_domain_label', ''))}</a></h3>
            </div>
            <span class="task-count">{esc(tech.get('group_count', 0))}개 과제 · {esc(tech.get('content_count', 0))}개 세부 조치</span>
          </div>
          <p class="cluster-copy">{esc(tech.get('top_subdomains', '세부 기술 정보 없음'))}</p>
          <div class="task-grid nested-task-grid">
{chr(10).join(cards)}
          </div>
        </section>"""
        )
    return "\n".join(clusters)


def render_policy_section(row: dict[str, Any]) -> str:
    return f"""      <section id="{esc(row.get('policy_id', ''))}" class="panel tech-section policy-section">
        <div class="tech-section-head">
          <div class="title-stack">
            <p class="eyebrow">정책 보고서</p>
            <h2>{esc(row.get('policy_name', ''))}</h2>
            <p class="page-summary">{esc(policy_lead_text(row))}</p>
          </div>
          <div class="tech-metrics" aria-label="{esc(row.get('policy_name', ''))} 집계">
            <div class="metric-box">
              <strong>{esc(row.get('tech_count', 0))}</strong>
              <span>연결 기술</span>
            </div>
            <div class="metric-box">
              <strong>{esc(row.get('group_count', 0))}</strong>
              <span>주요 과제</span>
            </div>
            <div class="metric-box">
              <strong>{esc(row.get('content_count', 0))}</strong>
              <span>세부 조치</span>
            </div>
          </div>
        </div>

        <div class="detail-pill-row">
          <span class="summary-pill">{esc(row.get('mix_text', '지원 유형 정보 없음'))}</span>
          <span class="summary-pill">{esc(' · '.join(f"{tech['tech_domain_label']} {tech['group_count']}" for tech in row.get('tech_list', [])[:3]))}</span>
        </div>

        <div class="detail-grid">
          <article class="detail-card">
            <div class="panel-head compact">
              <div>
                <p class="eyebrow">기술 분포</p>
                <h3>연결 기술 분포</h3>
              </div>
            </div>
            <ul class="insight-list">
{render_policy_distribution(row)}
            </ul>
          </article>
          <article class="detail-card">
            <div class="panel-head compact">
              <div>
                <p class="eyebrow">핵심 포인트</p>
                <h3>우선 확인할 기술</h3>
              </div>
            </div>
            <ul class="signal-list">
              <li><strong>지원 유형</strong><span>{esc(row.get('mix_text', '지원 유형 정보 없음'))}</span></li>
              <li><strong>상위 기술</strong><span>{esc(' · '.join(f"{tech['tech_domain_label']} {tech['group_count']}" for tech in row.get('tech_list', [])[:3]))}</span></li>
              <li><strong>연결 규모</strong><span>{esc(row.get('tech_count', 0))}개 기술 · {esc(row.get('group_count', 0))}개 과제 · {esc(row.get('content_count', 0))}개 세부 조치</span></li>
            </ul>
          </article>
        </div>

{render_policy_clusters(row)}
      </section>"""


def build_html(payload: dict[str, Any], domains: list[dict[str, Any]]) -> str:
    meta = payload.get("meta") or {}
    policy_rows = build_policy_rows(domains)
    tech_rows = build_tech_rows(domains)
    generated_at = format_generated_at(meta.get("generated_at", ""))
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>정책-기술 집중도 대시보드</title>
    <link rel="stylesheet" href="./briefing.css" />
  </head>
  <body>
    <main class="page-shell overview-page">
      <header class="report-header panel">
        <div class="title-stack">
          <p class="eyebrow">종합 현황</p>
          <h1>정책-기술 집중도 대시보드</h1>
          <p class="page-summary">{esc(summary_text(domains, policy_rows, tech_rows))}</p>
        </div>
        <div class="header-meta">
          <span class="summary-pill">{esc(generated_at)}</span>
        </div>
      </header>

      <section class="panel summary-panel">
        <div class="summary-ribbon" aria-label="대시보드 집계">
          {render_summary_pills(domains, policy_rows)}
        </div>
      </section>

      {render_matrix(domains, policy_rows)}

      <section class="insight-grid" aria-label="집중도 보조 요약">
{render_policy_focus(policy_rows)}
{render_tech_focus(tech_rows)}
      </section>
    </main>
  </body>
</html>
"""


def build_tech_detail_html(payload: dict[str, Any], domains: list[dict[str, Any]]) -> str:
    meta = payload.get("meta") or {}
    generated_at = format_generated_at(meta.get("generated_at", ""))
    sections = "\n".join(render_tech_section(domain) for domain in domains)
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>기술영역별 연결 정책</title>
    <link rel="stylesheet" href="./briefing.css" />
  </head>
  <body>
    <main class="page-shell detail-tech-page">
      <header class="report-header panel">
        <div class="title-stack">
          <p class="eyebrow">기술 영역</p>
          <h1>기술영역별 연결 정책</h1>
          <p class="page-summary">각 기술영역에 연결된 정책과 주요 과제를 기술별로 묶어 보여준다. 관련 정책과 대표 근거를 같은 흐름에서 확인할 수 있다.</p>
        </div>
        <div class="header-meta">
          <a class="summary-pill summary-link" href="./index.html">전체 대시보드로 돌아가기</a>
          <a class="summary-pill summary-link" href="./detail-policy.html">정책 기준으로 보기</a>
          <span class="summary-pill">{esc(generated_at)}</span>
        </div>
      </header>

      <section class="panel summary-panel">
        <div class="summary-ribbon" aria-label="기술 상세 이동">
{render_tech_nav(domains)}
        </div>
      </section>

{sections}
    </main>
  </body>
</html>
"""


def build_policy_detail_html(payload: dict[str, Any], domains: list[dict[str, Any]]) -> str:
    meta = payload.get("meta") or {}
    generated_at = format_generated_at(meta.get("generated_at", ""))
    policy_rows = build_policy_sections(domains)
    sections = "\n".join(render_policy_section(row) for row in policy_rows)
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>정책별 연결 기술</title>
    <link rel="stylesheet" href="./briefing.css" />
  </head>
  <body>
    <main class="page-shell detail-policy-page">
      <header class="report-header panel">
        <div class="title-stack">
          <p class="eyebrow">정책 보고서</p>
          <h1>정책별 연결 기술</h1>
          <p class="page-summary">각 정책이 어떤 기술에 연결되고 어디에 더 집중되는지 정책별로 보여준다. 기술 상세와 주요 과제를 같은 흐름에서 확인할 수 있다.</p>
        </div>
        <div class="header-meta">
          <a class="summary-pill summary-link" href="./index.html">전체 대시보드로 돌아가기</a>
          <a class="summary-pill summary-link" href="./detail-tech.html">기술 기준으로 보기</a>
          <span class="summary-pill">{esc(generated_at)}</span>
        </div>
      </header>

      <section class="panel summary-panel">
        <div class="summary-ribbon" aria-label="정책 상세 이동">
{render_policy_nav(policy_rows)}
        </div>
      </section>

{sections}
    </main>
  </body>
</html>
"""


def main() -> None:
    payload = load_payload()
    domains = active_domains(payload)
    if not domains:
        raise SystemExit("No active technology domains found in technology-lens.json")
    OUTPUT_PATH.write_text(build_html(payload, domains), encoding="utf-8")
    DETAIL_TECH_OUTPUT_PATH.write_text(build_tech_detail_html(payload, domains), encoding="utf-8")
    DETAIL_POLICY_OUTPUT_PATH.write_text(build_policy_detail_html(payload, domains), encoding="utf-8")


if __name__ == "__main__":
    main()
