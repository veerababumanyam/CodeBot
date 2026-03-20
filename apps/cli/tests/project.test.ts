import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  CodeBotClient,
  CodeBotAPIError,
} from "../src/client/api.js";
import { formatProjectTable } from "../src/output/formatters.js";
import type { ProjectResponse, PaginatedEnvelope } from "../src/types.js";

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function makeProject(overrides: Partial<ProjectResponse> = {}): ProjectResponse {
  return {
    id: "proj-001-abcdef",
    name: "TestProject",
    description: "A test project",
    status: "created",
    project_type: "greenfield",
    created_at: "2026-03-20T10:00:00Z",
    updated_at: "2026-03-20T10:00:00Z",
    ...overrides,
  };
}

describe("CodeBotClient - Projects", () => {
  let client: CodeBotClient;

  beforeEach(() => {
    vi.resetAllMocks();
    client = new CodeBotClient("http://localhost:8000", "test-token");
  });

  it("createProject calls POST /api/v1/projects and returns project data", async () => {
    const project = makeProject();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () =>
        Promise.resolve({
          status: "success",
          data: project,
          meta: { request_id: "r1", timestamp: "2026-03-20T10:00:00Z" },
        }),
    });

    const result = await client.createProject("TestProject", "A test project");

    expect(result.id).toBe("proj-001-abcdef");
    expect(result.name).toBe("TestProject");
    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, init] = mockFetch.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/projects");
    expect(init.method).toBe("POST");
    expect(init.headers.Authorization).toBe("Bearer test-token");
  });

  it("listProjects calls GET /api/v1/projects with pagination", async () => {
    const projects = [
      makeProject({ id: "p1", name: "Project A" }),
      makeProject({ id: "p2", name: "Project B" }),
    ];
    const envelope: PaginatedEnvelope<ProjectResponse> = {
      status: "success",
      data: projects,
      meta: { request_id: "r2", timestamp: "2026-03-20T10:00:00Z" },
      pagination: { page: 1, per_page: 20, total: 2, total_pages: 1 },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope),
    });

    const result = await client.listProjects(1, 20);

    expect(result.data).toHaveLength(2);
    expect(result.data[0]!.name).toBe("Project A");
    expect(result.data[1]!.name).toBe("Project B");
    const [url] = mockFetch.mock.calls[0]!;
    expect(url).toContain("page=1");
    expect(url).toContain("per_page=20");
  });

  it("deleteProject calls DELETE /api/v1/projects/{id}", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: () => Promise.reject(new Error("no body")),
    });

    await client.deleteProject("proj-001");

    const [url, init] = mockFetch.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/projects/proj-001");
    expect(init.method).toBe("DELETE");
  });

  it("handles 401 auth error with CodeBotAPIError", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () =>
        Promise.resolve({
          status: "error",
          error: { code: "AUTH_REQUIRED", message: "Not authenticated" },
        }),
    });

    await expect(
      client.createProject("Test", "test"),
    ).rejects.toThrow(CodeBotAPIError);

    try {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: () =>
          Promise.resolve({
            status: "error",
            error: { code: "AUTH_REQUIRED", message: "Not authenticated" },
          }),
      });
      await client.createProject("Test", "test");
    } catch (err) {
      expect(err).toBeInstanceOf(CodeBotAPIError);
      expect((err as CodeBotAPIError).statusCode).toBe(401);
      expect((err as CodeBotAPIError).message).toBe("Not authenticated");
    }
  });
});

describe("formatProjectTable", () => {
  it("formats projects into a table string", () => {
    const projects = [
      makeProject({ id: "p1-long-uuid-val", name: "Alpha" }),
      makeProject({
        id: "p2-long-uuid-val",
        name: "Beta",
        status: "completed",
      }),
    ];

    const output = formatProjectTable(projects);

    expect(output).toContain("p1-long-uuid");
    expect(output).toContain("Alpha");
    expect(output).toContain("p2-long-uuid");
    expect(output).toContain("Beta");
    expect(output).toContain("---");
  });
});
