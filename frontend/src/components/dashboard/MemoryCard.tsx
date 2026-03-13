import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Memory } from "@/types/memory";

const typeConfig: Record<string, { label: string; className: string }> = {
  semantic: {
    label: "Semantic",
    className: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  },
  episodic: {
    label: "Episodic",
    className: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  },
  procedural: {
    label: "Procedural",
    className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  },
};

const defaultTypeConfig = {
  label: "Unknown",
  className: "bg-gray-500/15 text-gray-400 border-gray-500/20",
};

function timeAgo(date: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(date).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

interface MemoryCardProps {
  memory: Memory;
}

export default function MemoryCard({ memory }: MemoryCardProps) {
  const config = typeConfig[memory.memory_type] || defaultTypeConfig;
  const project = memory.project;
  const projectName = Array.isArray(project) ? project[0]?.name : project?.name;

  return (
    <div className="group rounded-xl border border-border/50 bg-card/50 p-5 transition-all hover:border-border hover:bg-card/80">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className={cn("text-xs", config.className)}>
            {config.label}
          </Badge>
          {projectName && (
            <Badge variant="secondary" className="text-xs">
              {projectName}
            </Badge>
          )}
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {timeAgo(memory.created_at)}
        </span>
      </div>

      {/* Content */}
      <p className="text-sm leading-relaxed mb-3">{memory.content}</p>

      {/* Footer */}
      <div className="flex items-center justify-between gap-3">
        {/* Tags */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {memory.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded-md bg-secondary/60 px-2 py-0.5 text-[10px] text-muted-foreground"
            >
              {tag}
            </span>
          ))}
          {memory.tags.length > 4 && (
            <span className="text-[10px] text-muted-foreground">
              +{memory.tags.length - 4}
            </span>
          )}
        </div>

        {/* Importance indicator */}
        <div className="flex items-center gap-1 shrink-0">
          <div className="flex gap-0.5">
            {[1, 2, 3, 4, 5].map((level) => (
              <div
                key={level}
                className={cn(
                  "w-1.5 h-3 rounded-sm",
                  level <= Math.round(memory.importance * 5)
                    ? "bg-primary"
                    : "bg-secondary"
                )}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
