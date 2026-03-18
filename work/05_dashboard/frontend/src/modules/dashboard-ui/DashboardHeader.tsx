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
  mappingWorkbenchUrl: string;
  mappingNetworkUrl: string;
};

export function DashboardHeader({
  totalPolicies,
  totalGroups,
  totalContents,
  totalEvidence,
  matchedContents,
  activePolicyName,
  packId,
  mappingWorkbenchUrl,
  mappingNetworkUrl,
}: DashboardHeaderProps) {
  const signals = [
    {
      label: "정책",
      value: formatNumber(totalPolicies),
      meta: "총 대상 정책",
    },
    {
      label: "대표 그룹",
      value: formatNumber(totalGroups),
      meta: "정책 항목 그룹",
    },
    {
      label: "대표 내용",
      value: formatNumber(totalContents),
      meta: "정책 내용",
    },
    {
      label: "근거 링크",
      value: formatNumber(totalEvidence),
      meta: "근거 원문",
    },
    {
      label: "현재 범위",
      value: formatNumber(matchedContents),
      meta: "조회 범위",
    },
  ];

  return (
    <header className={styles.masthead}>
      <div className={styles.mastheadCopy}>
        <p className={styles.eyebrow}>Policy-Technology Dashboard</p>
        <h1 className={styles.mastheadTitle}>정책이 집중되는 기술영역을 한 화면에서 점검</h1>
        <p className={styles.mastheadBody}>
          정책별로 어떤 기술영역에 얼마나 많이 연결되는지와 각 연결 근거를 빠르게 확인합니다.
        </p>
        <div className={styles.metaRow}>
          <Chip tone="primary">static React app</Chip>
          <Chip>policy & technology pack</Chip>
          <Chip>{packId}</Chip>
          <Chip>{activePolicyName ?? "정책 전체 범위"}</Chip>
          <a href={mappingWorkbenchUrl} className={styles.headerLink}>
            정책-기술 매트릭스
          </a>
          <a href={mappingNetworkUrl} className={styles.headerLink}>
            정책-기술 네트워크
          </a>
        </div>
      </div>
      <div className={styles.signalBoard}>
        <div className={styles.signalHead}>
          <div>
            <p className={styles.eyebrow}>Pack Signals</p>
            <h2 className={styles.signalTitle}>전체 모수와 현재 범위를 같이 본다</h2>
          </div>
          <p className={styles.signalBody}>
            상단 지표는 실무 점검에 필요한 범위와 누적 수치를 빠르게 전달하기 위한 전용 요약입니다.
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
          <span>정책 · 기술영역 · 내용 · 근거 흐름</span>
          <span>근거 수집본 우선 정렬</span>
          <span>원문 링크 직접 연결</span>
          <span>정적 브라우저 빌드</span>
        </div>
      </div>
    </header>
  );
}
