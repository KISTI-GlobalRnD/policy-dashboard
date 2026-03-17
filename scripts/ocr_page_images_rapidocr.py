#!/usr/bin/env python3
"""Run Korean OCR on rendered page images using RapidOCR."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path


def ensure_rapidocr(loader_root: Path) -> Path:
    wheel_dir = loader_root / "wheels"
    lib_dir = loader_root / "lib"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)

    packages = {
        "rapidocr_onnxruntime": lambda fn: fn.endswith("py3-none-any.whl"),
        "onnxruntime": lambda fn: "cp312-cp312-manylinux_2_27_x86_64" in fn and fn.endswith(".whl"),
        "opencv_python_headless": lambda fn: "cp37-abi3-manylinux_2_28_x86_64" in fn and fn.endswith(".whl"),
        "numpy": lambda fn: "cp312-cp312-manylinux_2_27_x86_64" in fn and fn.endswith(".whl"),
        "Pillow": lambda fn: "cp312-cp312-manylinux_2_27_x86_64" in fn and fn.endswith(".whl"),
        "pyclipper": lambda fn: "cp312-cp312-manylinux2014_x86_64" in fn and fn.endswith(".whl"),
        "Shapely": lambda fn: "cp312-cp312-manylinux2014_x86_64" in fn and fn.endswith(".whl"),
        "PyYAML": lambda fn: "cp312-cp312-manylinux2014_x86_64" in fn and fn.endswith(".whl"),
        "six": lambda fn: fn.endswith("py2.py3-none-any.whl"),
        "tqdm": lambda fn: fn.endswith("py3-none-any.whl"),
    }

    for pkg, matcher in packages.items():
        marker = lib_dir / f".done_{pkg}"
        if marker.exists():
            continue
        meta = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json"))
        match = None
        for item in meta["urls"]:
            filename = item["filename"]
            if matcher(filename):
                match = (filename, item["url"])
                break
        if match is None:
            raise RuntimeError(f"No compatible wheel found for {pkg}")
        filename, url = match
        wheel_path = wheel_dir / filename
        if not wheel_path.exists():
            urllib.request.urlretrieve(url, wheel_path)
        with zipfile.ZipFile(wheel_path) as archive:
            archive.extractall(lib_dir)
        marker.write_text("ok", encoding="utf-8")

    sys.path.insert(0, str(lib_dir))
    return lib_dir


def ensure_korean_model(models_dir: Path) -> tuple[Path, Path]:
    models_dir.mkdir(parents=True, exist_ok=True)
    rec_model = models_dir / "korean_PP-OCRv5_rec_mobile_infer.onnx"
    rec_dict = models_dir / "ppocrv5_korean_dict.txt"

    if not rec_model.exists():
        urllib.request.urlretrieve(
            "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.7.0/onnx/PP-OCRv5/rec/korean_PP-OCRv5_rec_mobile_infer.onnx",
            rec_model,
        )
    if not rec_dict.exists():
        urllib.request.urlretrieve(
            "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.7.0/paddle/PP-OCRv5/rec/korean_PP-OCRv5_rec_mobile_infer/ppocrv5_korean_dict.txt",
            rec_dict,
        )

    return rec_model, rec_dict


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def page_no_from_name(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    if not match:
        raise ValueError(f"Cannot derive page number from {path.name}")
    return int(match.group(1))


def bbox_sort_key(bbox: object) -> tuple[float, float]:
    if isinstance(bbox, list) and bbox:
        first = bbox[0]
        if isinstance(first, list):
            xs = [float(point[0]) for point in bbox if isinstance(point, list) and len(point) >= 2]
            ys = [float(point[1]) for point in bbox if isinstance(point, list) and len(point) >= 2]
            if xs and ys:
                return min(ys), min(xs)
        if len(bbox) >= 4:
            return float(bbox[1]), float(bbox[0])
    return 0.0, 0.0


def build_markdown_text(page_records: list[dict]) -> str:
    parts = []
    for page in page_records:
        parts.append(f"<!-- page: {page['page_no']} -->\n{clean_text(page.get('text', ''))}\n")
    return "\n".join(parts).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    loader_root = out_root / "tmp" / "rapidocr_loader"
    ensure_rapidocr(loader_root)
    models_dir = loader_root / "models"
    rec_model, rec_dict = ensure_korean_model(models_dir)

    from rapidocr_onnxruntime import RapidOCR  # type: ignore

    engine = RapidOCR(
        rec_model_path=str(rec_model),
        rec_keys_path=str(rec_dict),
        intra_op_num_threads=1,
        inter_op_num_threads=1,
    )

    assets_dir = out_root / "work/02_structured-extraction/figures/assets" / args.document_id
    text_dir = out_root / "work/02_structured-extraction/text"
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"

    page_images = sorted(assets_dir.glob("page_*.png"))
    if not page_images:
        raise FileNotFoundError(f"No page images found in {assets_dir}")

    blocks = []
    page_records = []
    page_layout = []
    block_order = 0

    for image_path in page_images:
        page_no = page_no_from_name(image_path)
        result, _ = engine(str(image_path))
        lines = []
        page_evidences = []
        if result:
            for item in result:
                if len(item) < 3:
                    continue
                bbox, text, score = item
                text = str(text).strip()
                if not text:
                    continue
                block_order += 1
                evidence = {
                    "evidence_id": f"EVD-{args.document_id}-{block_order:05d}",
                    "document_id": args.document_id,
                    "page_no_or_sheet_name": page_no,
                    "block_order": block_order,
                    "block_type": "ocr_line",
                    "text": text,
                    "bbox": bbox,
                    "extraction_method": "rapidocr-korean-v5",
                    "extraction_confidence": float(score),
                    "page_no": page_no,
                }
                blocks.append(evidence)
                page_evidences.append(evidence)
                lines.append(
                    {
                        "evidence_id": evidence["evidence_id"],
                        "bbox": bbox,
                        "score": float(score),
                    }
                )
        sorted_page_evidences = sorted(page_evidences, key=lambda row: bbox_sort_key(row.get("bbox")))
        page_text = clean_text("\n".join(row["text"] for row in sorted_page_evidences))
        avg_confidence = (
            sum(float(row["extraction_confidence"]) for row in sorted_page_evidences) / len(sorted_page_evidences)
            if sorted_page_evidences
            else None
        )
        page_records.append(
            {
                "document_id": args.document_id,
                "page_no": page_no,
                "text": page_text,
                "line_count": len(sorted_page_evidences),
                "average_confidence": avg_confidence,
                "extraction_method": "rapidocr-korean-v5-line-aggregation",
                "extraction_confidence": "medium",
            }
        )
        page_layout.append(
            {
                "document_id": args.document_id,
                "page_no": page_no,
                "blocks": lines,
            }
        )

    text_path = text_dir / f"{args.document_id}_blocks.json"
    pages_path = text_dir / f"{args.document_id}_pages.json"
    markdown_path = text_dir / f"{args.document_id}.md"
    layout_path = layout_dir / f"{args.document_id}_ocr_layout.json"
    write_json(text_path, blocks)
    write_json(pages_path, page_records)
    write_text(markdown_path, build_markdown_text(page_records))
    write_json(layout_path, page_layout)

    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "document_id": args.document_id,
            "registry_id": args.registry_id,
            "source_rel_path": "",
            "internal_path": "",
            "source_format": "pdf",
            "page_count_or_sheet_count": len(page_images),
        }

    manifest.update(
        {
            "registry_id": args.registry_id,
            "extraction_run_id": "pilot-gs-001-korean-ocr-v2",
            "processing_status": "partial_table_pending",
            "quality_notes": [
                "Page images were rendered and then OCRed using RapidOCR with a Korean recognition model.",
                "Text blocks are line-level OCR outputs with bounding boxes and confidence scores.",
                "Page-level OCR text and markdown were aggregated from line blocks for manual review.",
                "Table structure is not yet reconstructed; further table parsing is still required.",
            ],
            "text_block_count": len(blocks),
            "text_output_path": str(text_path.relative_to(out_root)),
            "page_text_path": str(pages_path.relative_to(out_root)),
            "markdown_path": str(markdown_path.relative_to(out_root)),
            "layout_output_path": str(layout_path.relative_to(out_root)),
        }
    )
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
