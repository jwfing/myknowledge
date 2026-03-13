import { Brain, BookOpen, History, Workflow } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { DashboardStats as Stats } from "@/types/memory";

const statItems = [
  {
    key: "total" as const,
    label: "Total Memories",
    icon: Brain,
    color: "text-purple-400",
    bgColor: "bg-purple-400/10",
  },
  {
    key: "semantic" as const,
    label: "Semantic",
    icon: BookOpen,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10",
  },
  {
    key: "episodic" as const,
    label: "Episodic",
    icon: History,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10",
  },
  {
    key: "procedural" as const,
    label: "Procedural",
    icon: Workflow,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
  },
];

interface DashboardStatsProps {
  stats: Stats;
}

export default function DashboardStats({ stats }: DashboardStatsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <Card key={item.key} className="border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-lg ${item.bgColor} flex items-center justify-center shrink-0`}
              >
                <item.icon className={`w-5 h-5 ${item.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats[item.key]}</p>
                <p className="text-xs text-muted-foreground">{item.label}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
