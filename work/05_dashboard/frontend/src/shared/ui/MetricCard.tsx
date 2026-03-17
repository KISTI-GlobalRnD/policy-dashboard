import type { CSSProperties } from "react";
import { cn } from "../lib/cn";
import styles from "./primitives.module.css";

type MetricCardProps = {
  label: string;
  value: string;
  description: string;
  accent: string;
  className?: string;
};

export function MetricCard({ label, value, description, accent, className }: MetricCardProps) {
  const style = {
    "--metric-accent": accent,
  } as CSSProperties;

  return (
    <article className={cn(styles.metricCard, className)} style={style}>
      <span className={styles.metricLabel}>{label}</span>
      <strong className={styles.metricValue}>{value}</strong>
      <p className={styles.metricDescription}>{description}</p>
    </article>
  );
}
