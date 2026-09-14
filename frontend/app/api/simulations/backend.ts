export function backendUrl(path: string): string {
  const configured =
    process.env.BACKEND_API_URL ??
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    "http://127.0.0.1:8000";
  const normalized = configured.replace(/\/$/, "");
  const apiBase = normalized.endsWith("/api/v1") ? normalized : `${normalized}/api/v1`;
  return `${apiBase}${path}`;
}

export async function upstream(path: string, init?: RequestInit): Promise<Response> {
  return fetch(backendUrl(path), { ...init, cache: "no-store", signal: AbortSignal.timeout(15_000) });
}
