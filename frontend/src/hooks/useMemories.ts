import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Memory, DashboardStats, MemoryFilters } from "@/types/memory";

export function useMemories(filters: MemoryFilters) {
  return useQuery({
    queryKey: ["memories", filters],
    queryFn: async () => {
      const data = await api.getMemories({
        memory_type: filters.memoryType ?? undefined,
        project_id: filters.projectId ?? undefined,
        search: filters.search || undefined,
      });
      return data as Memory[];
    },
  });
}

export function useMemoryStats() {
  return useQuery({
    queryKey: ["memory-stats"],
    queryFn: async () => {
      return (await api.getMemoryStats()) as DashboardStats;
    },
  });
}
