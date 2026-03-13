import { useStaggerReveal } from "@/hooks/useScrollReveal";

const memories = [
  {
    tag: "Semantic",
    tagColor: "bg-teal-500/10 text-teal-600",
    title: "Facts & Concepts",
    description:
      "Stores general knowledge, definitions, and factual information extracted from your projects.",
    example: "The auth service uses JWT with RS256 signing.\nRate limits are set to 100 req/min per user.",
  },
  {
    tag: "Episodic",
    tagColor: "bg-cyan-600/10 text-cyan-700",
    title: "Events & Experiences",
    description:
      "Captures specific interactions, debugging sessions, and decision-making moments with full context.",
    example: "On Feb 12, we debugged a race condition\nin the payment queue — fixed with mutex lock.",
  },
  {
    tag: "Procedural",
    tagColor: "bg-emerald-500/10 text-emerald-600",
    title: "Patterns & Workflows",
    description:
      "Learns recurring patterns, coding conventions, deployment steps, and team-specific workflows.",
    example: "Deploy: run tests → build docker →\npush to ECR → update ECS task definition.",
  },
  {
    tag: "Working",
    tagColor: "bg-amber-500/10 text-amber-600",
    title: "Active Context",
    description:
      "Maintains the current session's focus and recent context for immediate, high-priority retrieval.",
    example: "Currently refactoring notification service.\nKey files: notify.ts, queue.ts, templates/",
  },
];

export default function MemoryModelSection() {
  const { ref, getStaggerStyle } = useStaggerReveal<HTMLDivElement>({
    threshold: 0.1,
    stagger: 100,
  });

  return (
    <section id="memory" className="py-24 sm:py-32 border-t border-border/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-teal-600 uppercase tracking-wider mb-4">
            <div className="w-5 h-px bg-teal-400/40" />
            Memory Model
            <div className="w-5 h-px bg-teal-400/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Inspired by{" "}
            <span className="text-gradient">how humans remember</span>
          </h2>
          <p className="text-base text-muted-foreground max-w-lg mx-auto">
            Four memory types work together to provide the right knowledge at the
            right time.
          </p>
        </div>

        <div ref={ref} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {memories.map((mem, i) => (
            <div
              key={mem.tag}
              style={getStaggerStyle(i)}
              className="group rounded-2xl border border-border/50 bg-card/40 p-7 transition-all duration-300 hover:border-border/70 shimmer-hover"
            >
              <span
                className={`inline-block text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-md ${mem.tagColor} mb-4`}
              >
                {mem.tag}
              </span>
              <h3 className="text-lg font-semibold mb-2">{mem.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                {mem.description}
              </p>
              <div className="rounded-xl bg-background/80 border border-border/30 px-4 py-3 mono text-xs text-muted-foreground/70 leading-relaxed whitespace-pre-line transition-colors duration-300 group-hover:border-border/50">
                {mem.example}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
