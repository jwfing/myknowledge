import { Zap, Plug, Globe, Webhook, Brain, Link, BarChart3, Tag, Network, Ruler, HardDrive, FileText, Search, Map, Clock, Target } from "lucide-react";
import { useStaggerReveal } from "@/hooks/useScrollReveal";

const layers = [
  {
    label: "Ingestion",
    color: "text-cyan-700",
    borderColor: "border-cyan-600/30",
    modules: [
      { icon: Zap, name: "Claude Hooks" },
      { icon: Plug, name: "MCP Server" },
      { icon: Globe, name: "REST API" },
      { icon: Webhook, name: "Webhooks" },
    ],
  },
  {
    label: "Processing",
    color: "text-teal-600",
    borderColor: "border-teal-500/30",
    modules: [
      { icon: Brain, name: "Entity Extraction" },
      { icon: Link, name: "Relation Mapping" },
      { icon: BarChart3, name: "Embedding Pipeline" },
      { icon: Tag, name: "Auto Classification" },
    ],
  },
  {
    label: "Storage",
    color: "text-emerald-600",
    borderColor: "border-emerald-500/30",
    modules: [
      { icon: Network, name: "Knowledge Graph" },
      { icon: Ruler, name: "Vector Store" },
      { icon: HardDrive, name: "Memory Index" },
      { icon: FileText, name: "Document Store" },
    ],
  },
  {
    label: "Retrieval",
    color: "text-amber-600",
    borderColor: "border-amber-500/30",
    modules: [
      { icon: Search, name: "Hybrid Search" },
      { icon: Map, name: "Graph Traversal" },
      { icon: Clock, name: "Memory Decay" },
      { icon: Target, name: "Context Ranking" },
    ],
  },
];

export default function ArchitectureSection() {
  const { ref, getStaggerStyle } = useStaggerReveal<HTMLDivElement>({
    threshold: 0.08,
    stagger: 150,
  });

  return (
    <section id="architecture" className="py-24 sm:py-32 border-t border-border/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-teal-600 uppercase tracking-wider mb-4">
            <div className="w-5 h-px bg-teal-400/40" />
            Architecture
            <div className="w-5 h-px bg-teal-400/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Designed for{" "}
            <span className="text-gradient">composability</span>
          </h2>
          <p className="text-base text-muted-foreground max-w-lg mx-auto">
            A layered architecture that integrates cleanly with your existing
            agent stack.
          </p>
        </div>

        <div className="rounded-2xl border border-border/50 bg-card/30 p-6 sm:p-10 relative overflow-hidden shimmer-hover">
          <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-teal-500/[0.03] rounded-full blur-[80px]" />

          <div className="space-y-6 relative" ref={ref}>
            {layers.map((layer, i) => (
              <div
                key={layer.label}
                className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-4 items-start"
                style={getStaggerStyle(i)}
              >
                <div
                  className={`text-xs font-semibold uppercase tracking-wider ${layer.color} sm:text-right sm:pr-5 sm:border-r-2 ${layer.borderColor} sm:py-3`}
                >
                  {layer.label}
                </div>
                <div className="flex flex-wrap gap-3">
                  {layer.modules.map((mod) => (
                    <div
                      key={mod.name}
                      className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-secondary/40 border border-border/40 text-sm font-medium transition-all duration-200 hover:border-border/70 hover:bg-secondary/60 hover:-translate-y-0.5"
                    >
                      <mod.icon className={`w-4 h-4 ${layer.color} opacity-70`} />
                      {mod.name}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
