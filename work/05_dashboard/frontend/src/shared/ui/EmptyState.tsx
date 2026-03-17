import styles from "./primitives.module.css";

type EmptyStateProps = {
  eyebrow: string;
  title: string;
  body: string;
};

export function EmptyState({ eyebrow, title, body }: EmptyStateProps) {
  return (
    <div className={styles.emptyState}>
      <p className={styles.emptyEyebrow}>{eyebrow}</p>
      <h2 className={styles.emptyTitle}>{title}</h2>
      <p className={styles.emptyBody}>{body}</p>
    </div>
  );
}
