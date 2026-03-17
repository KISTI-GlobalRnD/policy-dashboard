# DOC-POL-006 Figure BBox Gap

## 목적

- `DOC-POL-006`의 figure-adjacent 본문 잡음을 자동으로 줄일 수 있는지 확인

## 확인 결과

- `work/02_structured-extraction/figures` 아래 `FIG-DOC-POL-006-*.json` 파일은 존재한다.
- 그러나 현재 figure payload의 `source_bbox`는 전부 `null`이다.
- manifest 집계에는 `pages_with_images_markdown: 6`이 있으나, paragraph 정규화 단계에서 image bbox를 활용할 수 있는 상태는 아니다.

## 영향

- 표는 bbox overlap으로 pure text에서 제외할 수 있지만, figure/diagram은 현재 같은 방식의 자동 제외가 불가능하다.
- page 30 전후의 생태계 도식처럼 figure-adjacent 텍스트가 pure text에 섞이는 이유가 여기 있다.

## 판단

- 다음 단계에서 figure 영역 정리를 자동화하려면 PDF extractor에서 image bbox를 저장해야 한다.
- 그 전까지는 `DOC-POL-006`의 figure-adjacent 영역은 수동 검토 또는 heuristic suppression 범위로 다룰 수밖에 없다.
