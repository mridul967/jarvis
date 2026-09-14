import { NextResponse } from "next/server";
import { upstream } from "../backend";

export async function GET() {
  try {
    const response = await upstream("/simulations/audits");
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: `Backend proxy failed: ${error instanceof Error ? error.message : "unknown error"}` }, { status: 503 });
  }
}
