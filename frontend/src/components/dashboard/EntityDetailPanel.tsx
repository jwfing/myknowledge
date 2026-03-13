import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { ENTITY_TYPE_COLORS } from "@/types/graph";
import { useEntityMemories } from "@/hooks/useKnowledgeGraph";
import type { GraphEntity, GraphRelation } from "@/types/graph";

interface EntityDetailPanelProps {
  entity: GraphEntity | null;
  relations: GraphRelation[];
  entities: GraphEntity[];
  onClose: () => void;
}

export default function EntityDetailPanel({
  entity,
  relations,
  entities,
  onClose,
}: EntityDetailPanelProps) {
  const { data: memories, isLoading: memoriesLoading } = useEntityMemories(
    entity?.id ?? null
  );

  if (!entity) return null;

  const entityMap = new Map(entities.map((e) => [e.id, e]));

  const outgoing = relations.filter(
    (r) => r.source_entity_id === entity.id
  );
  const incoming = relations.filter(
    (r) => r.target_entity_id === entity.id
  );

  const projectName = entity.project
    ? Array.isArray(entity.project)
      ? entity.project[0]?.name
      : entity.project.name
    : null;

  return (
    <div className="absolute top-0 right-0 h-full w-80 border-l border-border/50 bg-card/95 backdrop-blur-xl z-20 flex flex-col shadow-2xl">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-border/40">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-sm truncate">{entity.name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <Badge
              variant="outline"
              className="text-[10px] px-1.5 py-0"
              style={{
                borderColor: ENTITY_TYPE_COLORS[entity.entity_type] || "#6b7280",
                color: ENTITY_TYPE_COLORS[entity.entity_type] || "#6b7280",
              }}
            >
              {entity.entity_type}
            </Badge>
            {projectName && (
              <span className="text-[10px] text-muted-foreground">
                {projectName}
              </span>
            )}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-7 w-7 p-0 shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-5">
          {/* Description */}
          {entity.description && (
            <div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {entity.description}
              </p>
            </div>
          )}

          {/* Outgoing Relations */}
          {outgoing.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Outgoing ({outgoing.length})
              </p>
              <div className="space-y-1.5">
                {outgoing.map((r) => {
                  const target = entityMap.get(r.target_entity_id);
                  return (
                    <div
                      key={r.id}
                      className="flex items-center gap-2 text-xs"
                    >
                      <span className="text-teal-500 shrink-0">
                        {r.relation_type}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="truncate">
                        {target?.name || "Unknown"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Incoming Relations */}
          {incoming.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Incoming ({incoming.length})
              </p>
              <div className="space-y-1.5">
                {incoming.map((r) => {
                  const source = entityMap.get(r.source_entity_id);
                  return (
                    <div
                      key={r.id}
                      className="flex items-center gap-2 text-xs"
                    >
                      <span className="truncate">
                        {source?.name || "Unknown"}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="text-teal-500 shrink-0">
                        {r.relation_type}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <Separator className="opacity-40" />

          {/* Linked Memories */}
          <div>
            <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Linked Memories
            </p>
            {memoriesLoading ? (
              <p className="text-xs text-muted-foreground">Loading...</p>
            ) : memories && memories.length > 0 ? (
              <div className="space-y-2">
                {memories.map((m) => (
                  <div
                    key={m.id}
                    className="rounded-lg border border-border/40 bg-background/50 p-2.5"
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <Badge
                        variant="secondary"
                        className="text-[9px] px-1.5 py-0"
                      >
                        {m.memory_type}
                      </Badge>
                      <span className="text-[9px] text-muted-foreground">
                        {new Date(m.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3">
                      {m.content}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                No linked memories
              </p>
            )}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
