export interface GraphEntity {
  id: string;
  name: string;
  entity_type: string;
  project_id: string | null;
  description: string | null;
  // PostgREST FK join returns array
  project?: { name: string }[] | { name: string } | null;
}

export interface GraphRelation {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relation_type: string;
  description: string | null;
}

export interface GraphFilters {
  projectId: string | null;
  entityType: string | null;
  search: string;
}

export interface GraphData {
  entities: GraphEntity[];
  relations: GraphRelation[];
}

export interface GraphStats {
  totalEntities: number;
  totalRelations: number;
  entityTypeCounts: Record<string, number>;
}

// D3 simulation node extends GraphEntity
export interface SimNode extends GraphEntity {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx: number | null;
  fy: number | null;
  degree: number;
}

export interface SimLink {
  source: SimNode | string;
  target: SimNode | string;
  relation_type: string;
  id: string;
}

export const ENTITY_TYPE_COLORS: Record<string, string> = {
  Component: "#0d9488",   // teal-600
  TechStack: "#0891b2",   // cyan-600
  Config: "#d97706",      // amber-600
  API: "#e11d48",         // rose-600
  Project: "#7c3aed",     // violet-600
  Infrastructure: "#059669", // emerald-600
};

export const ENTITY_TYPES = [
  "Component",
  "TechStack",
  "Config",
  "API",
  "Project",
  "Infrastructure",
] as const;
