import type { PropsWithChildren } from "react";
import { cn } from "../lib/cn";
import styles from "./primitives.module.css";

type PanelProps = PropsWithChildren<{
  className?: string;
}>;

export function Panel({ className, children }: PanelProps) {
  return <section className={cn(styles.panel, className)}>{children}</section>;
}
