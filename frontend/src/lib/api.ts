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
  }) => fetchJSON("/api/memories", filters),

  getMemoryStats: () => fetchJSON("/api/memory-stats"),

  getEntities: (filters: {
    project_id?: string;
    entity_type?: string;
  }) => fetchJSON("/api/entities", filters),

  getRelations: () => fetchJSON("/api/relations"),

  getGraphStats: () => fetchJSON("/api/graph-stats"),

  getEntityMemories: (entityId: string) =>
    fetchJSON(`/api/entity-memories/${entityId}`),
};
