import type { Report, SimulationConfig } from "../types";
const baseUrl = import.meta.env.VITE_API_URL ?? "";
export async function runSyntheticAnalysis(config: SimulationConfig): Promise<Report> { const response = await fetch(`${baseUrl}/api/v1/synthetic-analysis`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(config) }); if (!response.ok) throw new Error(`Analysis failed (${response.status})`); return response.json() as Promise<Report>; }
