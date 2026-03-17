import type { ReviewStatus } from "../dashboard-data/dashboard.types";
import type { ReviewStateSummary } from "../dashboard-model/mappingWorkbenchSelectors";

export function getReviewStatusLabel(status: ReviewStatus) {
  return status === "reviewed" ? "리뷰 완료" : "리뷰 필요";
}

export function getReviewStateSummaryLabel(status: ReviewStateSummary) {
  if (status === "reviewed") {
    return "리뷰 완료";
  }

  if (status === "needs_review") {
    return "리뷰 필요";
  }

  if (status === "mixed") {
    return "혼합";
  }

  return "없음";
}

export function getReviewStateSummaryShortLabel(status: ReviewStateSummary) {
  if (status === "reviewed") {
    return "완료";
  }

  if (status === "needs_review") {
    return "필요";
  }

  if (status === "mixed") {
    return "혼합";
  }

  return "없음";
}
