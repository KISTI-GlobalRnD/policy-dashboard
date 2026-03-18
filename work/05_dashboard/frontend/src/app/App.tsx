import { MappingWorkbenchPage } from "../modules/dashboard-ui/MappingWorkbenchPage";

function getViewMode(): "mapping-matrix" | "mapping-network" {
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view");
  const board = params.get("board");
  const normalizedView = (view ?? "").trim().toLowerCase();
  const normalizedBoard = (board ?? "").trim().toLowerCase();

  if (normalizedView === "dashboard") {
    return "mapping-matrix";
  }

  if (
    normalizedView === "network" ||
    normalizedView === "mapping-network" ||
    normalizedView === "ontology-network" ||
    normalizedView === "ontology" ||
    normalizedView === "mapping-ontology-network" ||
    normalizedBoard === "network" ||
    normalizedBoard === "ontology-network" ||
    normalizedBoard === "ontology"
  ) {
    return "mapping-network";
  }

  if (normalizedView === "mapping" || normalizedView === "matrix" || normalizedView === "mapping-matrix") {
    return "mapping-matrix";
  }

  return "mapping-matrix";
}

export function App() {
  const viewMode = getViewMode();

  if (viewMode === "mapping-network") {
    return <MappingWorkbenchPage initialMode="network" />;
  }

  if (viewMode === "mapping-matrix") {
    return <MappingWorkbenchPage initialMode="matrix" />;
  }

  return <MappingWorkbenchPage initialMode="matrix" />;
}
