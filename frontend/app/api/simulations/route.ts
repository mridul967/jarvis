import { NextRequest, NextResponse } from "next/server";
import { upstream } from "./backend";

export async function POST(request: NextRequest) {
  try {
    const response = await upstream("/simulations", { method: "POST", headers: { "content-type": "application/json" }, body: await request.text() });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: `Backend proxy failed: ${error instanceof Error ? error.message : "unknown error"}` }, { status: 503 });
  }
}
