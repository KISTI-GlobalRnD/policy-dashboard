import { Panel } from "../../shared/ui/Panel";
import styles from "./DashboardWorkbenchPage.module.css";

const STEPS = [
  ["Export Lens", "export_technology_lens_projection.py"],
  ["Validate", "validate_technology_lens_projection.py"],
  ["Load Store", "run_ontology_enrichment_pipeline.py"],
  ["Sync Assets", "copy-dashboard-data.mjs"],
  ["Static Build", "vite build"],
];

export function PipelineStrip() {
  return (
    <Panel className={styles.pipelineStrip}>
      <div>
        <p className={styles.eyebrow}>Pipeline</p>
        <h2 className={styles.sectionTitle}>정적 앱이 읽는 생성 경로</h2>
        <p className={styles.sectionBody}>
          프론트엔드는 서버 없이 technology lens projection과 원문 자산만 읽는다. 즉 화면은 정적이지만, 내부
          정보 구조는 온톨로지 계층을 그대로 따른다.
        </p>
      </div>
      <div className={styles.pipelineSteps}>
        {STEPS.map(([label, detail], index) => (
          <article key={label} className={styles.pipelineStep}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{label}</strong>
            <p>{detail}</p>
          </article>
        ))}
      </div>
    </Panel>
  );
}
