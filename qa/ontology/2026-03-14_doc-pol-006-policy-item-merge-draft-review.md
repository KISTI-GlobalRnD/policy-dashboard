# DOC-POL-006 Policy Item Merge Draft Review

## 대상

- 입력:
  - `work/04_ontology/instances/DOC-POL-006__classification-template.csv`
- 출력:
  - `work/04_ontology/merge_drafts/DOC-POL-006__policy-item-merge-draft.csv`
  - `work/04_ontology/merge_drafts/DOC-POL-006__policy-item-merge-draft-summary.json`

## 결과 요약

- classification row 수: 504
- merge candidate 수: 137
- merge primary로 시작했다가 필터에서 제외된 row 수: 59
- 제외 사유:
  - `background_tail`: 24
  - `example_scaffold`: 9
  - `no_action_no_taxonomy`: 8
  - `section_scaffold`: 6
  - `context_scaffold`: 5
  - `group_count_scaffold`: 3
  - `schedule_scaffold`: 2
  - `diagram_or_schedule_paragraph`: 1
  - `short_paragraph_scaffold`: 1
- continuation 부착 group 수: 14
- note/citation support 부착 group 수: 66
- 자원유형 추정값 보유 group 수: 88
- 전략 후보 보유 group 수: 55
- 기술분야 후보 보유 group 수: 26

## 잘 된 점

- `초전도체`, `선정절차`, `실무 추진협의체`처럼 대표 문단에 note/citation을 붙여 검토 단위를 줄였다.
- `citation`과 `note`는 merge draft에서 support evidence로 남고, 독립 policy item 후보로 튀지 않는다.
- 짧은 continuation paragraph는 같은 page 안에서 대표 문단에 붙일 수 있게 되어 split paragraph를 그대로 검토하지 않게 됐다.
- `참 고 초혁신경제 15대 프로젝트 세부 일정`, `시기 세부 일정`, `A社/B社/D社` 사례, `(...: 5개*)` 묶음 라벨, page 9 도식형 paragraph는 merge primary에서 제거됐다.

## 남은 이슈

- `3대분야`, `첨단소재․부품`, `혁신프로젝트(Kingpin) 본격추진`처럼 메타 선언이나 상위 묶음 성격의 bullet은 아직 primary candidate로 남아 있다.
- `방안 마련 필요`, `지원 필요`, `운영 필요`처럼 action cue와 필요 진술이 섞인 bullet은 아직 남아 있어 후속 수동 검토가 필요하다.
- `현재 → 개선` 비교형 bullet은 정책조치 후보로 유지했지만, 실제 ontology에서는 `policy item`이 아니라 `regulatory delta`로 따로 다루는 편이 더 맞을 수 있다.
- 현재 merge rule은 `same-page adjacency` 중심이라, 의미상 이어지는 문단이라도 page가 바뀌면 묶지 못한다.

## 판단

현재 결과는 `정식 ontology 적재본`이 아니라 `수동 큐레이션 전 draft`로는 적절하다.
특히 `일정표`, `도식`, `사례 인용`, `n개 묶음 라벨` 제거까지는 안정화됐고, 남은 문제는 `메타 추진선언`과 `need-type bullet`에 집중되어 있다.
다음 단계는 아래 두 갈래다.

- classification 단계에서 `메타 추진선언`, `상위 묶음 bullet`을 더 `no/review`로 내린다.
- merge 단계에서 `need-type bullet`과 `현재/개선 비교형`을 별도 role로 분기할지 결정한다.
