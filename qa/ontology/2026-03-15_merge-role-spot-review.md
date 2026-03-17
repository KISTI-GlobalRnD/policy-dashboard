# Merge Role Spot Review

## 대상

- `DOC-POL-005`
- `DOC-POL-006`
- `DOC-POL-010`

## 목적

`policy-item-merge-draft`에 추가한 `candidate_role_draft`가 실제 검토 작업지로 쓸 만한지 확인한다.

## 문서별 분포

- `DOC-POL-005`
  - `policy_action`: 197
  - `meta_program_frame`: 5
  - `problem_or_requirement`: 11
  - `background_context`: 8
  - `regulatory_delta`: 1
- `DOC-POL-006`
  - `policy_action`: 123
  - `meta_program_frame`: 9
  - `case_example`: 2
  - `regulatory_delta`: 3
- `DOC-POL-010`
  - `policy_action`: 72
  - `problem_or_requirement`: 8
  - `background_context`: 5
  - `meta_program_frame`: 1

## 잘 된 점

- `DOC-POL-006`의 `추진계획 발표`, `추진단 구성`, `3대분야`, `실무 추진협의체`는 `meta_program_frame`으로 분리된다.
- `DOC-POL-006`의 `현재 → 개선`, `본인인증의무 폐지`, `뮤직비디오 심의 개선`은 `regulatory_delta`로 안정적으로 잡힌다.
- `DOC-POL-006`의 기업 인용은 `case_example`으로 분기되어 일반 정책조치와 분리된다.
- `DOC-POL-010`의 `부작용 심화`, `저조하다는 지적`, `인재 유출 추세`는 `background_context` 또는 `problem_or_requirement`로 분리된다.
- role 판정은 support note가 아니라 `primary seed` 기준으로 이루어져, 대표 정책조치가 continuation 때문에 다른 role로 끌려가는 현상이 줄었다.

## 남은 이슈

- `DOC-POL-005`의 일부 `현장의견 ...` bullet은 `background_context`와 `problem_or_requirement` 경계에 있다.
- `DOC-POL-010`의 일부 실행문은 `policy_action`과 `problem_or_requirement` 경계에 있다.
- 현재 role은 reviewer override를 전제로 한 제안값이며, 바로 ontology 적재 상태값으로 보기에는 이르다.

## 판단

현재 `candidate_role_draft`는 `정책조치 / 메타 / 배경 / 문제·요구 / 사례인용 / 현행-개선`을 대략 가르는 용도로는 충분하다.
다음 단계는 role 자체를 더 세분화하는 것보다, 이 제안값을 reviewer override 전제의 작업지에 붙여 실제 검토를 진행하는 쪽이 더 생산적이다.
