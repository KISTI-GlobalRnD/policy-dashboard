# DOC-POL-006 Table Review Queue Review

## 대상

- 문서 ID: `DOC-POL-006`
- 검토 큐: `qa/extraction/review_queues/DOC-POL-006__table-review-queue.csv`

## 결과 요약

- review item 수: 30
- Markdown 표 후보: 10
- `find_tables()` 표 후보: 20

자동 분류 결과:

- `structured_table`: 16
- `layout_false_positive`: 7
- `fragment_or_broken`: 3
- `multi_page_fragment`: 2
- `review_required`: 2

## 확인 사항

- page chunk Markdown 표와 `find_tables()` 결과를 한 큐에서 비교할 수 있다.
- page 2, 3 같은 제목 박스형 false positive가 자동으로 위로 올라온다.
- page 36~38 일정표 조각처럼 병합 검토가 필요한 후보도 따로 보인다.
- `candidate_source`가 분리되어 있어 추출 경로별 신뢰도를 비교하기 쉽다.

## 한계

- `structured_table` 제안은 shape 중심이라 확정값이 아니다.
- `visual_table`은 아직 자동으로 잘 잡지 못한다.
- page 26처럼 page chunk 쪽에 누락된 표는 `find_tables()` 경로에 의존한다.

## 판단

표는 앞으로도 rule-only로 닫지 않는 게 맞다.
현재 검토 큐 방식이면 자동 추출과 사람 검토를 함께 운영할 수 있다.
