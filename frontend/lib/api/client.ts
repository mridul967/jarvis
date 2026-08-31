type FetchOptions = RequestInit & {
  next?: { revalidate?: number | false; tags?: string[] };
};

export async function api<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const base =
    typeof window === "undefined"
      ? (process.env.INTERNAL_API_URL ?? "http://localhost:8000")
      : "";
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      detail?.detail ?? `API request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}
