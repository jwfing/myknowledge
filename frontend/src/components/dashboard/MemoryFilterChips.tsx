import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { MemoryFilters, Project } from "@/types/memory";

const memoryTypes = [
  { value: "all", label: "All Types" },
  { value: "semantic", label: "Semantic", color: "bg-blue-400" },
  { value: "episodic", label: "Episodic", color: "bg-amber-400" },
  { value: "procedural", label: "Procedural", color: "bg-emerald-400" },
];

interface MemoryFilterChipsProps {
  filters: MemoryFilters;
  onChange: (filters: MemoryFilters) => void;
  projects: Project[];
}

export default function MemoryFilterChips({
  filters,
  onChange,
  projects,
}: MemoryFilterChipsProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Type filter chips */}
      <div className="flex items-center gap-1.5">
        {memoryTypes.map((type) => {
          const isActive =
            type.value === "all"
              ? !filters.memoryType
              : filters.memoryType === type.value;
          return (
            <button
              key={type.value}
              onClick={() =>
                onChange({
                  ...filters,
                  memoryType: type.value === "all" ? null : type.value,
                })
              }
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              )}
            >
              {type.color && (
                <span
                  className={cn("w-1.5 h-1.5 rounded-full", type.color)}
                />
              )}
              {type.label}
            </button>
          );
        })}
      </div>

      {/* Project filter */}
      {projects.length > 0 && (
        <Select
          value={filters.projectId || "all"}
          onValueChange={(v) =>
            onChange({
              ...filters,
              projectId: v === "all" ? null : v,
            })
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
    </div>
  );
}
