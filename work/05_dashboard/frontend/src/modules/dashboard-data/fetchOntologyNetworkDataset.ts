import technologyLensProjectionJson from "../../../../data-contracts/technology-lens.json";
import { technologyLensProjectionSchema } from "./dashboard.schema";
import type { TechnologyLensProjection } from "./dashboard.types";

const STATIC_TECHNOLOGY_LENS_DATA = (() => {
  try {
    return technologyLensProjectionSchema.parse(technologyLensProjectionJson);
  } catch {
    return technologyLensProjectionSchema.parse({});
  }
})();

export async function fetchOntologyNetworkDataset(): Promise<TechnologyLensProjection> {
  return STATIC_TECHNOLOGY_LENS_DATA;
}
