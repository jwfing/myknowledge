import { GitBranch, Link2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { ENTITY_TYPE_COLORS } from "@/types/graph";
import type { GraphStats as Stats } from "@/types/graph";

interface GraphStatsProps {
  stats: Stats;
}

export default function GraphStats({ stats }: GraphStatsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-teal-400/10 flex items-center justify-center shrink-0">
              <GitBranch className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.totalEntities}</p>
              <p className="text-xs text-muted-foreground">Entities</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-400/10 flex items-center justify-center shrink-0">
              <Link2 className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.totalRelations}</p>
              <p className="text-xs text-muted-foreground">Relations</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-2 border-border/50">
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground mb-2.5">Entity Types</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.entityTypeCounts)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <span
                  key={type}
                  className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium bg-secondary/60"
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor:
                        ENTITY_TYPE_COLORS[type] || "#6b7280",
                    }}
                  />
                  {type}
                  <span className="text-muted-foreground">{count}</span>
                </span>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
