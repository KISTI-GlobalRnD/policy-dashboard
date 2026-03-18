import { useEffect } from "react";
import { MappingWorkbenchPage } from "../modules/dashboard-ui/MappingWorkbenchPage";
import { buildAppUrl } from "../shared/lib/route";

function getViewMode(): "matrix" | "network" {
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view");
  const board = params.get("board");
  const normalizedView = (view ?? "").trim().toLowerCase();
  const normalizedBoard = (board ?? "").trim().toLowerCase();

  if (normalizedView === "network") {
    return "network";
  }

  if (normalizedView === "matrix" || normalizedView === "mapping" || normalizedView === "mapping-matrix" || normalizedView === "dashboard") {
    return "matrix";
  }

  if (normalizedBoard === "network" || normalizedBoard === "mapping-network") {
    return "network";
  }
  if (normalizedBoard === "matrix") {
    return "matrix";
  }

  return "matrix";
}

export function App() {
  const viewMode = getViewMode();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const view = (params.get("view") ?? "").trim().toLowerCase();
    const board = (params.get("board") ?? "").trim().toLowerCase();
    const isLegacyView = view === "" ? false : !["matrix", "network"].includes(view);
    const isLegacyBoard = board !== "" && board !== "network";

    if (!isLegacyView && !isLegacyBoard) {
      return;
    }

    params.set("view", viewMode);
    params.delete("board");
    const next = buildAppUrl(params);
    if (next !== `${window.location.pathname}${window.location.search}`) {
      window.history.replaceState({}, "", next);
    }
  }, [viewMode]);

  if (viewMode === "network") {
    return <MappingWorkbenchPage initialMode="network" />;
  }

  return <MappingWorkbenchPage initialMode="matrix" />;
}
