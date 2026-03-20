const BASE = import.meta.env.VITE_API_URL ?? "";

let authToken: string | null = null;

export function setAuthToken(t: string | null): void {
  authToken = t;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (authToken) {
    h["Authorization"] = `Bearer ${authToken}`;
  }

  const init: RequestInit = { method, headers: h };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, init);

  if (!res.ok) {
    const e = await res.json().catch(() => ({
      error: { message: res.statusText },
    }));
    throw new Error(
      (e as { error?: { message?: string } }).error?.message ??
        `HTTP ${String(res.status)}`,
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(p: string) => request<T>("GET", p),
  post: <T>(p: string, b?: unknown) => request<T>("POST", p, b),
  patch: <T>(p: string, b?: unknown) => request<T>("PATCH", p, b),
  delete: <T>(p: string) => request<T>("DELETE", p),
};
