export type BlockItem = {
  id: string;
  block_id: string;
  position: number;
  visibility: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PublicStatsData = {
  public_repos: number;
  stars: number;
  top_languages: string[];
  contributions_last_year: number | null;
  active_parts: {
    night: number;
    morning: number;
    afternoon: number;
    evening: number;
  };
};

export type PublicStats = {
  data: PublicStatsData;
  fetched_at: string;
};

export type Block = {
  id: string;
  type: string;
  title: string;
  position: number;
  visibility: string;
  props: Record<string, unknown>;
  items: BlockItem[];
  stats?: PublicStats | null;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  csrfToken?: string,
): Promise<T | undefined> {
  if (!path.startsWith("/api/")) {
    throw new Error('API paths must start with "/api/".');
  }

  const headers = new Headers();
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (csrfToken !== undefined) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (response.status === 204) {
    return undefined;
  }

  const raw = await response.text();
  let payload: unknown;
  try {
    payload = raw ? (JSON.parse(raw) as unknown) : undefined;
  } catch {
    payload = undefined;
  }

  if (!response.ok) {
    let detail = "Request failed.";
    if (typeof payload === "object" && payload !== null && "detail" in payload) {
      const responseDetail = payload.detail;
      if (typeof responseDetail === "string") {
        detail = responseDetail;
      } else if (Array.isArray(responseDetail)) {
        const messages = responseDetail
          .map((item) => {
            if (typeof item !== "object" || item === null || !("msg" in item)) {
              return null;
            }
            return typeof item.msg === "string" ? item.msg : null;
          })
          .filter((message): message is string => message !== null);
        if (messages.length > 0) {
          detail = messages.join("; ");
        }
      }
    }
    throw new ApiError(response.status, detail);
  }

  return payload as T;
}

export function apiGet<T>(path: string): Promise<T | undefined> {
  return request<T>("GET", path);
}

export function apiSend<T>(
  method: string,
  path: string,
  body?: unknown,
  csrfToken?: string,
): Promise<T | undefined> {
  return request<T>(method, path, body, csrfToken);
}
