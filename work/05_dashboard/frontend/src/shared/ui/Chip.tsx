import type { PropsWithChildren } from "react";
import { cn } from "../lib/cn";
import styles from "./primitives.module.css";

type ChipProps = PropsWithChildren<{
  tone?: "primary" | "neutral";
  className?: string;
}>;

export function Chip({ tone = "neutral", className, children }: ChipProps) {
  return (
    <span className={cn(styles.chip, tone === "primary" ? styles.chipPrimary : styles.chipNeutral, className)}>
      {children}
    </span>
  );
}
