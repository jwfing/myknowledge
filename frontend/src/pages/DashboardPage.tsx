import { useState } from "react";
import { Brain, GitBranch, Link2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import MemorySearchBar from "@/components/dashboard/MemorySearchBar";
import MemoryFilterChips from "@/components/dashboard/MemoryFilterChips";
import MemoryList from "@/components/dashboard/MemoryList";
import GraphFilterBar from "@/components/dashboard/GraphFilterBar";
import KnowledgeGraphView from "@/components/dashboard/KnowledgeGraphView";
import { useMemories, useMemoryStats } from "@/hooks/useMemories";
import { useGraphData, useGraphStats } from "@/hooks/useKnowledgeGraph";
import type { MemoryFilters } from "@/types/memory";
import type { GraphFilters } from "@/types/graph";

export default function DashboardPage() {
  const [filters, setFilters] = useState<MemoryFilters>({
    search: "",
    memoryType: null,
    projectId: null,
  });
  const [graphFilters, setGraphFilters] = useState<GraphFilters>({
    projectId: null,
    entityType: null,
    search: "",
  });

  const { data: memories, isLoading } = useMemories(filters);
  const { data: stats } = useMemoryStats();
  const { data: graphData } = useGraphData(graphFilters);
  const { data: graphStats } = useGraphStats();

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Memory Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Here are your stored memories.
        </p>
      </div>

      {/* Unified overview stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        {stats && (
          <>
            <OverviewCard icon={Brain} label="Memories" value={stats.total} color="purple" />
            <OverviewCard label="Semantic" value={stats.semantic} color="blue" />
            <OverviewCard label="Episodic" value={stats.episodic} color="amber" />
            <OverviewCard label="Procedural" value={stats.procedural} color="emerald" />
          </>
        )}
        {graphStats && (
          <>
            <OverviewCard icon={GitBranch} label="Entities" value={graphStats.totalEntities} color="teal" />
            <OverviewCard icon={Link2} label="Relations" value={graphStats.totalRelations} color="cyan" />
          </>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="memories">
        <TabsList className="mb-4">
          <TabsTrigger value="memories">
            Memories
            {stats ? ` (${stats.total})` : ""}
          </TabsTrigger>
          <TabsTrigger value="graph">
            Knowledge Graph
            {graphStats ? ` (${graphStats.totalEntities})` : ""}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="memories">
          <div className="space-y-4">
            <MemorySearchBar
              value={filters.search}
              onChange={(search) => setFilters((prev) => ({ ...prev, search }))}
            />
            <MemoryFilterChips
              filters={filters}
              onChange={setFilters}
              projects={stats?.projects || []}
            />
          </div>
          <div className="mt-4">
            <MemoryList memories={memories || []} isLoading={isLoading} />
          </div>
        </TabsContent>

        <TabsContent value="graph">
          <div className="mb-4">
            <GraphFilterBar
              filters={graphFilters}
              onChange={setGraphFilters}
              projects={stats?.projects || []}
            />
          </div>
          <KnowledgeGraphView
            entities={graphData?.entities || []}
            relations={graphData?.relations || []}
          />
        </TabsContent>
      </Tabs>
    </main>
  );
}

const COLOR_MAP: Record<string, { bg: string; text: string }> = {
  purple: { bg: "bg-purple-400/10", text: "text-purple-400" },
  blue: { bg: "bg-blue-400/10", text: "text-blue-400" },
  amber: { bg: "bg-amber-400/10", text: "text-amber-400" },
  emerald: { bg: "bg-emerald-400/10", text: "text-emerald-400" },
  teal: { bg: "bg-teal-400/10", text: "text-teal-400" },
  cyan: { bg: "bg-cyan-400/10", text: "text-cyan-400" },
};

function OverviewCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  color: string;
}) {
  const c = COLOR_MAP[color] || COLOR_MAP.purple;
  return (
    <Card className="border-border/50">
      <CardContent className="p-3">
        <div className="flex items-center gap-2.5">
          {Icon && (
            <div className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center shrink-0`}>
              <Icon className={`w-4 h-4 ${c.text}`} />
            </div>
          )}
          <div>
            <p className="text-xl font-bold leading-none">{value}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
