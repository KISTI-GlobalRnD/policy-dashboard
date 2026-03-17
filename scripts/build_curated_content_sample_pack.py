#!/usr/bin/env python3
"""Build a small curated content-evidence sample pack from current raw ontology data."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


LEGACY_POLICY_ITEM_REP_MAP_PATH = (
    Path(__file__).resolve().parent.parent / "work/04_ontology/samples/legacy_policy_item_rep_map.json"
)


SAMPLE_GROUPS = [
    {
        "policy_item_group_id": "PIG-POL-002-01",
        "policy_bucket_id": "PBK-POL-002-01",
        "group_label": "국가 AI 바이오 연구소 및 파운데이션 모델",
        "group_summary": "국가 연구거점을 중심으로 바이오 파운데이션 모델을 구축·개방하는 대표 묶음",
        "group_description": "국가 AI 바이오 연구소 설립과 범용 바이오 파운데이션 모델 구축을 하나의 대표 항목으로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-003", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-011", "is_primary": 0},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-011-001", "is_primary": 0},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-002-00001", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-002-00060", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-002-01-01",
                "content_label": "국가 연구거점 설립",
                "content_statement": "(가칭) 국가 AI 바이오 연구소를 설립해 국가 차원의 AI-바이오 연구개발 거점을 구축한다.",
                "content_summary": "연구소 설립을 통해 국가 차원의 전담 거점을 만든다.",
                "content_type": "institution_setup",
                "display_order": 1,
                "evidence_policy_item_ids": ["ITM-POL-002-00001"],
            },
            {
                "policy_item_content_id": "PIC-POL-002-01-02",
                "content_label": "바이오 파운데이션 모델 구축·개방",
                "content_statement": "연구소를 중심으로 멀티모달-멀티스케일 바이오 파운데이션 모델을 구축하고 산업 활용을 확산한다.",
                "content_summary": "범용 바이오 파운데이션 모델을 구축·개방한다.",
                "content_type": "model_development",
                "display_order": 2,
                "evidence_policy_item_ids": ["ITM-POL-002-00060"],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-002-02",
        "policy_bucket_id": "PBK-POL-002-02",
        "group_label": "바이오 데이터 플랫폼 및 개방체계",
        "group_summary": "K-BDS 중심 통합플랫폼과 데이터 개방·표준화·품질관리를 함께 보여주는 대표 묶음",
        "group_description": "데이터 수집·연계, 개방, 표준화, 품질 고도화를 하나의 운영 체계로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-003", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-011", "is_primary": 0},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-005", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-011-001", "is_primary": 0},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-002-00099", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-002-00102", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00108", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00113", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00114", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-002-02-01",
                "content_label": "K-BDS 중심 데이터 통합·개방",
                "content_statement": "K-BDS를 국가바이오데이터통합플랫폼으로 고도화하고 민간·거점 데이터를 연계해 외부 연구자 활용까지 개방한다.",
                "content_summary": "통합플랫폼 구축과 데이터 개방을 함께 추진한다.",
                "content_type": "platform_operation",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-002-00099",
                    "ITM-POL-002-00102",
                    "ITM-POL-002-00108",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-002-02-02",
                "content_label": "데이터 표준화·품질관리 강화",
                "content_statement": "메타데이터와 데이터 표준화를 지원하고 품질선도 체계를 확대해 바이오 데이터 품질을 높인다.",
                "content_summary": "표준화와 품질관리 체계를 함께 강화한다.",
                "content_type": "standard_quality_management",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-002-00113",
                    "ITM-POL-002-00114",
                ],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-002-03",
        "policy_bucket_id": "PBK-POL-002-02",
        "group_label": "AI 바이오 법제·규제 개선",
        "group_summary": "데이터 활용 법체계와 규제특례를 함께 정리한 대표 묶음",
        "group_description": "데이터 활용 편의를 높이는 법제도와 안전한 활용 특례를 함께 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 2,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-003", "is_primary": 1},
            {"taxonomy_type": "strategy", "term_id": "STR-010", "is_primary": 0},
            {"taxonomy_type": "tech_domain", "term_id": "TD-011", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-011-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-003", "is_primary": 0},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-002-00105", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-002-00107", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00111", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00112", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-002-03-01",
                "content_label": "데이터 활용 법체계 정비",
                "content_statement": "인체유래물·보건의료 데이터 활용 편의를 높이는 규제 개선과 디지털헬스케어 법체계를 정비한다.",
                "content_summary": "데이터 활용 법체계를 정비한다.",
                "content_type": "regulation_reform",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-002-00105",
                    "ITM-POL-002-00107",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-002-03-02",
                "content_label": "안전한 데이터 활용 특례",
                "content_statement": "복수기관 기증 동의와 폐쇄망 클라우드 등 안전한 데이터 활용 특례를 도입해 활용성을 높인다.",
                "content_summary": "데이터 활용 특례와 안전조치를 함께 마련한다.",
                "content_type": "secure_data_use",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-002-00111",
                    "ITM-POL-002-00112",
                ],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-002-04",
        "policy_bucket_id": "PBK-POL-002-03",
        "group_label": "AI-바이오 융합 인재양성 트랙",
        "group_summary": "융합 교육 부족 문제와 전문 교육트랙 개설을 함께 보여주는 인재 샘플",
        "group_description": "AI와 바이오를 함께 이해하는 인재 양성을 위한 교육트랙 구성 예시다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-003", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-011", "is_primary": 0},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-011-001", "is_primary": 0},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-002-00115", "member_role": "background_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-002-00116", "member_role": "representative_item", "is_representative": 1},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-002-04-01",
                "content_label": "대학원-전문과정 융합 교육트랙",
                "content_statement": "대학원부터 전문과정까지 이어지는 AI-바이오 융합 교육트랙을 개설하고 산학 연계 프로그램을 운영한다.",
                "content_summary": "융합 교육트랙을 개설해 전문 인재를 양성한다.",
                "content_type": "training_program",
                "display_order": 1,
                "evidence_policy_item_ids": ["ITM-POL-002-00116"],
            }
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-011-01",
        "policy_bucket_id": "PBK-POL-011-01",
        "group_label": "AX 기획 컨설팅 및 가이드라인",
        "group_summary": "부처 AX기획 초기 단계의 컨설팅과 가이드라인 제공을 묶은 대표 샘플",
        "group_description": "AX자문단, AX가이드라인, AX사전 컨설팅을 하나의 기획 지원 패키지로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-007", "is_primary": 1},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-011-00818", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00832", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-011-00833", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00836", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-011-01-01",
                "content_label": "부처 대상 AX 기획 컨설팅",
                "content_statement": "AX자문단과 사전 컨설팅(PoC)을 통해 부처와 전담기관의 AX 기획을 지원한다.",
                "content_summary": "AX 기획 단계의 컨설팅을 제공한다.",
                "content_type": "planning_support",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-011-00818",
                    "ITM-POL-011-00836",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-011-01-02",
                "content_label": "분야별 AX 가이드라인 제공",
                "content_statement": "분야별 AX 성공사례와 기술 스택 정보를 담은 가이드라인을 마련해 AX사업 기획 참고자료로 제공한다.",
                "content_summary": "부처가 참고할 AX 가이드라인을 제공한다.",
                "content_type": "guideline_support",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-011-00832",
                    "ITM-POL-011-00833",
                ],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-011-02",
        "policy_bucket_id": "PBK-POL-011-01",
        "group_label": "공공 AX 실행 인프라 지원",
        "group_summary": "GPU, 데이터, 공통기반, 검증을 묶은 실행 지원 패키지",
        "group_description": "공공 AX 본사업에 필요한 자원 지원과 검증 체계를 대표 내용으로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 2,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-004", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-005", "is_primary": 0},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-011-00817", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00822", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00830", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00831", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-011-00835", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-011-02-01",
                "content_label": "GPU·데이터·공통기반 지원",
                "content_statement": "특화 AI모델 개발을 위한 GPU와 데이터, 범정부 AI공통기반을 함께 지원한다.",
                "content_summary": "공공 AX 실행에 필요한 자원을 통합 지원한다.",
                "content_type": "resource_support",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-011-00822",
                    "ITM-POL-011-00830",
                    "ITM-POL-011-00831",
                ],
                "extra_evidence_specs": [
                    {
                        "derived_representation_id": "DRV-CTBL-DOC-POL-012-003",
                        "source_policy_item_id": "ITM-POL-011-00831",
                        "evidence_label": "정부 AX사업 GPU 지원 표",
                        "link_role": "secondary_support",
                        "evidence_strength": "medium",
                    }
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-011-02-02",
                "content_label": "성능 검증 및 실증 지원",
                "content_statement": "현장 실증과 성능·신뢰성 검증을 지원해 AX사업 결과물의 품질을 높인다.",
                "content_summary": "실증과 검증을 함께 지원한다.",
                "content_type": "validation_support",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-011-00817",
                    "ITM-POL-011-00835",
                ],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-011-03",
        "policy_bucket_id": "PBK-POL-011-02",
        "group_label": "AX 원스톱 운영체계 및 국가 AX지도",
        "group_summary": "운영 거버넌스와 국가 AX 현황 가시화를 함께 보여주는 인프라·제도 샘플",
        "group_description": "AX 원스톱 지원센터 운영과 국가 AX지도 구축을 하나의 운영체계로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-001", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-001", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-001-008", "is_primary": 1},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-011-00846", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-011-00847", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-011-00848", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-011-03-01",
                "content_label": "AX 원스톱 지원센터 운영",
                "content_statement": "AX 원스톱 지원센터와 공공AI사업지원센터를 운영해 부처별 AX사업 지원을 본격화한다.",
                "content_summary": "원스톱 운영체계를 구축한다.",
                "content_type": "program_operation",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-011-00846",
                    "ITM-POL-011-00847",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-011-03-02",
                "content_label": "국가 AX지도 구축",
                "content_statement": "지역·분야별 AX 수요와 투자, 보유 자원을 종합 분석한 국가 AX지도를 구축해 민관 투자계획 수립에 활용한다.",
                "content_summary": "국가 AX 현황을 지도 형태로 제공한다.",
                "content_type": "mapping_and_monitoring",
                "display_order": 2,
                "evidence_policy_item_ids": ["ITM-POL-011-00848"],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-005-01",
        "policy_bucket_id": "PBK-POL-005-01",
        "group_label": "K-NPU 성능 고도화 및 실증",
        "group_summary": "독자 AI모델 연계 성능 고도화와 테스트베드·검증·사업화를 묶은 대표 샘플",
        "group_description": "AI반도체 전략에서 핵심 기술 고도화와 실증·사업화를 함께 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-002", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-009", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-009-001", "is_primary": 1},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-005-00225", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00242", "member_role": "representative_item", "is_representative": 1},
            {"policy_item_id": "ITM-POL-005-00283", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00284", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00287", "member_role": "supporting_item", "is_representative": 0},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-005-01-01",
                "content_label": "독자 AI모델 연계 성능 고도화",
                "content_statement": "독자 AI모델과 국산 NPU의 연계성을 높여 최신 AI모델 맞춤형 성능을 확보한다.",
                "content_summary": "국산 NPU 성능을 독자 AI모델과 함께 고도화한다.",
                "content_type": "performance_advancement",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-005-00225",
                    "ITM-POL-005-00284",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-005-01-02",
                "content_label": "테스트베드·검증·사업화 지원",
                "content_statement": "대규모 K-NPU 테스트베드, 성과 검증, 실증·사업화 지원체계를 함께 구축한다.",
                "content_summary": "K-NPU 테스트베드와 사업화 지원체계를 구축한다.",
                "content_type": "testbed_and_validation",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-005-00242",
                    "ITM-POL-005-00283",
                    "ITM-POL-005-00287",
                ],
                "extra_evidence_specs": [
                    {
                        "derived_representation_id": "DRV-FIG-DOC-POL-007-008",
                        "source_policy_item_id": "ITM-POL-005-00242",
                        "evidence_label": "K-NPU 테스트베드·실증 도식 예시",
                        "link_role": "secondary_support",
                        "evidence_strength": "medium",
                    }
                ],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-005-02",
        "policy_bucket_id": "PBK-POL-005-02",
        "group_label": "AI반도체 금융·세제 지원",
        "group_summary": "정책금융과 세제 인센티브를 함께 보여주는 인프라·제도 샘플",
        "group_description": "초기 투자비용 지원, 직간접 투자, 대규모 투융자, 세액 공제를 한데 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-002", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-009", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-009-001", "is_primary": 1},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-005-00304", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00306", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00310", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00311", "member_role": "representative_item", "is_representative": 1},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-005-02-01",
                "content_label": "정책금융 프로그램 제공",
                "content_statement": "수요-공급기업 지원, 직간접 투자, 성장 단계별 대규모 투·융자를 포함한 정책금융 프로그램을 제공한다.",
                "content_summary": "정책금융과 투자 프로그램을 패키지로 제공한다.",
                "content_type": "policy_finance",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-005-00304",
                    "ITM-POL-005-00310",
                    "ITM-POL-005-00311",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-005-02-02",
                "content_label": "세제 인센티브 제공",
                "content_statement": "NPU 기반 AI컴퓨팅 인프라·설비 투자에 대한 세액 공제를 통해 수요기업 도입 인센티브를 제공한다.",
                "content_summary": "세제 인센티브로 수요기업 도입을 촉진한다.",
                "content_type": "tax_incentive",
                "display_order": 2,
                "evidence_policy_item_ids": ["ITM-POL-005-00306"],
            },
        ],
    },
    {
        "policy_item_group_id": "PIG-POL-005-03",
        "policy_bucket_id": "PBK-POL-005-03",
        "group_label": "AI반도체 인재양성 체계",
        "group_summary": "글로벌·고급 인재와 현장형 실무인재 양성을 함께 보여주는 인재 샘플",
        "group_description": "AI반도체 고급 인재와 실무형 인재 양성을 하나의 대표 항목으로 묶은 샘플 큐레이션이다.",
        "group_status": "sample_curated",
        "source_basis_type": "manual_sample",
        "display_order": 1,
        "taxonomies": [
            {"taxonomy_type": "strategy", "term_id": "STR-002", "is_primary": 1},
            {"taxonomy_type": "tech_domain", "term_id": "TD-009", "is_primary": 1},
            {"taxonomy_type": "tech_subdomain", "term_id": "TSD-009-001", "is_primary": 1},
        ],
        "members": [
            {"policy_item_id": "ITM-POL-005-00312", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00313", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00314", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00315", "member_role": "supporting_item", "is_representative": 0},
            {"policy_item_id": "ITM-POL-005-00317", "member_role": "representative_item", "is_representative": 1},
        ],
        "contents": [
            {
                "policy_item_content_id": "PIC-POL-005-03-01",
                "content_label": "글로벌·고급 인재 양성",
                "content_statement": "글로벌 기업·대학 연계교육과 학·석사 연계과정을 통해 AI반도체 고급 인재를 양성한다.",
                "content_summary": "글로벌 연계형 고급 인재를 양성한다.",
                "content_type": "advanced_talent_training",
                "display_order": 1,
                "evidence_policy_item_ids": [
                    "ITM-POL-005-00312",
                    "ITM-POL-005-00315",
                ],
            },
            {
                "policy_item_content_id": "PIC-POL-005-03-02",
                "content_label": "현장형 실무인재 및 재교육",
                "content_statement": "체험형 실습교육과 재직자 재교육을 통해 팹리스 현장형 설계 인력을 양성한다.",
                "content_summary": "현장형 실무인재와 재직자 재교육을 함께 추진한다.",
                "content_type": "workforce_training",
                "display_order": 2,
                "evidence_policy_item_ids": [
                    "ITM-POL-005-00313",
                    "ITM-POL-005-00314",
                    "ITM-POL-005-00317",
                ],
            },
        ],
    },
]

SAMPLE_PACK_INTENDED_USES = [
    "Dashboard drill-down prototyping for group-content-evidence navigation",
    "Ontology discussion around PolicyItemGroup and PolicyItemContent shape",
    "Reference example for how multiple raw policy_items can be grouped into one curated item",
]

SAMPLE_PACK_NON_GOALS = [
    "Authoritative full-policy curation",
    "Strict implementation contract for every evidence object type",
    "Replacement for source asset master or derived_to_source_asset_map validation",
]

SAMPLE_PACK_LIMITATIONS = [
    "This pack is a manual sample, not an authoritative full curation layer.",
    "Current sample evidence is still paragraph-first; it includes one canonical_table example and one figure example.",
    "Current sample taxonomy examples include strategy, tech_domain, and tech_subdomain, but not every group is exhaustively curated.",
    "Use ontology master tables and validation outputs for strict traceability checks.",
]


def read_lookup(connection: sqlite3.Connection, sql: str) -> dict[str, dict[str, str]]:
    rows = connection.execute(sql).fetchall()
    return {row[0]: dict(row) for row in rows}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_sources_by_rep_from_csv(
    derived_map_csv: Path,
    source_assets_csv: Path,
) -> dict[str, list[dict[str, str]]]:
    with source_assets_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        source_asset_rows = list(csv.DictReader(handle))
    source_asset_lookup = {row["source_asset_id"]: row for row in source_asset_rows}

    with derived_map_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        derived_map_rows = list(csv.DictReader(handle))

    sources_by_rep: dict[str, list[dict[str, str]]] = {}
    for row in derived_map_rows:
        source_asset = source_asset_lookup.get(row["source_asset_id"])
        if not source_asset:
            continue
        sources_by_rep.setdefault(row["derived_representation_id"], []).append(
            {
                "derived_representation_id": row["derived_representation_id"],
                "source_asset_id": source_asset["source_asset_id"],
                "asset_type": source_asset["asset_type"],
                "asset_path_or_url": source_asset["asset_path_or_url"],
                "page_no": source_asset["page_no"],
                "section_id": source_asset["section_id"],
            }
        )
    return sources_by_rep


def build_evidence_json(
    rep: dict[str, str],
    source_assets: list[dict[str, str]],
    *,
    source_policy_item_id: str = "",
    source_policy_item_label: str = "",
    evidence_label: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "derived_representation_id": rep["derived_representation_id"],
        "source_object_type": rep["source_object_type"],
        "source_object_id": rep["source_object_id"],
        "representation_type": rep["representation_type"],
        "document_id": rep["document_id"],
        "location_type": rep["location_type"],
        "location_value": rep["location_value"],
        "evidence_text": rep["plain_text"],
        "structured_payload_path": rep["structured_payload_path"],
        "table_json_path": rep["table_json_path"],
        "source_assets": source_assets,
    }
    if source_policy_item_id:
        payload["source_policy_item_id"] = source_policy_item_id
    if source_policy_item_label:
        payload["source_policy_item_label"] = source_policy_item_label
    if evidence_label:
        payload["evidence_label"] = evidence_label
    return payload


def load_legacy_policy_item_rep_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and all(isinstance(value, str) for value in payload.values()):
        return {str(key): value for key, value in payload.items()}
    lookup: dict[str, str] = {}
    for policy in payload.get("policies", []):
        for bucket in policy.get("buckets", []):
            for group in bucket.get("groups", []):
                for member in group.get("member_items", []):
                    policy_item_id = member.get("policy_item_id", "")
                    derived_representation_id = member.get("derived_representation_id", "")
                    if policy_item_id and derived_representation_id:
                        lookup[policy_item_id] = derived_representation_id
                for content in group.get("contents", []):
                    for evidence in content.get("evidence", []):
                        policy_item_id = evidence.get("source_policy_item_id", "")
                        derived_representation_id = evidence.get("derived_representation_id", "")
                        if policy_item_id and derived_representation_id:
                            lookup.setdefault(policy_item_id, derived_representation_id)
    return lookup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--derived-map-csv")
    parser.add_argument("--source-assets-csv")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        item_lookup = read_lookup(
            connection,
            """
            SELECT
                pi.policy_item_id,
                pi.policy_bucket_id,
                pi.item_label,
                pi.item_statement,
                pi.item_description,
                pb.policy_id,
                p.policy_name,
                rc.resource_category_id,
                rc.display_label AS resource_category_label
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN policies p ON p.policy_id = pb.policy_id
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            """,
        )
        rep_lookup = read_lookup(
            connection,
            """
            SELECT
                l.policy_item_id,
                l.derived_representation_id,
                dr.document_id,
                dr.source_object_type,
                dr.source_object_id,
                dr.representation_type,
                dr.location_type,
                dr.location_value,
                dr.plain_text,
                dr.structured_payload_path,
                dr.table_json_path
            FROM policy_item_evidence_links l
            JOIN derived_representations dr ON dr.derived_representation_id = l.derived_representation_id
            WHERE l.is_primary = 1
            """,
        )
        item_id_by_rep_id = {
            rep["derived_representation_id"]: policy_item_id
            for policy_item_id, rep in rep_lookup.items()
        }
        derived_lookup = read_lookup(
            connection,
            """
            SELECT
                dr.derived_representation_id,
                dr.document_id,
                dr.source_object_type,
                dr.source_object_id,
                dr.representation_type,
                dr.location_type,
                dr.location_value,
                dr.plain_text,
                dr.structured_payload_path,
                dr.table_json_path
            FROM derived_representations dr
            """
        )
        if args.derived_map_csv and args.source_assets_csv:
            sources_by_rep = load_sources_by_rep_from_csv(
                Path(args.derived_map_csv),
                Path(args.source_assets_csv),
            )
        else:
            source_rows = connection.execute(
                """
                SELECT
                    map.derived_representation_id,
                    sa.source_asset_id,
                    sa.asset_type,
                    sa.asset_path_or_url,
                    sa.page_no,
                    sa.section_id
                FROM derived_to_source_asset_map map
                JOIN source_assets sa ON sa.source_asset_id = map.source_asset_id
                ORDER BY map.derived_representation_id, map.is_primary DESC, sa.source_asset_id
                """
            ).fetchall()
            sources_by_rep = {}
            for row in source_rows:
                sources_by_rep.setdefault(row["derived_representation_id"], []).append(dict(row))

        strategy_lookup = read_lookup(connection, "SELECT strategy_id, strategy_label FROM strategies")
        tech_domain_lookup = read_lookup(connection, "SELECT tech_domain_id, tech_domain_label FROM tech_domains")
        tech_subdomain_lookup = read_lookup(
            connection,
            "SELECT tech_subdomain_id, tech_subdomain_label FROM tech_subdomains",
        )

        groups_rows: list[dict[str, object]] = []
        group_members_rows: list[dict[str, object]] = []
        contents_rows: list[dict[str, object]] = []
        content_evidence_rows: list[dict[str, object]] = []
        group_taxonomy_rows: list[dict[str, object]] = []
        display_rows: list[dict[str, object]] = []
        sample_json_policies: dict[str, dict[str, object]] = {}
        representation_types_in_pack: set[str] = set()
        taxonomy_types_in_pack: set[str] = set()
        legacy_item_rep_map = load_legacy_policy_item_rep_map(LEGACY_POLICY_ITEM_REP_MAP_PATH)

        def resolve_policy_item_id(policy_item_id: str) -> str:
            if policy_item_id in item_lookup and policy_item_id in rep_lookup:
                return policy_item_id
            derived_representation_id = legacy_item_rep_map.get(policy_item_id, "")
            if derived_representation_id:
                resolved_policy_item_id = item_id_by_rep_id.get(derived_representation_id, "")
                if resolved_policy_item_id:
                    return resolved_policy_item_id
            raise KeyError(policy_item_id)

        for group in SAMPLE_GROUPS:
            groups_rows.append(
                {
                    "policy_item_group_id": group["policy_item_group_id"],
                    "policy_bucket_id": group["policy_bucket_id"],
                    "group_label": group["group_label"],
                    "group_summary": group["group_summary"],
                    "group_description": group["group_description"],
                    "group_status": group["group_status"],
                    "source_basis_type": group["source_basis_type"],
                    "display_order": group["display_order"],
                    "notes": "sample_pack_2026-03-14",
                }
            )
            display_rows.append(
                {
                    "display_text_id": f"DSP-GRP-{group['policy_item_group_id']}",
                    "target_object_type": "policy_item_group",
                    "target_object_id": group["policy_item_group_id"],
                    "display_role": "policy_item_group_card",
                    "title_text": group["group_label"],
                    "summary_text": group["group_summary"],
                    "description_text": group["group_description"],
                    "generated_by": "manual_sample",
                    "review_status": "reviewed",
                    "source_basis_type": "manual_sample",
                    "notes": "sample_pack_2026-03-14",
                }
            )

            member_items_json = []
            for index, member in enumerate(group["members"], start=1):
                resolved_policy_item_id = resolve_policy_item_id(member["policy_item_id"])
                item = item_lookup[resolved_policy_item_id]
                rep = rep_lookup[resolved_policy_item_id]
                group_members_rows.append(
                    {
                        "policy_item_group_member_id": f"PGM-{group['policy_item_group_id']}-{index:02d}",
                        "policy_item_group_id": group["policy_item_group_id"],
                        "policy_item_id": resolved_policy_item_id,
                        "member_role": member["member_role"],
                        "is_representative": member["is_representative"],
                        "confidence": "high",
                        "notes": "sample_pack_2026-03-14",
                    }
                )
                member_items_json.append(
                    {
                        "policy_item_id": resolved_policy_item_id,
                        "item_label": item["item_label"],
                        "item_statement": item["item_statement"],
                        "member_role": member["member_role"],
                        "is_representative": bool(member["is_representative"]),
                        "derived_representation_id": rep["derived_representation_id"],
                    }
                )

            taxonomy_json = []
            for taxonomy in group["taxonomies"]:
                taxonomy_types_in_pack.add(taxonomy["taxonomy_type"])
                label = ""
                if taxonomy["taxonomy_type"] == "strategy":
                    label = strategy_lookup[taxonomy["term_id"]]["strategy_label"]
                elif taxonomy["taxonomy_type"] == "tech_domain":
                    label = tech_domain_lookup[taxonomy["term_id"]]["tech_domain_label"]
                elif taxonomy["taxonomy_type"] == "tech_subdomain":
                    label = tech_subdomain_lookup[taxonomy["term_id"]]["tech_subdomain_label"]
                group_taxonomy_rows.append(
                    {
                        "policy_item_group_taxonomy_map_id": f"PGT-{group['policy_item_group_id']}-{taxonomy['taxonomy_type']}-{taxonomy['term_id']}",
                        "policy_item_group_id": group["policy_item_group_id"],
                        "taxonomy_type": taxonomy["taxonomy_type"],
                        "term_id": taxonomy["term_id"],
                        "is_primary": taxonomy["is_primary"],
                        "confidence": "high",
                        "review_status": "reviewed",
                        "notes": "sample_pack_2026-03-14",
                    }
                )
                taxonomy_json.append(
                    {
                        "taxonomy_type": taxonomy["taxonomy_type"],
                        "term_id": taxonomy["term_id"],
                        "label": label,
                        "is_primary": bool(taxonomy["is_primary"]),
                    }
                )

            contents_json = []
            for content in group["contents"]:
                contents_rows.append(
                    {
                        "policy_item_content_id": content["policy_item_content_id"],
                        "policy_item_group_id": group["policy_item_group_id"],
                        "content_label": content["content_label"],
                        "content_statement": content["content_statement"],
                        "content_summary": content["content_summary"],
                        "content_type": content["content_type"],
                        "content_status": "sample_curated",
                        "display_order": content["display_order"],
                        "notes": "sample_pack_2026-03-14",
                    }
                )
                display_rows.append(
                    {
                        "display_text_id": f"DSP-CNT-{content['policy_item_content_id']}",
                        "target_object_type": "policy_item_content",
                        "target_object_id": content["policy_item_content_id"],
                        "display_role": "policy_item_content_card",
                        "title_text": content["content_label"],
                        "summary_text": content["content_summary"],
                        "description_text": content["content_statement"],
                        "generated_by": "manual_sample",
                        "review_status": "reviewed",
                        "source_basis_type": "manual_sample",
                        "notes": "sample_pack_2026-03-14",
                    }
                )
                evidence_json = []
                for evidence_index, policy_item_id in enumerate(content["evidence_policy_item_ids"], start=1):
                    resolved_policy_item_id = resolve_policy_item_id(policy_item_id)
                    item = item_lookup[resolved_policy_item_id]
                    rep = rep_lookup[resolved_policy_item_id]
                    representation_types_in_pack.add(rep["representation_type"])
                    content_evidence_rows.append(
                        {
                            "policy_item_content_evidence_link_id": f"CEL-{content['policy_item_content_id']}-{evidence_index:02d}",
                            "policy_item_content_id": content["policy_item_content_id"],
                            "derived_representation_id": rep["derived_representation_id"],
                            "link_role": "primary_support" if evidence_index == 1 else "secondary_support",
                            "evidence_strength": "high" if evidence_index == 1 else "medium",
                            "is_primary": 1 if evidence_index == 1 else 0,
                            "sort_order": evidence_index,
                            "notes": resolved_policy_item_id,
                        }
                    )
                    evidence_json.append(
                        build_evidence_json(
                            rep,
                            sources_by_rep.get(rep["derived_representation_id"], []),
                            source_policy_item_id=resolved_policy_item_id,
                            source_policy_item_label=item["item_label"],
                        )
                    )
                extra_evidence_specs = content.get("extra_evidence_specs", [])
                for extra_index, extra_spec in enumerate(extra_evidence_specs, start=len(content["evidence_policy_item_ids"]) + 1):
                    rep = derived_lookup[extra_spec["derived_representation_id"]]
                    representation_types_in_pack.add(rep["representation_type"])
                    content_evidence_rows.append(
                        {
                            "policy_item_content_evidence_link_id": f"CEL-{content['policy_item_content_id']}-{extra_index:02d}",
                            "policy_item_content_id": content["policy_item_content_id"],
                            "derived_representation_id": rep["derived_representation_id"],
                            "link_role": extra_spec.get("link_role", "secondary_support"),
                            "evidence_strength": extra_spec.get("evidence_strength", "medium"),
                            "is_primary": 0,
                            "sort_order": extra_index,
                            "notes": extra_spec.get("source_policy_item_id", rep["source_object_id"]),
                        }
                    )
                    source_policy_item_id = extra_spec.get("source_policy_item_id", "")
                    if source_policy_item_id:
                        try:
                            source_policy_item_id = resolve_policy_item_id(source_policy_item_id)
                        except KeyError:
                            pass
                    source_policy_item_label = ""
                    if source_policy_item_id and source_policy_item_id in item_lookup:
                        source_policy_item_label = item_lookup[source_policy_item_id]["item_label"]
                    evidence_json.append(
                        build_evidence_json(
                            rep,
                            sources_by_rep.get(rep["derived_representation_id"], []),
                            source_policy_item_id=source_policy_item_id,
                            source_policy_item_label=source_policy_item_label,
                            evidence_label=extra_spec.get("evidence_label", ""),
                        )
                    )
                contents_json.append(
                    {
                        "policy_item_content_id": content["policy_item_content_id"],
                        "content_label": content["content_label"],
                        "content_statement": content["content_statement"],
                        "content_summary": content["content_summary"],
                        "content_type": content["content_type"],
                        "display_order": content["display_order"],
                        "evidence": evidence_json,
                    }
                )

            representative_item = item_lookup[resolve_policy_item_id(group["members"][0]["policy_item_id"])]
            policy_node = sample_json_policies.setdefault(
                representative_item["policy_id"],
                {
                    "policy_id": representative_item["policy_id"],
                    "policy_name": representative_item["policy_name"],
                    "buckets": {},
                },
            )
            bucket_node = policy_node["buckets"].setdefault(
                group["policy_bucket_id"],
                {
                    "policy_bucket_id": group["policy_bucket_id"],
                    "resource_category_id": representative_item["resource_category_id"],
                    "resource_category_label": representative_item["resource_category_label"],
                    "groups": [],
                },
            )
            bucket_node["groups"].append(
                {
                    "policy_item_group_id": group["policy_item_group_id"],
                    "group_label": group["group_label"],
                    "group_summary": group["group_summary"],
                    "group_description": group["group_description"],
                    "taxonomies": taxonomy_json,
                    "member_items": member_items_json,
                    "contents": contents_json,
                }
            )

        included_representation_types = sorted(representation_types_in_pack)
        included_taxonomy_types = sorted(taxonomy_types_in_pack)
        sample_payload = {
            "sample_scope": {
                "pack_id": "content-evidence-sample-pack-2026-03-14",
                "contract_level": "manual_sample_reference",
                "strict_implementation_contract": False,
                "generated_from": "current_raw_policy_items",
                "purpose": "Provide a small manual sample of the policy group-content-evidence structure for dashboard prototyping and ontology discussion.",
                "intended_uses": SAMPLE_PACK_INTENDED_USES,
                "non_goals": SAMPLE_PACK_NON_GOALS,
                "coverage": {
                    "included_representation_types": included_representation_types,
                    "included_taxonomy_types": included_taxonomy_types,
                    "omitted_example_types": [],
                },
                "traceability_basis": "Each evidence.source_assets array is copied from the current derived_to_source_asset_map source used at build time for the same derived_representation_id.",
                "limitations": SAMPLE_PACK_LIMITATIONS,
                "policy_count": len(sample_json_policies),
                "group_count": len(groups_rows),
                "content_count": len(contents_rows),
            },
            "policies": [
                {
                    "policy_id": policy["policy_id"],
                    "policy_name": policy["policy_name"],
                    "buckets": list(policy["buckets"].values()),
                }
                for policy in sample_json_policies.values()
            ],
        }

        write_csv(
            out_dir / "policy_item_groups_sample.csv",
            [
                "policy_item_group_id",
                "policy_bucket_id",
                "group_label",
                "group_summary",
                "group_description",
                "group_status",
                "source_basis_type",
                "display_order",
                "notes",
            ],
            groups_rows,
        )
        write_csv(
            out_dir / "policy_item_group_members_sample.csv",
            [
                "policy_item_group_member_id",
                "policy_item_group_id",
                "policy_item_id",
                "member_role",
                "is_representative",
                "confidence",
                "notes",
            ],
            group_members_rows,
        )
        write_csv(
            out_dir / "policy_item_contents_sample.csv",
            [
                "policy_item_content_id",
                "policy_item_group_id",
                "content_label",
                "content_statement",
                "content_summary",
                "content_type",
                "content_status",
                "display_order",
                "notes",
            ],
            contents_rows,
        )
        write_csv(
            out_dir / "policy_item_content_evidence_links_sample.csv",
            [
                "policy_item_content_evidence_link_id",
                "policy_item_content_id",
                "derived_representation_id",
                "link_role",
                "evidence_strength",
                "is_primary",
                "sort_order",
                "notes",
            ],
            content_evidence_rows,
        )
        write_csv(
            out_dir / "policy_item_group_taxonomy_map_sample.csv",
            [
                "policy_item_group_taxonomy_map_id",
                "policy_item_group_id",
                "taxonomy_type",
                "term_id",
                "is_primary",
                "confidence",
                "review_status",
                "notes",
            ],
            group_taxonomy_rows,
        )
        write_csv(
            out_dir / "display_texts_curated_sample.csv",
            [
                "display_text_id",
                "target_object_type",
                "target_object_id",
                "display_role",
                "title_text",
                "summary_text",
                "description_text",
                "generated_by",
                "review_status",
                "source_basis_type",
                "notes",
            ],
            display_rows,
        )
        write_json(Path(args.out_json), sample_payload)
        write_json(
            Path(args.out_summary_json),
            {
                "contract_level": "manual_sample_reference",
                "policy_count": len(sample_json_policies),
                "group_count": len(groups_rows),
                "content_count": len(contents_rows),
                "group_member_count": len(group_members_rows),
                "content_evidence_count": len(content_evidence_rows),
                "group_taxonomy_count": len(group_taxonomy_rows),
                "display_text_count": len(display_rows),
                "included_representation_types": included_representation_types,
                "included_taxonomy_types": included_taxonomy_types,
                "limitations": SAMPLE_PACK_LIMITATIONS,
                "policies": [
                    {
                        "policy_id": policy["policy_id"],
                        "policy_name": policy["policy_name"],
                        "bucket_count": len(policy["buckets"]),
                    }
                    for policy in sample_payload["policies"]
                ],
            },
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
