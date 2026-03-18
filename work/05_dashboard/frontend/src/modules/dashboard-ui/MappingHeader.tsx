import { MetricCard } from "../../shared/ui/MetricCard";
import { Chip } from "../../shared/ui/Chip";
import { formatNumber } from "../../shared/lib/format";
import styles from "./MappingWorkbenchPage.module.css";

type MappingHeaderProps = {
  packId: string;
  generatedFrom: string;
  totalPolicies: number;
  visiblePolicyCount: number;
  mappedDomainCount: number;
  mappedGroupCount: number;
  mappedContentCount: number;
  unmappedContentCount: number;
  reviewedContentCount: number;
};

export function MappingHeader({
  packId,
  generatedFrom,
  totalPolicies,
  visiblePolicyCount,
  mappedDomainCount,
  mappedGroupCount,
  mappedContentCount,
  unmappedContentCount,
  reviewedContentCount,
}: MappingHeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.headerCopy}>
        <p className={styles.eyebrow}>정책-기술 매핑 작업면</p>
        <h1 className={styles.headerTitle}>정책과 기술 대분류의 매핑 집중도를 빠르게 확인하는 작업면</h1>
        <p className={styles.headerBody}>
          정책-기술 연결 강도와 공백을 먼저 확인하고, 필요한 경우에만 대표 내용과 원문 근거로 드릴다운합니다.
        </p>
        <div className={styles.headerChips}>
          <Chip tone="primary">{packId}</Chip>
          <Chip>{generatedFrom}</Chip>
          <Chip>
            정책 {formatNumber(visiblePolicyCount)} / {formatNumber(totalPolicies)}
          </Chip>
          <Chip>14개 기술 대분류 기준</Chip>
        </div>
      </div>

      <div className={styles.metricGrid}>
        <MetricCard
          label="기술 대분류 커버리지"
          value={`${formatNumber(mappedDomainCount)} / 14`}
          description="현재 필터 결과에서 실제 매핑이 존재하는 기술 대분류 수"
          accent="var(--color-accent)"
        />
        <MetricCard
          label="매핑된 대표 그룹"
          value={formatNumber(mappedGroupCount)}
          description="기술 대분류에 연결된 대표 그룹 수"
          accent="var(--color-infra)"
        />
        <MetricCard
          label="매핑된 대표 내용"
          value={formatNumber(mappedContentCount)}
          description="기술 대분류 셀 안으로 들어가는 대표 내용 수"
          accent="var(--color-tech)"
        />
        <MetricCard
          label="미매핑 대표 내용"
          value={formatNumber(unmappedContentCount)}
          description="기술 대분류가 아직 붙지 않은 내용 수"
          accent="var(--color-talent)"
        />
        <MetricCard
          label="리뷰 완료 대표 내용"
          value={formatNumber(reviewedContentCount)}
          description="현재 필터 결과에서 매핑 리뷰가 완료된 대표 내용 수"
          accent="var(--color-warn)"
        />
      </div>
    </header>
  );
}
