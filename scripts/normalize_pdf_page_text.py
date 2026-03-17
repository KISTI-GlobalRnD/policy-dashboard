#!/usr/bin/env python3
"""Normalize pure text for a text-based PDF using bbox blocks as the primary source.

Text paragraphs are reconstructed from PyMuPDF bbox blocks.
Markdown tables are preserved separately from PyMuPDF4LLM page chunks.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


FOOTER_PATTERN = re.compile(r"^[-–—]?\s*\d+\s*[-–—]?$")
NUMBERED_HEADING_PATTERN = re.compile(r"^\d+[.)]\s*\S")
ROMAN_HEADING_PATTERN = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+(?:[.)]\s*|\s+)")
CIRCLED_MARKERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳❶❷❸❹❺❻❼❽❾❿"
CIRCLED_HEADING_PATTERN = re.compile(rf"^[{CIRCLED_MARKERS}]\s*\S")
BULLET_PATTERN = re.compile(r"^(?:[-*]+|ㅇ|□|▪|•|➊|➋|➌|➍|➎|➏|➐|➑|➒|➓|⇨)\s*")
MARKER_ONLY_PATTERN = re.compile(r"^[❶-❿➊➋➌➍➎➏➐➑➒➓ㅇ□▪•*\-]+(?:\s+[❶-❿➊➋➌➍➎➏➐➑➒➓ㅇ□▪•*\-]+)*$")
NOISE_MARKERS = set("❶❷❸❹❺❻❼❽❾❿➊➋➌➍➎➏➐➑➒➓ㅇ□▪•*-")
STRONG_ENDING_PATTERN = re.compile(r"[.!?:;|]$")
DATE_NOTE_PATTERN = re.compile(r"^\(.*[’']?\d{2}.*\)$")
PURE_DATE_PATTERN = re.compile(r"^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.$")
HEADING_PREFIX_NORMALIZER = re.compile(r"^\(\d+\)\s*")
STAR_NOTE_PATTERN = re.compile(r"^\*{1,3}\s*\S")
INLINE_DOT_AFTER_SPACE_PATTERN = re.compile(r"(?<=[가-힣A-Za-z0-9])([·․･])\s+(?=[가-힣A-Za-z0-9])")
INLINE_DOT_BEFORE_SPACE_PATTERN = re.compile(r"(?<=[가-힣A-Za-z0-9])\s+([·․･])(?=[가-힣A-Za-z0-9])")
INLINE_SECTION_MARKER_SPLIT_PATTERN = re.compile(rf"(?<=\S)\s+(?=(?:[{CIRCLED_MARKERS}])\s*\()")
LOW_RISK_TEXT_REPLACEMENTS = [
    ("성장전략TF", "성장전략 TF"),
    ("초혁신경제15대프로젝트", "초혁신경제 15대 프로젝트"),
    ("의료AI", "의료 AI"),
    ("AI반도체", "AI 반도체"),
    ("AI바이오", "AI 바이오"),
    ("임상3상", "임상 3상"),
    ("기존ICT", "기존 ICT"),
    ("범장르AI", "범장르 AI"),
    ("바이오헬스분야AI", "바이오헬스분야 AI"),
    ("AI신약개발지원", "AI 신약개발 지원"),
    ("장르별AI", "장르별 AI"),
    ("스타트업이AI를활용", "스타트업이 AI를 활용"),
    ("매년AI 콘텐츠", "매년 AI 콘텐츠"),
    ("범장르및장르별AI", "범장르및장르별 AI"),
    ("통해AI·디지탈", "통해 AI·디지탈"),
    ("있는AI·디지털", "있는 AI·디지털"),
    ("에서AI 혁신이가속화", "에서 AI 혁신이 가속화"),
    ("해외거점기관을통한R&D", "해외거점기관을 통한 R&D"),
    ("및지자체의견", "및 지자체의견"),
    ("현장방문및민관협의체", "현장방문 및 민관협의체"),
    ("네트워킹등지원", "네트워킹 등 지원"),
    ("글로벌진출모델및성과창출", "글로벌진출모델 및 성과창출"),
    ("통해 AI·디지탈분야성과창출", "통해 AI·디지탈분야 성과창출"),
    ("활용하여창의적아이디어로쉽게게임", "활용하여 창의적아이디어로쉽게 게임"),
    ("에도전하도록AI 도구구독비지원신설", "에도전하도록 AI 도구구독비지원신설"),
    ("콘텐츠창제작전문인력1.2천명을양성하여", "콘텐츠창제작전문인력 1.2천명을양성하여"),
    ("가속화될것으로기대", "가속화될것으로 기대"),
    ("전문가의견등을통해", "전문가의견 등을 통해"),
    ("관계부처및", "관계부처 및"),
    ("부처업계간담회", "부처 업계간담회"),
    ("지자체및업계건의등", "지자체 및 업계건의 등"),
    ("빅데이터등첨단기술활용기반을", "빅데이터 등 첨단기술 활용기반을"),
    ("확충하고민간투자연계지원강화하여", "확충하고 민간투자 연계 지원 강화하여"),
    ("조성하고민간투자연계지원강화하여", "조성하고 민간투자 연계 지원 강화하여"),
    ("관계부처및유관협회및기관을포함하여", "관계부처 및 유관협회 및 기관을 포함하여"),
    ("확대및성공사례확산을통해", "확대 및 성공사례 확산을 통해"),
    ("의료기술과새롭게성장하고있는", "의료기술과 새롭게 성장하고있는"),
    ("의료기기를융합", "의료기기를 융합"),
    ("글로벌진출모델 ", "글로벌진출 모델 "),
    ("범장르및장르별 AI", "범장르 및 장르별 AI"),
    ("창의적아이디어로쉽게", "창의적 아이디어로 쉽게"),
    ("AI 도구구독비지원신설", "AI 도구 구독비 지원 신설"),
    ("콘텐츠창제작전문인력", "콘텐츠 창제작 전문인력"),
    ("1.2천명을양성하여", "1.2천명을 양성하여"),
    ("발전에따라게임등콘텐츠창·제작", "발전에 따라 게임 등 콘텐츠 창·제작"),
    ("가속화될것으로 기대", "가속화될 것으로 기대"),
    ("전문가의견 등을 통해선정", "전문가의견 등을 통해 선정"),
    ("관계부처 및유관협회및기관을 포함하여구성", "관계부처 및 유관협회 및 기관을 포함하여 구성"),
    ("확충하고 민간투자 연계 지원 강화하여혁신신약창출고속화견인필요", "확충하고 민간투자 연계 지원 강화하여 혁신신약창출고속화견인필요"),
    ("조성하고 민간투자 연계 지원 강화하여신약개발전주기지원", "조성하고 민간투자 연계 지원 강화하여 신약개발전주기지원"),
    ("의료기기를 융합(패키지)하여글로벌진출 모델 및 성과창출", "의료기기를 융합(패키지)하여 글로벌진출 모델 및 성과창출"),
    ("신융합장르발굴위한범장르 및 장르별 AI", "신융합장르 발굴위한 범장르 및 장르별 AI"),
    ("게임 개발에도전하도록", "게임 개발에 도전하도록"),
    ("향후5년간", "향후 5년간"),
    ("6천명양성추진", "6천명 양성 추진"),
    ("및유관협회및기관", "및 유관협회 및 기관"),
    ("하여구성", "하여 구성"),
    ("하여글로벌", "하여 글로벌"),
    ("디지탈분야", "디지탈 분야"),
    ("콘텐츠제작지원확대", "콘텐츠 제작지원 확대"),
    ("발굴위한", "발굴 위한"),
    ("한국의우수한의료기술", "한국의 우수한 의료기술"),
    ("성장하고있는", "성장하고 있는"),
    ("AI 바이오등해외전문인재의전략적확보", "AI 바이오 등 해외전문인재의 전략적 확보"),
    ("신약개발전주기지원", "신약개발 전주기 지원"),
    ("혁신신약창출고속화견인필요", "혁신신약창출 고속화 견인 필요"),
    ("‘26년75억원", "‘26년 75억원"),
    ("국정과제와의연계성", "국정과제와의 연계성"),
    ("지자체의견", "지자체 의견"),
    ("바이오헬스분야", "바이오헬스 분야"),
    ("글로벌탑티어해외석학30명유치추진", "글로벌 탑티어 해외석학 30명 유치 추진"),
    ("등기술융합생태계", "등 기술융합 생태계"),
    ("해외거점확보", "해외거점 확보"),
    ("정책지원방안마련", "정책지원 방안 마련"),
    ("의료시스템해외진출기반조성", "의료시스템 해외진출 기반 조성"),
    ("최신정보통신기술이결합된의료시스템의해외진출지원", "최신 정보통신기술이 결합된 의료시스템의 해외진출 지원"),
    ("ICT 기반의료시스템해외수출전주기지원", "ICT 기반 의료시스템 해외수출 전주기 지원"),
    ("현지인수․진출병원", "현지 인수․진출 병원"),
    ("데이터확보및실증등", "데이터 확보 및 실증 등"),
    ("연구개발에 활용될수있는디지털헬스데이터", "연구개발에 활용될 수 있는 디지털헬스 데이터"),
    ("해외진출규제사항및애로사항해결을위한정책지원사항발굴", "해외진출 규제사항 및 애로사항 해결을 위한 정책지원사항 발굴"),
    ("가시적성과창출", "가시적 성과 창출"),
    ("성과창출도모", "성과 창출 도모"),
    ("신융합장르발굴 위한범장르", "신융합장르 발굴 위한 범장르"),
    ("구체적인프로젝트", "구체적인 프로젝트"),
    ("해외인수병원을거점으로", "해외인수병원을 거점으로"),
    ("지원하는K-디지털헬스케어新수출전략", "지원하는 K-디지털헬스케어 新수출전략"),
    ("고려하여국내인재", "고려하여 국내인재"),
    ("양성과해외우수인재유치를위한현실적인정부지원필요", "양성과 해외우수인재 유치를 위한 현실적인 정부지원 필요"),
    ("등바이오헬스핵심인재11만명양성추진", "등 바이오헬스 핵심인재 11만명 양성 추진"),
    ("진출 지원등글로벌진출을위한단계적전주기 지원확대", "진출 지원 등 글로벌진출을 위한 단계적 전주기 지원 확대"),
    ("첨단기술기반제조인력등바이오헬스 핵심인재2단계양성5개년계획수립", "첨단기술기반제조인력 등 바이오헬스 핵심인재 2단계 양성 5개년계획 수립"),
    ("AI 활용융합모델확산등으로신약개발효율화", "AI 활용 융합모델 확산 등으로 신약개발 효율화"),
    ("기반 조성및해외성공사례발굴", "기반 조성 및 해외성공사례발굴"),
    ("위해최신 정보통신기술이", "위해 최신 정보통신기술이"),
    ("중심으로연구개발및임상시험수탁", "중심으로 연구개발 및 임상시험수탁"),
    ("등국내중소·벤처기업의테스트베드구축지원", "등 국내중소·벤처기업의 테스트베드 구축 지원"),
    ("통한해외거점 확보및기업진출지원", "통한 해외거점 확보 및 기업진출 지원"),
    ("병원과임상및실증을지원하는", "병원과 임상 및 실증을 지원하는"),
    ("장비등보유또는컨소시움구성", "장비 등 보유 또는 컨소시움 구성"),
    ("현지의료진대상의료기기교육훈련을 통한제품 현지화요구사항도출", "현지 의료진 대상 의료기기 교육훈련을 통한 제품 현지화 요구사항 도출"),
    ("수렴및사업계획구체화를 통해정책지원 방안 마련", "수렴 및 사업계획 구체화를 통해 정책지원 방안 마련"),
    ("펀드조성·투자활성화등해외진출기관금융지원방안 마련", "펀드조성·투자활성화 등 해외진출기관 금융지원방안 마련"),
    ("해외인수병원을 거점으로중소", "해외인수병원을 거점으로 중소"),
    ("K-디지털헬스케어 新수출전략정책지원", "K-디지털헬스케어 新수출전략 정책지원"),
    ("바이오헬스산업전문인력부족", "바이오헬스산업 전문인력 부족"),
    ("ICT 기반의료시스템", "ICT 기반 의료시스템"),
    ("해외성공사례발굴", "해외성공사례 발굴"),
    ("현지의료진대상의료기기교육훈련", "현지 의료진 대상 의료기기 교육훈련"),
    ("현지화요구사항도출", "현지화 요구사항 도출"),
    ("K-디지털헬스수출모델구축을위한분야별의견", "K-디지털헬스 수출모델 구축을 위한 분야별 의견"),
    ("금융지원방안 마련", "금융지원 방안 마련"),
    ("컨소시움구성", "컨소시움 구성"),
    ("기업진출지원", "기업 진출 지원"),
    ("국내중소·벤처기업", "국내 중소·벤처기업"),
    ("임상시험수탁", "임상시험 수탁"),
    ("협업방안", "협업 방안"),
    ("글로벌진출", "글로벌 진출"),
    ("빅데이터기반디지털의료기기연구개발통해", "빅데이터 기반 디지털의료기기 연구개발 통해"),
    ("글로벌수준의기술경쟁력확보", "글로벌 수준의 기술경쟁력 확보"),
    ("테스트베드성과기업등해외시장진출성공가능", "테스트베드 성과기업 등 해외시장 진출 성공 가능"),
    ("모델선정·지원", "모델 선정·지원"),
    ("중기부협업하여", "중기부 협업하여"),
    ("스케일업팁스플랫폼", "스케일업 팁스 플랫폼"),
    ("유망기업선정하고지원사업집중", "유망기업 선정하고 지원사업 집중"),
    ("사업화성공률제고", "사업화 성공률 제고"),
    ("인허가컨설팅", "인허가 컨설팅"),
    ("지원등글로벌", "지원 등 글로벌"),
    ("진출을위한단계적전주기 지원확대", "진출을 위한 단계적 전주기 지원 확대"),
    ("글로벌액셀러레이팅플랫폼등을", "글로벌 액셀러레이팅 플랫폼 등을"),
    ("통한컨설팅", "통한 컨설팅"),
    ("글로벌제약사네트워크구축등제공", "글로벌 제약사 네트워크 구축 등 제공"),
    ("블록버스터급신약3건창출", "블록버스터급 신약 3건 창출"),
    ("글로벌액셀러레이팅플랫폼2단계사업", "글로벌 액셀러레이팅 플랫폼 2단계 사업"),
    ("추진및美", "추진 및 美"),
    ("등주요거점진출지속확대", "등 주요거점 진출 지속 확대"),
    ("빅데이터 기반 디지털의료기기 연구개발 통해", "빅데이터 기반 디지털의료기기 연구개발을 통해"),
    ("펀드조성·투자활성화", "펀드 조성·투자활성화"),
    ("정책지원사항 발굴", "정책지원 사항 발굴"),
    ("통해공동으로", "통해 공동으로"),
    ("집중*하여사업화", "집중*하여 사업화"),
    ("복지부유망기업", "복지부 유망기업"),
    ("중기부투자유치", "중기부 투자유치"),
    ("복지부R&D평가하여", "복지부 R&D 평가하여"),
    ("R&D자금&사업화자금", "R&D자금 & 사업화자금"),
    ("보고서작성및", "보고서 작성 및"),
    ("리뷰등현지전문의활용임상자문서비스", "리뷰 등 현지 전문의 활용 임상자문 서비스"),
    ("투자활성화등해외진출기관금융지원", "투자활성화 등 해외진출기관 금융지원"),
]
LOW_RISK_FRAGMENT_REPLACEMENTS = [
    ("을통해", "을 통해"),
    ("를통해", "를 통해"),
    ("을위해", "을 위해"),
    ("를위해", "를 위해"),
    ("을통한", "을 통한"),
    ("를통한", "를 통한"),
    ("에대한", "에 대한"),
    ("을중심으로", "을 중심으로"),
    ("를중심으로", "를 중심으로"),
    ("을포함하여", "을 포함하여"),
    ("를포함하여", "를 포함하여"),
    ("을고려하여", "을 고려하여"),
    ("를고려하여", "를 고려하여"),
    ("성과창출", "성과 창출"),
    ("방안마련", "방안 마련"),
    ("전주기지원", "전주기 지원"),
    ("기반조성", "기반 조성"),
    ("유치추진", "유치 추진"),
    ("될수있는", "될 수 있는"),
    ("성과창출을", "성과 창출을"),
    ("성과창출이", "성과 창출이"),
    ("등방안", "등 방안"),
    ("및해외", "및 해외"),
    ("통한제품", "통한 제품"),
    ("중심으로연구", "중심으로 연구"),
    ("통한해외", "통한 해외"),
    ("및 사업계획구체화", "및 사업계획 구체화"),
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def normalize_line(line: str) -> str:
    line = line.replace("\xa0", " ")
    line = line.replace("\uf000", "- ")
    line = line.strip()
    line = re.sub(r"[ \t]+", " ", line)
    return line


def is_table_line(line: str) -> bool:
    return line.startswith("|") and line.count("|") >= 2


def is_footer_line(line: str) -> bool:
    return bool(FOOTER_PATTERN.match(line))


def is_noise_marker_line(line: str) -> bool:
    compact = line.replace(" ", "")
    return bool(MARKER_ONLY_PATTERN.match(line)) or (compact != "" and all(char in NOISE_MARKERS for char in compact))


def classify_text_block(text: str) -> str:
    if text.startswith("|"):
        return "table_markdown"
    if text.startswith("#"):
        return "heading"
    if text.startswith("【") or (text.startswith("<") and text.endswith(">")):
        return "heading"
    if CIRCLED_HEADING_PATTERN.match(text):
        return "heading"
    if ROMAN_HEADING_PATTERN.match(text):
        return "heading"
    if NUMBERED_HEADING_PATTERN.match(text):
        return "heading"
    if text.startswith("(") and text.endswith(")") and DATE_NOTE_PATTERN.match(text):
        return "citation"
    if text == "현장의 목소리" or text.endswith("현장의 목소리"):
        return "heading"
    if text.startswith("※"):
        return "note"
    if STAR_NOTE_PATTERN.match(text):
        return "note"
    if BULLET_PATTERN.match(text):
        return "bullet"
    return "paragraph"


def starts_new_text_unit(text: str) -> bool:
    return classify_text_block(text) in {"heading", "bullet", "note", "citation"}


def smart_join(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if left.endswith(("(", "[", "{", "“", "\"", "『")):
        return f"{left}{right}"
    if right.startswith((")", "]", "}", ",", ".", ":", ";", "”", "\"", "』")):
        return f"{left}{right}"
    return f"{left} {right}"


def normalize_surface_text(text: str, block_type: str) -> str:
    text = text.strip()
    if block_type == "table_markdown":
        return text
    star_match = re.match(r"^((?:\*\s*){2,3})(?=\S)", text)
    if star_match:
        text = f"{'*' * star_match.group(1).count('*')} {text[star_match.end():].lstrip()}"
    if block_type in {"bullet", "note"}:
        text = re.sub(r"^([□ㅇ▪•※⇨])(?=\S)", r"\1 ", text)
        text = re.sub(r"^(-)(?=\S)", r"- ", text)
        text = re.sub(r"^(\*{1,3})(?=[^\s*])", r"\1 ", text)
    text = INLINE_DOT_AFTER_SPACE_PATTERN.sub(r"\1", text)
    text = INLINE_DOT_BEFORE_SPACE_PATTERN.sub(r"\1", text)
    for source, target in LOW_RISK_TEXT_REPLACEMENTS:
        text = text.replace(source, target)
    for source, target in LOW_RISK_FRAGMENT_REPLACEMENTS:
        text = text.replace(source, target)
    for source, target in LOW_RISK_TEXT_REPLACEMENTS:
        text = text.replace(source, target)
    return re.sub(r"[ \t]+", " ", text).strip()


def fold_lines(lines: list[str]) -> str:
    text = ""
    for line in lines:
        text = smart_join(text, line) if text else line
    return re.sub(r"\s+", " ", text).strip()


def merge_bbox(a: list[float] | None, b: list[float] | None) -> list[float] | None:
    if a is None:
        return b
    if b is None:
        return a
    return [
        min(a[0], b[0]),
        min(a[1], b[1]),
        max(a[2], b[2]),
        max(a[3], b[3]),
    ]


def normalize_bbox_shape(raw_bbox: object) -> list[float] | None:
    if raw_bbox in (None, ""):
        return None
    if isinstance(raw_bbox, (list, tuple)):
        if len(raw_bbox) == 4 and all(isinstance(value, (int, float)) for value in raw_bbox):
            return [float(value) for value in raw_bbox]
        if raw_bbox and all(isinstance(point, (list, tuple)) and len(point) >= 2 for point in raw_bbox):
            xs = [float(point[0]) for point in raw_bbox]
            ys = [float(point[1]) for point in raw_bbox]
            return [min(xs), min(ys), max(xs), max(ys)]
    return None


def rect_overlap_ratio(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b:
        return 0.0
    ix0 = max(a[0], b[0])
    iy0 = max(a[1], b[1])
    ix1 = min(a[2], b[2])
    iy1 = min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    intersection = (ix1 - ix0) * (iy1 - iy0)
    area_a = max((a[2] - a[0]) * (a[3] - a[1]), 1.0)
    return intersection / area_a


def bbox_width(bbox: list[float] | None) -> float:
    if not bbox:
        return 0.0
    return max(bbox[2] - bbox[0], 0.0)


def bbox_center_x(bbox: list[float] | None) -> float:
    if not bbox:
        return 0.0
    return (bbox[0] + bbox[2]) / 2.0


def is_centered_bbox(bbox: list[float] | None, page_width: float) -> bool:
    if not bbox or page_width <= 0:
        return False
    width = bbox_width(bbox)
    if width <= 0 or width >= page_width * 0.82:
        return False
    return abs(bbox_center_x(bbox) - (page_width / 2.0)) <= 70


def has_sentence_continuation_shape(previous_bbox: list[float], current_bbox: list[float], page_width: float) -> bool:
    prev_width = bbox_width(previous_bbox)
    curr_width = bbox_width(current_bbox)
    left_delta = current_bbox[0] - previous_bbox[0]
    right_delta = current_bbox[2] - previous_bbox[2]

    near_left_aligned = abs(left_delta) <= 32
    hanging_indent = 0 <= left_delta <= 56
    similar_right_edge = abs(right_delta) <= 56
    previous_fills_line = prev_width >= page_width * 0.65 or previous_bbox[2] >= page_width * 0.78
    current_has_body_width = curr_width >= page_width * 0.42 or current_bbox[2] >= page_width * 0.60

    return current_has_body_width and (near_left_aligned or hanging_indent or similar_right_edge or previous_fills_line)


def should_merge_centered_title(previous: dict, current: dict, page_width: float, vertical_gap: float) -> bool:
    prev_bbox = previous.get("bbox")
    curr_bbox = current.get("bbox")
    if not prev_bbox or not curr_bbox:
        return False
    if previous["block_type"] not in {"paragraph", "heading"}:
        return False
    if current["block_type"] not in {"paragraph", "heading"}:
        return False
    if len(previous["text"]) > 80 or len(current["text"]) > 80:
        return False
    if vertical_gap > 36:
        return False
    return is_centered_bbox(prev_bbox, page_width) and is_centered_bbox(curr_bbox, page_width)


def is_candidate_table_bbox(rows: int, cols: int) -> bool:
    if rows <= 0 or cols <= 0:
        return False
    if rows == 1 and cols <= 3:
        return False
    if rows >= 2 and cols >= 2:
        return True
    if cols >= 4:
        return True
    return False


def load_table_bboxes_from_page_records(page_records: list[dict]) -> dict[int, list[list[float]]]:
    bboxes_by_page: dict[int, list[list[float]]] = defaultdict(list)
    for page in page_records:
        page_no = int(page.get("page_no", 0) or 0)
        if page_no <= 0:
            continue
        for table in page.get("tables", []):
            bbox = table.get("bbox")
            rows = int(table.get("rows", 0) or 0)
            cols = int(table.get("columns", 0) or 0)
            bbox = normalize_bbox_shape(bbox)
            if bbox and is_candidate_table_bbox(rows, cols):
                bboxes_by_page[page_no].append(bbox)
    return bboxes_by_page


def load_table_bboxes(document_id: str, table_dir: Path, page_records: list[dict]) -> dict[int, list[list[float]]]:
    bboxes_by_page: dict[int, list[list[float]]] = defaultdict(list)
    for path in sorted(table_dir.glob(f"TBL-{document_id}-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        page_no = payload.get("page_no_or_sheet_name")
        if not isinstance(page_no, int):
            continue
        shape = payload.get("table_shape", {})
        rows = int(shape.get("rows", 0) or 0)
        cols = int(shape.get("cols", 0) or 0)
        source_bbox = payload.get("source_bbox")
        source_bbox = normalize_bbox_shape(source_bbox)
        if source_bbox and is_candidate_table_bbox(rows, cols):
            bboxes_by_page[page_no].append(source_bbox)
    if not bboxes_by_page:
        return load_table_bboxes_from_page_records(page_records)
    return bboxes_by_page


def split_raw_blocks_from_markdown(page_text: str) -> list[dict]:
    blocks = []
    current_lines: list[str] = []
    current_kind: str | None = None

    def flush() -> None:
        nonlocal current_lines, current_kind
        if not current_lines:
            current_kind = None
            return
        blocks.append({"kind": current_kind or "text", "lines": current_lines[:]})
        current_lines = []
        current_kind = None

    for line in page_text.splitlines():
        normalized = normalize_line(line)
        if not normalized:
            flush()
            continue
        if is_table_line(normalized):
            if current_kind != "table":
                flush()
            current_kind = "table"
            current_lines.append(normalized)
            continue
        if current_kind == "table":
            flush()
        current_kind = "text"
        current_lines.append(normalized)

    flush()
    return blocks


def extract_table_markdown_blocks(page_no: int, page_text: str) -> list[dict]:
    blocks = []
    for raw_index, raw_block in enumerate(split_raw_blocks_from_markdown(page_text), start=1):
        if raw_block["kind"] != "table":
            continue
        table_text = "\n".join(raw_block["lines"]).strip()
        if not table_text:
            continue
        blocks.append(
            {
                "page_no": page_no,
                "raw_block_order": raw_index,
                "block_type": "table_markdown",
                "text": table_text,
                "source_line_count": len(raw_block["lines"]),
                "merged_block_count": 1,
                "normalization_actions": [],
                "bbox": None,
                "source_mode": "markdown_table",
            }
        )
    return blocks


def split_text_units(lines: list[str]) -> list[list[str]]:
    units: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if current and starts_new_text_unit(line):
            units.append(current)
            current = [line]
            continue
        current.append(line)

    if current:
        units.append(current)
    return units


def should_skip_block(text: str, bbox: list[float] | None, page_height: float, table_bboxes: list[list[float]]) -> tuple[bool, str]:
    if not text:
        return True, "empty"
    if is_noise_marker_line(text):
        return True, "noise_marker"
    if is_footer_line(text):
        return True, "footer"
    if bbox and bbox[1] >= page_height * 0.92 and is_footer_line(text):
        return True, "footer"
    if bbox and any(rect_overlap_ratio(bbox, table_bbox) >= 0.35 for table_bbox in table_bboxes):
        return True, "table_overlap"
    return False, ""


def normalize_bbox_text_blocks(
    page_no: int,
    page_blocks: list[dict],
    page_height: float,
    page_width: float,
    table_bboxes: list[list[float]],
) -> tuple[list[dict], dict]:
    normalized = []
    removed_footer_count = 0
    skipped_table_overlap_count = 0
    skipped_noise_count = 0

    sorted_blocks = sorted(
        page_blocks,
        key=lambda block: (
            round((normalize_bbox_shape(block.get("bbox")) or [0.0, 0.0, 0.0, 0.0])[1] / 6.0),
            (normalize_bbox_shape(block.get("bbox")) or [0.0, 0.0, 0.0, 0.0])[2],
            (normalize_bbox_shape(block.get("bbox")) or [0.0, 0.0, 0.0, 0.0])[0],
        ),
    )
    for raw_index, block in enumerate(sorted_blocks, start=1):
        bbox = normalize_bbox_shape(block.get("bbox"))
        raw_lines = [normalize_line(line) for line in block.get("text", "").splitlines()]
        raw_lines = [line for line in raw_lines if line]
        if not raw_lines:
            continue

        first_line = fold_lines(raw_lines[:1])
        skip, reason = should_skip_block(first_line, bbox, page_height, table_bboxes)
        if skip:
            if reason == "footer":
                removed_footer_count += 1
            elif reason in {"noise_marker", "empty"}:
                skipped_noise_count += 1
            elif reason == "table_overlap":
                skipped_table_overlap_count += 1
            continue

        lines = [line for line in raw_lines if not is_noise_marker_line(line) and not is_footer_line(line)]
        if not lines:
            continue

        units = split_text_units(lines)
        for unit_lines in units:
            text = fold_lines(unit_lines)
            if not text or is_noise_marker_line(text):
                continue
            normalized.append(
                {
                    "page_no": page_no,
                    "raw_block_order": raw_index,
                    "block_type": classify_text_block(text),
                    "text": text,
                    "source_line_count": len(unit_lines),
                    "merged_block_count": 1,
                    "normalization_actions": [],
                    "bbox": bbox,
                    "source_mode": "bbox_text",
                }
            )

    merged = []
    merge_count = 0
    for block in normalized:
        if merged and should_merge(merged[-1], block, page_width):
            merged[-1]["text"] = smart_join(merged[-1]["text"], block["text"])
            merged[-1]["source_line_count"] += block["source_line_count"]
            merged[-1]["merged_block_count"] += 1
            merged[-1]["bbox"] = merge_bbox(merged[-1].get("bbox"), block.get("bbox"))
            merged[-1]["normalization_actions"].append("merged_continuation")
            merge_count += 1
            continue
        merged.append(block)

    summary = {
        "page_no": page_no,
        "text_block_count": len(merged),
        "removed_footer_count": removed_footer_count,
        "skipped_table_overlap_count": skipped_table_overlap_count,
        "skipped_noise_count": skipped_noise_count,
        "merge_count": merge_count,
    }
    return merged, summary


def should_merge(previous: dict, current: dict, page_width: float) -> bool:
    if previous["block_type"] == "table_markdown" or current["block_type"] == "table_markdown":
        return False

    prev_bbox = previous.get("bbox")
    curr_bbox = current.get("bbox")
    if not prev_bbox or not curr_bbox:
        return False

    vertical_gap = curr_bbox[1] - prev_bbox[3]
    same_line = abs(curr_bbox[1] - prev_bbox[1]) <= 8
    left_delta = curr_bbox[0] - prev_bbox[0]

    if should_merge_centered_title(previous, current, page_width, vertical_gap):
        return True
    if previous["block_type"] == "citation" or current["block_type"] == "citation":
        return False
    if previous["block_type"] == "heading":
        return False
    if current["block_type"] in {"heading", "bullet", "note"}:
        return False

    if vertical_gap > 40:
        return False
    if same_line:
        return True
    if vertical_gap < -8:
        return False
    if STRONG_ENDING_PATTERN.search(previous["text"]):
        return False
    if previous["text"].endswith(("｢", "(", "[", "·")):
        return True
    if previous["text"].endswith((",", ":", "→", "⇨", "및", "등")) and vertical_gap <= 24:
        return True
    if current["block_type"] == "paragraph" and has_sentence_continuation_shape(prev_bbox, curr_bbox, page_width):
        if vertical_gap <= 26:
            return True
    if left_delta >= 8 and current["block_type"] == "paragraph":
        return True
    if vertical_gap <= 12 and current["block_type"] == "paragraph":
        return True
    if vertical_gap <= 24 and len(current["text"]) <= 120 and current["block_type"] == "paragraph":
        return True
    return False


def is_cover_metadata_block(page_no: int, block: dict) -> bool:
    if page_no != 1:
        return False
    text = block["text"].strip()
    if PURE_DATE_PATTERN.fullmatch(text):
        return True
    if text in {"관계부처합동"}:
        return True
    if ("성장전략TF" in text or "성장전략 TF" in text) and ("관계장관회의" in text or "공개" in text):
        return True
    return False


def normalized_heading_key(text: str) -> str:
    return HEADING_PREFIX_NORMALIZER.sub("", text).strip()


def split_inline_section_marker_blocks(block: dict) -> list[dict]:
    if block["block_type"] == "table_markdown":
        return [block]

    parts = [part.strip() for part in INLINE_SECTION_MARKER_SPLIT_PATTERN.split(block["text"]) if part.strip()]
    if len(parts) <= 1:
        return [block]

    split_blocks: list[dict] = []
    for index, part in enumerate(parts):
        new_block = {**block}
        new_block["text"] = part
        new_block["block_type"] = classify_text_block(part)
        if index > 0:
            new_block["normalization_actions"] = [*new_block.get("normalization_actions", []), "split_inline_section_marker"]
        split_blocks.append(new_block)
    return split_blocks


def postprocess_page_blocks(page_no: int, blocks: list[dict]) -> tuple[list[dict], int]:
    processed: list[dict] = []
    skipped_noise_count = 0
    seen_special_heading_keys: set[str] = set()

    for block in blocks:
        block = {**block}
        block["text"] = normalize_surface_text(block["text"], block["block_type"])
        for split_block in split_inline_section_marker_blocks(block):
            if is_cover_metadata_block(page_no, split_block):
                skipped_noise_count += 1
                continue
            if split_block["block_type"] == "heading":
                heading_key = normalized_heading_key(split_block["text"])
                if heading_key == "현장의 목소리" and heading_key in seen_special_heading_keys:
                    skipped_noise_count += 1
                    continue
                if heading_key == "현장의 목소리":
                    seen_special_heading_keys.add(heading_key)
            processed.append(split_block)

    return processed, skipped_noise_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    pages_path = out_root / "work/02_structured-extraction/text" / f"{args.document_id}_pages.json"
    blocks_path = out_root / "work/02_structured-extraction/text" / f"{args.document_id}_blocks.json"
    layout_path = out_root / "work/02_structured-extraction/layout" / f"{args.document_id}_layout.json"
    if not layout_path.exists():
        ocr_layout_path = out_root / "work/02_structured-extraction/layout" / f"{args.document_id}_ocr_layout.json"
        if ocr_layout_path.exists():
            layout_path = ocr_layout_path
    table_dir = out_root / "work/02_structured-extraction/tables"
    if not pages_path.exists():
        raise FileNotFoundError(f"Missing page chunk file: {pages_path}")
    if not blocks_path.exists():
        raise FileNotFoundError(f"Missing bbox block file: {blocks_path}")
    if not layout_path.exists():
        raise FileNotFoundError(f"Missing layout file: {layout_path}")

    page_records = json.loads(pages_path.read_text(encoding="utf-8"))
    bbox_blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    layout_pages = json.loads(layout_path.read_text(encoding="utf-8"))
    normalized_dir = out_root / "work/03_processing/normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)

    blocks_by_page: dict[int, list[dict]] = defaultdict(list)
    for block in bbox_blocks:
        page_no = int(block["page_no_or_sheet_name"])
        blocks_by_page[page_no].append(block)

    layout_by_page = {int(page["page_no"]): page for page in layout_pages}
    table_bboxes_by_page = load_table_bboxes(args.document_id, table_dir, page_records)

    page_outputs = []
    paragraph_outputs = []
    page_summaries = []
    paragraph_counter = 0

    for page_record in page_records:
        page_no = int(page_record["page_no"])
        page_layout = layout_by_page.get(page_no, {})
        page_height = float(page_layout.get("page_height", 0.0) or 0.0)
        page_width = float(page_layout.get("page_width", 0.0) or 0.0)

        text_blocks, summary = normalize_bbox_text_blocks(
            page_no=page_no,
            page_blocks=blocks_by_page.get(page_no, []),
            page_height=page_height,
            page_width=page_width,
            table_bboxes=table_bboxes_by_page.get(page_no, []),
        )
        text_blocks, postprocess_skipped = postprocess_page_blocks(page_no, text_blocks)
        summary["skipped_noise_count"] += postprocess_skipped
        table_blocks = extract_table_markdown_blocks(page_no, page_record.get("text", ""))
        page_summaries.append(summary)

        clean_text = "\n\n".join(block["text"] for block in text_blocks).strip()
        combined_blocks = text_blocks + table_blocks

        page_outputs.append(
            {
                "document_id": args.document_id,
                "page_no": page_no,
                "clean_text": clean_text,
                "text_block_count": len(text_blocks),
                "table_block_count": len(table_blocks),
                "metadata": page_record.get("metadata", {}),
            }
        )

        for page_block_order, block in enumerate(combined_blocks, start=1):
            paragraph_counter += 1
            paragraph_outputs.append(
                {
                    "paragraph_id": f"PAR-{args.document_id}-{paragraph_counter:05d}",
                    "document_id": args.document_id,
                    "page_no": page_no,
                    "page_block_order": page_block_order,
                    "block_type": block["block_type"],
                    "text": block["text"],
                    "source_line_count": block["source_line_count"],
                    "merged_block_count": block.get("merged_block_count", 1),
                    "normalization_actions": "|".join(block.get("normalization_actions", [])),
                    "source_mode": block.get("source_mode", "bbox_text"),
                }
            )

    summary_payload = {
        "document_id": args.document_id,
        "source_page_chunk_path": str(pages_path.relative_to(out_root)),
        "source_bbox_block_path": str(blocks_path.relative_to(out_root)),
        "page_count": len(page_records),
        "paragraph_count": len(paragraph_outputs),
        "text_paragraph_count": sum(1 for row in paragraph_outputs if row["block_type"] != "table_markdown"),
        "table_block_count": sum(page["table_block_count"] for page in page_outputs),
        "removed_footer_count": sum(page["removed_footer_count"] for page in page_summaries),
        "skipped_table_overlap_count": sum(page["skipped_table_overlap_count"] for page in page_summaries),
        "skipped_noise_count": sum(page["skipped_noise_count"] for page in page_summaries),
        "merge_count": sum(page["merge_count"] for page in page_summaries),
    }

    page_output_path = normalized_dir / f"{args.document_id}__pages-clean.json"
    paragraph_output_path = normalized_dir / f"{args.document_id}__paragraphs.json"
    paragraph_csv_path = normalized_dir / f"{args.document_id}__paragraphs.csv"
    summary_path = normalized_dir / f"{args.document_id}__text-normalization-report.json"

    write_json(page_output_path, page_outputs)
    write_json(paragraph_output_path, paragraph_outputs)
    write_json(summary_path, summary_payload)
    write_csv(
        paragraph_csv_path,
        paragraph_outputs,
        [
            "paragraph_id",
            "document_id",
            "page_no",
            "page_block_order",
            "block_type",
            "text",
            "source_line_count",
            "merged_block_count",
            "normalization_actions",
            "source_mode",
        ],
    )


if __name__ == "__main__":
    main()
