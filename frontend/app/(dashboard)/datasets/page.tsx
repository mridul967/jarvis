import { DatasetManagerClient } from "./_components/dataset-manager-client";
import { getSampleInstance } from "@/lib/api/datasets";

export const dynamic = "force-dynamic";

export default async function DatasetsPage() {
  const sample = await getSampleInstance().catch(() => null);
  return <DatasetManagerClient sample={sample} />;
}
