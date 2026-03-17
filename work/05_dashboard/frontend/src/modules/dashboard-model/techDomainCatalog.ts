export type TechDomainReference = {
  termId: string;
  label: string;
  shortLabel: string;
};

export const TECH_DOMAIN_REFERENCES: TechDomainReference[] = [
  { termId: "TD-001", label: "인공지능", shortLabel: "AI" },
  { termId: "TD-002", label: "에너지", shortLabel: "EN" },
  { termId: "TD-003", label: "이차전지", shortLabel: "BAT" },
  { termId: "TD-004", label: "국방", shortLabel: "DEF" },
  { termId: "TD-005", label: "소재", shortLabel: "MAT" },
  { termId: "TD-006", label: "사이버보안", shortLabel: "SEC" },
  { termId: "TD-007", label: "차세대통신", shortLabel: "NET" },
  { termId: "TD-008", label: "첨단로봇제조", shortLabel: "ROBO" },
  { termId: "TD-009", label: "반도체디스플레이", shortLabel: "SEMI" },
  { termId: "TD-010", label: "양자", shortLabel: "QNT" },
  { termId: "TD-011", label: "첨단바이오", shortLabel: "BIO" },
  { termId: "TD-012", label: "우주항공", shortLabel: "AERO" },
  { termId: "TD-013", label: "해양", shortLabel: "OCEAN" },
  { termId: "TD-014", label: "첨단모빌리티", shortLabel: "MOVE" },
];

export const TECH_DOMAIN_REFERENCE_MAP = new Map(TECH_DOMAIN_REFERENCES.map((entry) => [entry.termId, entry]));
