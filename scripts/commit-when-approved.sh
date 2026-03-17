#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/commit-when-approved.sh \"커밋 메시지\"" >&2
  exit 1
fi

message="$1"
shift

if [[ -n "${GIT_COMMIT_FORCE:-}" ]]; then
  git commit "$@" -m "$message"
  exit 0
fi

printf '현재 변경 요약:\n'
git status --short
printf '\n이 변경으로 커밋하겠습니까? [y/N]: '
read -r answer

if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
  echo '커밋이 취소되었습니다.'
  exit 1
fi

git add -A
git commit "$@" -m "$message"
echo '커밋이 완료되었습니다.'
