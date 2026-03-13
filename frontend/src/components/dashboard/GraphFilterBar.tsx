import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ENTITY_TYPE_COLORS, ENTITY_TYPES } from "@/types/graph";
import type { GraphFilters } from "@/types/graph";
import type { Project } from "@/types/memory";

interface GraphFilterBarProps {
  filters: GraphFilters;
  onChange: (filters: GraphFilters) => void;
  projects: Project[];
}

export default function GraphFilterBar({
  filters,
  onChange,
  projects,
}: GraphFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Entity type chips */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={() =>
            onChange({ ...filters, entityType: null })
          }
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
            !filters.entityType
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          All
        </button>
        {ENTITY_TYPES.map((type) => (
          <button
            key={type}
            onClick={() =>
              onChange({
                ...filters,
                entityType: filters.entityType === type ? null : type,
              })
            }
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              filters.entityType === type
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: ENTITY_TYPE_COLORS[type] }}
            />
            {type}
          </button>
        ))}
      </div>

      {/* Project filter */}
      {projects.length > 0 && (
        <Select
          value={filters.projectId || "all"}
          onValueChange={(v) =>
            onChange({ ...filters, projectId: v === "all" ? null : v })
          }
        >
          <SelectTrigger className="w-[180px] h-8 text-xs bg-card/50">
            <SelectValue placeholder="All Projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Search */}
      <div className="relative ml-auto">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          placeholder="Search entities..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="pl-8 h-8 w-48 text-xs bg-card/50"
        />
      </div>
    </div>
  );
}
