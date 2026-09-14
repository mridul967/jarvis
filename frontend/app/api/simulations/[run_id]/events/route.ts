import { NextResponse } from "next/server";
import { upstream } from "../../backend";

export async function GET(_: Request, context: { params: Promise<{ run_id: string }> }) {
  const { run_id } = await context.params;
  try {
    const response = await upstream(`/simulations/${run_id}/events`);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: `Backend proxy failed: ${error instanceof Error ? error.message : "unknown error"}` }, { status: 503 });
  }
}
