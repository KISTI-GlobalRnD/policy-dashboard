import technologyLensProjectionJson from "../../../../data-contracts/technology-lens.json";
import { technologyLensProjectionSchema } from "./dashboard.schema";
import type { TechnologyLensProjection } from "./dashboard.types";

const RUNTIME_TECHNOLOGY_LENS_PATH = "./data/technology-lens.json";

const buildDataUrl = (path: string) => new URL(path, window.location.href).toString();

export async function fetchOntologyNetworkDataset(): Promise<TechnologyLensProjection> {
  try {
    const runtimeResponse = await fetch(buildDataUrl(RUNTIME_TECHNOLOGY_LENS_PATH));
    if (runtimeResponse.ok) {
      return technologyLensProjectionSchema.parse(await runtimeResponse.json());
    }
  } catch {
    // Continue with repository fallback when runtime JSON is unavailable.
  }

  return technologyLensProjectionSchema.parse(technologyLensProjectionJson);
}

