import {
  Search,
  GitBranch,
  Plug,
  Brain,
  Filter,
  BarChart3,
} from "lucide-react";
import { useStaggerReveal } from "@/hooks/useScrollReveal";

const features = [
  {
    icon: GitBranch,
    title: "Knowledge Graph",
    description:
      "Automatically builds entity-relation graphs from agent interactions. Discover hidden connections across projects.",
    color: "text-teal-600",
    bgColor: "bg-teal-500/8",
    borderColor: "group-hover:border-teal-500/20",
  },
  {
    icon: Search,
    title: "Vector Search",
    description:
      "Semantic retrieval across your entire knowledge base. Find relevant context even when exact keywords don't match.",
    color: "text-cyan-700",
    bgColor: "bg-cyan-600/8",
    borderColor: "group-hover:border-cyan-600/20",
  },
  {
    icon: Brain,
    title: "Human-like Memory",
    description:
      "Episodic, semantic, and procedural memory layers that mirror how humans organize knowledge.",
    color: "text-emerald-600",
    bgColor: "bg-emerald-500/8",
    borderColor: "group-hover:border-emerald-500/20",
  },
  {
    icon: Filter,
    title: "Auto Ingestion",
    description:
      "Passively captures knowledge via Claude Hooks. No manual tagging — the pipeline extracts entities, decisions, and patterns.",
    color: "text-amber-600",
    bgColor: "bg-amber-500/8",
    borderColor: "group-hover:border-amber-500/20",
  },
  {
    icon: BarChart3,
    title: "Cross-Project Sharing",
    description:
      "Knowledge learned in one project is available everywhere. Your coding agent's insights help your writing agent.",
    color: "text-rose-500",
    bgColor: "bg-rose-500/8",
    borderColor: "group-hover:border-rose-500/20",
  },
  {
    icon: Plug,
    title: "MCP Native",
    description:
      "Install once, use everywhere. Works out of the box with Claude Code, Cursor, and any MCP-compatible client.",
    color: "text-sky-600",
    bgColor: "bg-sky-500/8",
    borderColor: "group-hover:border-sky-500/20",
  },
];

export default function FeaturesSection() {
  const { ref, getStaggerStyle } = useStaggerReveal<HTMLDivElement>({
    threshold: 0.1,
    stagger: 80,
  });

  return (
    <section id="features" className="py-24 sm:py-32 relative">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-teal-600 uppercase tracking-wider mb-4">
            <div className="w-5 h-px bg-teal-400/40" />
            Core Features
            <div className="w-5 h-px bg-teal-400/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Not just memory.{" "}
            <span className="text-gradient">Knowledge infrastructure.</span>
          </h2>
          <p className="text-base text-muted-foreground max-w-lg mx-auto">
            Go beyond simple key-value storage. RememberIt understands,
            connects, and evolves your knowledge automatically.
          </p>
        </div>

        <div ref={ref} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              style={getStaggerStyle(i)}
              className={`group relative rounded-2xl border border-border/50 bg-card/40 p-7 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-xl hover:shadow-teal-500/[0.04] shimmer-hover ${feature.borderColor}`}
            >
              <div className="absolute top-0 left-6 right-6 h-px bg-gradient-to-r from-transparent via-teal-500/0 to-transparent group-hover:via-teal-500/20 transition-all duration-500" />
              <div
                className={`w-10 h-10 rounded-xl ${feature.bgColor} flex items-center justify-center mb-5 icon-bounce`}
              >
                <feature.icon className={`w-5 h-5 ${feature.color}`} />
              </div>
              <h3 className="text-base font-semibold mb-2.5">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
