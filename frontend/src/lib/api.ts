async function fetchJSON<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value) url.searchParams.set(key, value);
    }
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getMemories: (filters: {
    memory_type?: string;
    project_id?: string;
    search?: string;
  }) => fetchJSON("/api/v1/memories", filters),

  getMemoryStats: () => fetchJSON("/api/v1/memory-stats"),

  getEntities: (filters: {
    project_id?: string;
    entity_type?: string;
  }) => fetchJSON("/api/v1/entities", filters),

  getRelations: () => fetchJSON("/api/v1/relations"),

  getGraphStats: () => fetchJSON("/api/v1/graph-stats"),

  getEntityMemories: (entityId: string) =>
    fetchJSON(`/api/v1/entity-memories/${entityId}`),
};
