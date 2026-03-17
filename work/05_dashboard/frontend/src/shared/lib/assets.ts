const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"];

export function sanitizeAssetPath(path: string | undefined) {
  if (!path) {
    return null;
  }

  return path.split("::")[0]?.replace(/^\.?\//, "") ?? null;
}

function getExtension(path: string) {
  const normalized = path.toLowerCase();
  const match = normalized.match(/\.[a-z0-9]+$/);
  return match?.[0] ?? "";
}

export function getAssetPreviewKind(path: string | undefined) {
  const sanitizedPath = sanitizeAssetPath(path);
  if (!sanitizedPath) {
    return "none" as const;
  }

  const extension = getExtension(sanitizedPath);
  if (IMAGE_EXTENSIONS.includes(extension)) {
    return "image" as const;
  }

  if (extension === ".pdf") {
    return "pdf" as const;
  }

  return "unsupported" as const;
}

export function resolveAssetHref(path: string | undefined) {
  const sanitizedPath = sanitizeAssetPath(path);
  if (!sanitizedPath) {
    return null;
  }

  if (path?.startsWith("http://") || path?.startsWith("https://")) {
    return path;
  }

  const raw = import.meta.env.DEV
    ? `/@fs/${__REPO_ROOT__}/${sanitizedPath}`
    : `${import.meta.env.BASE_URL}source-assets/${sanitizedPath}`;

  return encodeURI(raw);
}
