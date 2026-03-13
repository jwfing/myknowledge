export interface Memory {
  id: string;
  content: string;
  memory_type: string;
  importance: number;
  project_id: string | null;
  tags: string[];
  source_session_id: string | null;
  created_at: string;
  updated_at: string;
  // Joined from projects table (PostgREST returns array for FK joins)
  project?: { name: string }[] | { name: string } | null;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  tech_stack: string[];
  created_at: string;
}

export interface MemoryFilters {
  search: string;
  memoryType: string | null;
  projectId: string | null;
}

export interface DashboardStats {
  total: number;
  semantic: number;
  episodic: number;
  procedural: number;
  projects: Project[];
}
