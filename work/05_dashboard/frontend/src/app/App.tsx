import { DashboardWorkbenchPage } from "../modules/dashboard-ui/DashboardWorkbenchPage";
import { MappingWorkbenchPage } from "../modules/dashboard-ui/MappingWorkbenchPage";

function getViewMode(): "dashboard" | "mapping-matrix" | "mapping-network" {
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view");
  const board = params.get("board");

  if (view === "dashboard") {
    return "dashboard";
  }

  if (view === "network" || board === "network") {
    return "mapping-network";
  }

  if (view === "mapping") {
    return "mapping-matrix";
  }

  return "dashboard";
}

export function App() {
  const viewMode = getViewMode();

  if (viewMode === "mapping-network") {
    return <MappingWorkbenchPage initialMode="network" />;
  }

  if (viewMode === "mapping-matrix") {
    return <MappingWorkbenchPage initialMode="matrix" />;
  }

  return <DashboardWorkbenchPage />;
}
