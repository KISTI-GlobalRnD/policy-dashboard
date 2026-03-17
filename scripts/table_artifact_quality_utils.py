"""Shared heuristics for classifying extracted table artifacts."""

from __future__ import annotations

FRONT_MATTER_TOKENS = [
    "의안번호",
    "제 출 자",
    "제출 연월일",
    "의결사항",
    "심 의",
    "심의",
    "과학기술관계장관회의",
]


def extract_preview_from_cell_matrix(cell_matrix: list[list[object]]) -> str:
    for row in cell_matrix:
        values = [str(cell).strip() for cell in row if cell not in (None, "")]
        if values:
            return " | ".join(values[:4])[:200]
    return ""


def looks_like_front_matter(preview: str) -> bool:
    compact = preview.replace(" ", "")
    return any(token.replace(" ", "") in compact for token in FRONT_MATTER_TOKENS)


def looks_like_heading_box(preview: str) -> bool:
    stripped = preview.strip()
    compact = stripped.replace(" ", "")
    if not stripped:
        return False
    if stripped.startswith("<") and stripped.endswith(">"):
        return True
    if stripped.startswith(("Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "◇", "◈", "◆")):
        return True
    if stripped.startswith(("(전략", "(비전", "(목표", "비전", "목표")):
        return True
    if compact.startswith(("Ⅰ.", "Ⅱ.", "Ⅲ.", "Ⅳ.")):
        return True
    return False


def classify_json_table(
    rows: int,
    cols: int,
    preview: str,
    source_format: str,
    treat_as_char: str,
    text_wrap: str,
) -> tuple[str, str]:
    compact_preview = preview.replace(" ", "")
    if not compact_preview:
        return "layout_false_positive", "empty_table_box"

    if source_format in {"hwpx", "hwp"}:
        if looks_like_front_matter(preview):
            return "layout_false_positive", "front_matter_table"
        if rows == 1 and cols == 1:
            return "layout_false_positive", "single_cell_layout_box"
        if rows == 1 and cols <= 3:
            return "layout_false_positive", "single_row_layout_box"
        if rows <= 3 and cols <= 3 and looks_like_heading_box(preview):
            return "layout_false_positive", "heading_box"
        if text_wrap == "IN_FRONT_OF_TEXT" and treat_as_char == "0":
            return "layout_false_positive", "floating_layout_box"
        if rows >= 3 and cols >= 4:
            return "structured_table", "hwpx_matrix_table"
        if rows >= 4 and cols >= 2 and any(
            token in compact_preview for token in ["구분", "%", "202", "20’", "20'", "단계", "기존", "개선"]
        ):
            return "structured_table", "hwpx_grid_table"
        if cols == 1 and rows >= 3:
            return "review_required", "single_column_info_box"
        if rows >= 3 and cols >= 2:
            return "review_required", "hwpx_needs_manual_review"
        return "layout_false_positive", "small_hwpx_layout_box"

    if rows == 1 and cols <= 3:
        return "layout_false_positive", "single_row_small_box"
    if rows <= 2 and cols >= 8:
        return "fragment_or_broken", "wide_text_fragment"
    if any(token in compact_preview for token in ["시기", "상반기", "하반기"]) and rows <= 5:
        return "multi_page_fragment", "timeline_fragment"
    if rows >= 3 and cols >= 2:
        return "structured_table", "shape_based"
    return "review_required", "needs_manual_review"


def classify_table_payload(table: dict, source_format: str) -> tuple[str, str]:
    shape = table.get("table_shape", {})
    rows = int(shape.get("rows", 0) or 0)
    cols = int(shape.get("cols", 0) or 0)
    preview = extract_preview_from_cell_matrix(table.get("cell_matrix") or [])
    treat_as_char = str(table.get("treat_as_char", ""))
    text_wrap = str(table.get("text_wrap", ""))
    return classify_json_table(rows, cols, preview, source_format, treat_as_char, text_wrap)
