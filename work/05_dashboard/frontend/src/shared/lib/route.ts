export function getAppPathname(): string {
  return window.location.pathname;
}

export function buildAppUrl(params: URLSearchParams): string {
  const query = params.toString();
  return `${getAppPathname()}${query ? `?${query}` : ""}`;
}

export function withCurrentSearch(mutator: (params: URLSearchParams) => void): string {
  const params = new URLSearchParams(window.location.search);
  mutator(params);
  return buildAppUrl(params);
}

