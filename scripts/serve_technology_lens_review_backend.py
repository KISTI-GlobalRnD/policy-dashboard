#!/usr/bin/env python3
"""Run a lightweight backend for manual technology-lens review tasks."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote, urlparse


ALLOWED_DECISION_STATUSES = {"approved", "revised", "rejected", "deferred", "pending"}


def read_csv_rows(path: Path, required: Iterable[str] | None = None) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        if required is None:
            return [], []
        return list(required), []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if required is not None and fieldnames:
        for name in required:
            if name not in fieldnames:
                fieldnames.append(name)
    return fieldnames, rows


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


class TechnologyLensReviewService:
    """Provide read/write access to technology-lens review CSV + evidence from DB."""

    def __init__(self, decision_csv: Path, db_path: Path) -> None:
        self.decision_csv = decision_csv
        self.db_path = db_path
        self.lock = threading.Lock()

    def _load_db_rows(self, group_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            evidence_rows = cursor.execute(
                """
                SELECT
                    c.policy_item_content_id,
                    c.content_label,
                    c.content_statement,
                    l.link_role,
                    l.evidence_strength,
                    l.is_primary AS link_is_primary,
                    d.representation_type,
                    d.source_object_type,
                    d.source_object_id,
                    d.location_value,
                    d.plain_text,
                    doc.document_id AS source_document_id,
                    doc.normalized_title,
                    sa.page_no AS source_page_no,
                    sa.asset_path_or_url AS source_asset_path
                FROM policy_item_contents c
                LEFT JOIN policy_item_content_evidence_links l
                  ON l.policy_item_content_id = c.policy_item_content_id
                LEFT JOIN derived_representations d
                  ON d.derived_representation_id = l.derived_representation_id
                LEFT JOIN derived_to_source_asset_map m
                  ON m.derived_representation_id = d.derived_representation_id
                LEFT JOIN source_assets sa
                  ON sa.source_asset_id = m.source_asset_id
                LEFT JOIN documents doc
                  ON doc.document_id = sa.document_id
                WHERE c.policy_item_group_id = ?
                ORDER BY c.display_order, l.is_primary DESC, c.policy_item_content_id, l.link_role
                """,
                (group_id,),
            ).fetchall()

            member_rows = cursor.execute(
                """
                SELECT
                    gm.policy_item_id,
                    gm.member_role,
                    gm.is_representative,
                    gm.confidence,
                    i.item_label,
                    i.item_statement
                FROM policy_item_group_members gm
                JOIN policy_items i ON i.policy_item_id = gm.policy_item_id
                WHERE gm.policy_item_group_id = ?
                ORDER BY gm.is_representative DESC, gm.member_role, gm.policy_item_id
                """,
                (group_id,),
            ).fetchall()

        return [dict(row) for row in evidence_rows], [dict(row) for row in member_rows]

    def _read_decisions(self) -> tuple[list[str], list[dict[str, str]]]:
        required_fields = (
            "decision_key",
            "active_in_queue",
            "tech_domain_id",
            "tech_domain_label",
            "policy_item_group_id",
            "policy_id",
            "policy_name",
            "group_label",
            "group_summary",
            "decision_status",
            "reviewed_group_label",
            "reviewed_group_summary",
            "reviewed_group_description",
            "reviewer_name",
            "reviewer_notes",
        )
        return read_csv_rows(self.decision_csv, required=required_fields)

    def get_decision_rows(self) -> list[dict[str, str]]:
        _, rows = self._read_decisions()
        return rows

    def get_task(self, decision_key: str) -> dict[str, Any] | None:
        rows = self.get_decision_rows()
        for row in rows:
            if row.get("decision_key") == decision_key:
                return self._decorate_task(row)
        return None

    def list_tasks(
        self,
        status: str | None = None,
        tech_domain_id: str | None = None,
        policy_id: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.get_decision_rows()
        normalized_query = normalize_text(query or "").lower() if query else ""

        filtered: list[dict[str, str]] = []
        for row in rows:
            if status:
                if (row.get("decision_status") or "pending").strip().lower() != status:
                    continue
            if tech_domain_id and row.get("tech_domain_id") != tech_domain_id:
                continue
            if policy_id and row.get("policy_id") != policy_id:
                continue
            if normalized_query:
                candidates = " ".join(
                    [
                        normalize_text(row.get("group_label", "")),
                        normalize_text(row.get("group_summary", "")),
                        normalize_text(row.get("policy_name", "")),
                        normalize_text(row.get("tech_domain_label", "")),
                        normalize_text(row.get("reviewer_notes", "")),
                    ]
                ).lower()
                if normalized_query not in candidates:
                    continue
            filtered.append(row)

        filtered.sort(
            key=lambda row: (
                to_int(row.get("priority_rank", 999999), 999999),
                to_int(row.get("tech_domain_display_order", 999), 999),
                to_int(row.get("policy_order", 9999), 9999),
                row.get("decision_key", ""),
            )
        )

        return [self._decorate_task(row) for row in filtered]

    def _decorate_task(self, row: dict[str, str]) -> dict[str, Any]:
        group_id = row.get("policy_item_group_id", "")
        if not group_id:
            return dict(row)

        evidence_rows, member_rows = self._load_db_rows(group_id)
        return {
            **row,
            "evidence": evidence_rows,
            "member_items": member_rows,
            "evidence_count": str(len(evidence_rows)),
        }

    def update_decision(self, decision_key: str, payload: dict[str, str]) -> dict[str, Any]:
        with self.lock:
            fieldnames, rows = self._read_decisions()
            if not rows:
                raise KeyError(f"Decision row not found: {decision_key}")

            status = (payload.get("decision_status", "") or "").strip().lower()
            if status and status not in ALLOWED_DECISION_STATUSES:
                raise ValueError(f"Invalid decision_status: {status}")

            matched = False
            for row in rows:
                if row.get("decision_key") != decision_key:
                    continue
                matched = True
                if status:
                    row["decision_status"] = status

                for field in (
                    "reviewed_group_label",
                    "reviewed_group_summary",
                    "reviewed_group_description",
                    "reviewer_name",
                    "reviewer_notes",
                ):
                    if field in payload:
                        row[field] = (payload[field] or "").strip()
                break

            if not matched:
                raise KeyError(f"Decision row not found: {decision_key}")

            write_csv_rows(self.decision_csv, rows, fieldnames)

        updated = self.get_task(decision_key)
        if updated is None:
            raise RuntimeError(f"Failed to reload updated decision: {decision_key}")
        return updated

    def status_summary(self) -> dict[str, Any]:
        rows = self.get_decision_rows()
        status_counts: dict[str, int] = {}
        for row in rows:
            status = (row.get("decision_status") or "pending").strip().lower() or "pending"
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "total": len(rows),
            "status_counts": status_counts,
        }


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    raw = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(raw)


class ReviewBackendHandler(BaseHTTPRequestHandler):
    service: TechnologyLensReviewService

    def _json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _handle_error(self, status: int, message: str) -> None:
        json_response(self, {"error": message}, status=status)

    def do_OPTIONS(self) -> None:  # pragma: no cover - browser preflight compatibility
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _set_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        if path in {"", "/", "/ui"}:
            self._serve_ui()
            return

        if path == "/api/health":
            payload = {
                "ok": True,
                "db_path": str(self.service.db_path),
                "decision_csv": str(self.service.decision_csv),
                "summary": self.service.status_summary(),
            }
            return json_response(self, payload)

        if path == "/api/review-tasks":
            status = (query.get("status", [""],)[0] or "").strip().lower() or None
            tech_domain_id = (query.get("tech_domain_id", [""],)[0] or "").strip() or None
            policy_id = (query.get("policy_id", [""],)[0] or "").strip() or None
            search_query = (query.get("q", [""],)[0] or "").strip()

            items = self.service.list_tasks(
                status=status,
                tech_domain_id=tech_domain_id,
                policy_id=policy_id,
                query=search_query,
            )
            payload = {
                "items": items,
                "count": len(items),
                "summary": self.service.status_summary(),
            }
            return json_response(self, payload)

        if path.startswith("/api/review-tasks/"):
            decision_key = unquote(path.removeprefix("/api/review-tasks/"))
            task = self.service.get_task(decision_key)
            if task is None:
                return self._handle_error(404, f"Task not found: {decision_key}")
            return json_response(self, task)

        self._handle_error(404, f"Unknown endpoint: {self.path}")

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path.startswith("/api/review-tasks/"):
            return self._handle_error(404, f"Unknown endpoint: {self.path}")

        decision_key = unquote(path.removeprefix("/api/review-tasks/"))

        try:
            payload = self._json_body()
        except json.JSONDecodeError:
            return self._handle_error(400, "Invalid JSON payload")

        try:
            task = self.service.update_decision(decision_key, payload)
        except KeyError as error:
            return self._handle_error(404, str(error))
        except (ValueError, TypeError) as error:
            return self._handle_error(400, str(error))

        json_response(
            self,
            {
                "updated": True,
                "item": task,
            },
        )

    def _serve_ui(self) -> None:
        html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Technology Lens Review</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 20px; color: #1d1d1f; }
    h1 { margin: 0 0 10px 0; }
    .toolbar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
    .toolbar label { display: flex; flex-direction: column; font-size: 12px; color: #444; }
    button, select, input, textarea { font: inherit; }
    .task { border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin-bottom: 12px; }
    .task-header { display: grid; grid-template-columns: 1fr auto; gap: 10px; }
    .badge { padding: 3px 8px; border-radius: 999px; background: #eef; font-size: 12px; }
    .row { display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 8px; }
    .row .full { grid-column: 1 / -1; }
    textarea { width: 100%; min-height: 62px; }
    .meta { font-size: 13px; color: #555; margin: 6px 0; }
    .evidence { margin-top: 8px; background: #f8f8fc; padding: 8px; border-radius: 8px; }
    .evidence-item { margin-bottom: 8px; }
    .status { font-weight: bold; }
  </style>
</head>
<body>
  <h1>Technology Lens Review Console</h1>
  <div class="toolbar">
    <label>상태
      <select id="statusFilter">
        <option value="">전체</option>
        <option value="pending">pending</option>
        <option value="approved">approved</option>
        <option value="revised">revised</option>
        <option value="rejected">rejected</option>
        <option value="deferred">deferred</option>
      </select>
    </label>
    <label>검색
      <input id="searchQuery" type="text" placeholder="그룹 라벨/정책명/도메인" />
    </label>
    <button id="reload">새로고침</button>
  </div>
  <div id="summary" class="meta"></div>
  <div id="taskList"></div>

  <script>
    const statusFilter = document.getElementById('statusFilter');
    const searchQuery = document.getElementById('searchQuery');
    const summary = document.getElementById('summary');
    const taskList = document.getElementById('taskList');

    async function fetchJson(url, options = {}) {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `Request failed: ${response.status}`);
      }
      return response.json();
    }

    function escapeHtml(value) {
      const div = document.createElement('div');
      div.textContent = value || '';
      return div.innerHTML;
    }

    function escapeAttr(value) {
      return String(value || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function evidenceToText(item) {
      const text = item.plain_text || item.content_statement || '';
      if (!text) {
        return '(근거 텍스트 없음)';
      }
      return `${item.source_document_id || ''} ${item.normalized_title || ''} ${item.source_page_no || ''}`.trim() + `\n${text}`;
    }

    function render(tasks) {
      taskList.innerHTML = '';
      tasks.forEach(task => {
        const wrapper = document.createElement('section');
        wrapper.className = 'task';

        const header = document.createElement('div');
        header.className = 'task-header';
        header.innerHTML = `<div>
          <h3 style="margin:0">${escapeHtml(task.group_label || '')}</h3>
          <div class="meta">${escapeHtml(task.tech_domain_label || '')} / ${escapeHtml(task.policy_name || '')} / ${escapeHtml(task.decision_key || '')}</div>
        </div>
        <div class="badge">${task.decision_status || 'pending'}</div>`;
        wrapper.appendChild(header);

        const summaryRow = document.createElement('div');
        summaryRow.className = 'meta';
        summaryRow.textContent = task.group_summary || '';
        wrapper.appendChild(summaryRow);

        const form = document.createElement('div');
        form.className = 'row';
        form.innerHTML = `
          <label>결정 상태
            <select data-key="${escapeAttr(task.decision_key)}" data-field="decision_status">
              <option value="pending" ${task.decision_status === 'pending' ? 'selected' : ''}>pending</option>
              <option value="approved" ${task.decision_status === 'approved' ? 'selected' : ''}>approved</option>
              <option value="revised" ${task.decision_status === 'revised' ? 'selected' : ''}>revised</option>
              <option value="rejected" ${task.decision_status === 'rejected' ? 'selected' : ''}>rejected</option>
              <option value="deferred" ${task.decision_status === 'deferred' ? 'selected' : ''}>deferred</option>
            </select>
          </label>
          <label>검수자
            <input data-key="${escapeAttr(task.decision_key)}" data-field="reviewer_name" value="${escapeAttr(task.reviewer_name)}" />
          </label>
          <label class="full">수정 라벨
            <textarea data-key="${escapeAttr(task.decision_key)}" data-field="reviewed_group_label">${escapeHtml(task.reviewed_group_label || '')}</textarea>
          </label>
          <label class="full">수정 요약
            <textarea data-key="${escapeAttr(task.decision_key)}" data-field="reviewed_group_summary">${escapeHtml(task.reviewed_group_summary || '')}</textarea>
          </label>
          <label class="full">수정 설명
            <textarea data-key="${escapeAttr(task.decision_key)}" data-field="reviewed_group_description">${escapeHtml(task.reviewed_group_description || '')}</textarea>
          </label>
          <label class="full">검수 노트
            <textarea data-key="${escapeAttr(task.decision_key)}" data-field="reviewer_notes">${escapeHtml(task.reviewer_notes || '')}</textarea>
          </label>
          <div class="full"><button data-action="save" data-key="${escapeAttr(task.decision_key)}">저장</button></div>
        `;
        wrapper.appendChild(form);

        const evidence = document.createElement('div');
        evidence.className = 'evidence';
        const evidenceItems = (task.evidence || []).slice(0, 5).map(item => {
          const raw = evidenceToText(item);
          return `<div class="evidence-item"><strong>${escapeHtml(item.content_label || '')}</strong><pre>${escapeHtml(raw)}</pre></div>`;
        }).join('');
        evidence.innerHTML = `<strong>근거</strong>${evidenceItems || '<div>(근거가 없습니다.)</div>'}`;
        wrapper.appendChild(evidence);

        taskList.appendChild(wrapper);
      });
    }

    async function loadTasks() {
      const query = new URLSearchParams();
      if (statusFilter.value) query.set('status', statusFilter.value);
      if (searchQuery.value.trim()) query.set('q', searchQuery.value.trim());
      const url = `/api/review-tasks?${query.toString()}`;
      const payload = await fetchJson(url);
      const summaryItems = Object.entries(payload.summary.status_counts || {}).map(([k, v]) => `${k}: ${v}`).join(' / ');
      summary.textContent = `총 ${payload.summary.total}건 / ${payload.count}건 표시 (${summaryItems})`;
      render(payload.items);
    }

    async function saveTask(decisionKey) {
      const fields = document.querySelectorAll(`[data-key="${CSS.escape(decisionKey)}"]`);
      const payload = {};
      fields.forEach((field) => {
        const key = field.dataset.field;
        payload[key] = field.value;
      });

      const response = await fetchJson(`/api/review-tasks/${encodeURIComponent(decisionKey)}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      const updated = response.item;
      await loadTasks();
      return updated;
    }

    taskList.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-action="save"]');
      if (!button) return;
      const decisionKey = button.dataset.key;
      try {
        button.disabled = true;
        await saveTask(decisionKey);
      } finally {
        button.disabled = false;
      }
    });

    statusFilter.addEventListener('change', loadTasks);
    searchQuery.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        loadTasks();
      }
    });
    document.getElementById('reload').addEventListener('click', loadTasks);

    loadTasks().catch((error) => {
      summary.textContent = error.message || '요청 실패';
    });
  </script>
</body>
</html>
"""

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", default="qa/ontology/review_queues/technology-lens-review-decisions.csv")
    parser.add_argument("--db-path", default="work/04_ontology/ontology.sqlite")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = TechnologyLensReviewService(Path(args.decision_csv), Path(args.db_path))

    handler = ReviewBackendHandler
    handler.service = service

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Technology lens review backend running at http://{args.host}:{args.port}/")
    print(f"decision csv: {service.decision_csv}")
    print(f"ontology db: {service.db_path}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
