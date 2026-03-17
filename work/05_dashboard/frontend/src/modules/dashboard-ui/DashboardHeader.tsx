import { Chip } from "../../shared/ui/Chip";
import { formatNumber } from "../../shared/lib/format";
import styles from "./DashboardWorkbenchPage.module.css";

type DashboardHeaderProps = {
  totalPolicies: number;
  totalGroups: number;
  totalContents: number;
  totalEvidence: number;
  matchedContents: number;
  activePolicyName: string | null;
  packId: string;
};

export function DashboardHeader({
  totalPolicies,
  totalGroups,
  totalContents,
  totalEvidence,
  matchedContents,
  activePolicyName,
  packId,
}: DashboardHeaderProps) {
  const signals = [
    {
      label: "정책",
      value: formatNumber(totalPolicies),
      meta: "projected policies",
    },
    {
      label: "대표 그룹",
      value: formatNumber(totalGroups),
      meta: "policy item groups",
    },
    {
      label: "대표 내용",
      value: formatNumber(totalContents),
      meta: "content nodes",
    },
    {
      label: "근거 링크",
      value: formatNumber(totalEvidence),
      meta: "content evidences",
    },
    {
      label: "현재 범위",
      value: formatNumber(matchedContents),
      meta: "filtered contents",
    },
  ];

  return (
    <header className={styles.masthead}>
      <div className={styles.mastheadCopy}>
        <p className={styles.eyebrow}>Technology Lens Projection</p>
        <h1 className={styles.mastheadTitle}>기술 축별 대표 정책 내용과 근거를 읽는 정적 대시보드</h1>
        <p className={styles.mastheadBody}>
          기술별 대표 항목은 <strong>PolicyItemGroup - PolicyItemContent - Evidence - SourceAsset</strong> 계층으로
          유지하되, curated 그룹과 provisional fallback을 한 화면에서 같이 읽는다. 대형 화면에서는 정책 인덱스,
          대표 내용 테이블, 원문 trace를 한 작업면 안에서 같이 본다.
        </p>
        <div className={styles.metaRow}>
          <Chip tone="primary">static React app</Chip>
          <Chip>technology lens pack</Chip>
          <Chip>{packId}</Chip>
          <Chip>{activePolicyName ?? "정책 전체 범위"}</Chip>
        </div>
      </div>
      <div className={styles.signalBoard}>
        <div className={styles.signalHead}>
          <div>
            <p className={styles.eyebrow}>Pack Signals</p>
            <h2 className={styles.signalTitle}>전체 모수와 현재 범위를 같이 본다</h2>
          </div>
          <p className={styles.signalBody}>
            상단은 요약 카드 더미가 아니라, 현재 샘플 팩의 크기와 필터 범위를 빠르게 읽는 데이터 스트립으로 유지한다.
          </p>
        </div>

        <div className={styles.signalStrip}>
          {signals.map((signal) => (
            <div key={signal.label} className={styles.signalCell}>
              <span className={styles.signalLabel}>{signal.label}</span>
              <strong className={styles.signalValue}>{signal.value}</strong>
              <span className={styles.signalMeta}>{signal.meta}</span>
            </div>
          ))}
        </div>

        <div className={styles.signalTape}>
          <span>{"tech -> policy -> group -> content -> evidence"}</span>
          <span>gold + provisional projection</span>
          <span>direct source links</span>
          <span>static build only</span>
        </div>
      </div>
    </header>
  );
}
