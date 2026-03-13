import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  GraphEntity,
  GraphRelation,
  GraphData,
  GraphStats,
  GraphFilters,
} from "@/types/graph";

const MAX_NODES = 200;

export function useGraphData(filters: GraphFilters) {
  return useQuery({
    queryKey: ["graph-data", filters],
    queryFn: async (): Promise<GraphData> => {
      // Fetch entities with project join
      let entities = (await api.getEntities({
        project_id: filters.projectId ?? undefined,
        entity_type: filters.entityType ?? undefined,
      })) as GraphEntity[];

      // Client-side search filter
      if (filters.search) {
        const q = filters.search.toLowerCase();
        entities = entities.filter(
          (e) =>
            e.name.toLowerCase().includes(q) ||
            e.description?.toLowerCase().includes(q)
        );
      }

      // Fetch all relations
      const allRelations = (await api.getRelations()) as GraphRelation[];

      // Filter relations to only those where both ends are in the entity set
      const entityIds = new Set(entities.map((e) => e.id));
      let relations = allRelations.filter(
        (r) =>
          entityIds.has(r.source_entity_id) && entityIds.has(r.target_entity_id)
      );

      // If too many nodes, keep top N by degree
      if (entities.length > MAX_NODES) {
        const degreeMap = new Map<string, number>();
        for (const r of relations) {
          degreeMap.set(
            r.source_entity_id,
            (degreeMap.get(r.source_entity_id) || 0) + 1
          );
          degreeMap.set(
            r.target_entity_id,
            (degreeMap.get(r.target_entity_id) || 0) + 1
          );
        }

        entities.sort(
          (a, b) => (degreeMap.get(b.id) || 0) - (degreeMap.get(a.id) || 0)
        );
        entities = entities.slice(0, MAX_NODES);

        const keptIds = new Set(entities.map((e) => e.id));
        relations = relations.filter(
          (r) =>
            keptIds.has(r.source_entity_id) && keptIds.has(r.target_entity_id)
        );
      }

      return { entities, relations };
    },
    staleTime: 60_000,
  });
}

export function useGraphStats() {
  return useQuery({
    queryKey: ["graph-stats"],
    queryFn: async (): Promise<GraphStats> => {
      return (await api.getGraphStats()) as GraphStats;
    },
    staleTime: 60_000,
  });
}

export function useEntityMemories(entityId: string | null) {
  return useQuery({
    queryKey: ["entity-memories", entityId],
    enabled: !!entityId,
    queryFn: async () => {
      return (await api.getEntityMemories(entityId!)) as {
        id: string;
        content: string;
        memory_type: string;
        importance: number;
        created_at: string;
      }[];
    },
  });
}
