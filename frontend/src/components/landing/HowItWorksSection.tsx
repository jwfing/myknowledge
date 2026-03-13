import { Radio, Sparkles, Layers, Crosshair } from "lucide-react";
import { useStaggerReveal } from "@/hooks/useScrollReveal";

const steps = [
  {
    icon: Radio,
    num: "01",
    title: "Capture",
    description:
      "Claude Hooks automatically collect conversations. MCP tools let agents actively save important context.",
    color: "text-teal-600",
    borderColor: "border-teal-500/25",
    numBg: "bg-teal-500/8",
  },
  {
    icon: Sparkles,
    num: "02",
    title: "Extract",
    description:
      "Backend pipeline identifies entities, relationships, decisions, and patterns from raw conversation data.",
    color: "text-cyan-700",
    borderColor: "border-cyan-600/25",
    numBg: "bg-cyan-600/8",
  },
  {
    icon: Layers,
    num: "03",
    title: "Structure",
    description:
      "Knowledge is organized into graph nodes and memory categories — semantic, episodic, and procedural.",
    color: "text-emerald-600",
    borderColor: "border-emerald-500/25",
    numBg: "bg-emerald-500/8",
  },
  {
    icon: Crosshair,
    num: "04",
    title: "Recall",
    description:
      "Hybrid retrieval combines vector similarity, graph traversal, and memory decay for precise results.",
    color: "text-amber-600",
    borderColor: "border-amber-500/25",
    numBg: "bg-amber-500/8",
  },
];

export default function HowItWorksSection() {
  const { ref, isVisible, getStaggerStyle } = useStaggerReveal<HTMLDivElement>({
    threshold: 0.1,
    stagger: 120,
  });

  return (
    <section id="how-it-works" className="py-24 sm:py-32 border-t border-border/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-teal-600 uppercase tracking-wider mb-4">
            <div className="w-5 h-px bg-teal-400/40" />
            How It Works
            <div className="w-5 h-px bg-teal-400/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            From raw conversations to{" "}
            <span className="text-gradient">structured knowledge</span>
          </h2>
          <p className="text-base text-muted-foreground max-w-lg mx-auto">
            A four-stage pipeline that turns your agent interactions into a
            searchable, connected knowledge base.
          </p>
        </div>

        {/* Pipeline */}
        <div className="relative" ref={ref}>
          {/* Animated flowing connector line */}
          <div className="hidden lg:block absolute top-[28px] left-[12%] right-[12%] h-[2px] overflow-hidden rounded-full">
            <div
              className={`w-full h-full transition-all duration-1000 ${isVisible ? "flow-line" : "bg-border/20"}`}
              style={{ opacity: isVisible ? 1 : 0 }}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, i) => (
              <div
                key={step.title}
                className="text-center relative z-10"
                style={getStaggerStyle(i)}
              >
                <div
                  className={`w-[56px] h-[56px] rounded-2xl ${step.numBg} border ${step.borderColor} flex items-center justify-center mx-auto mb-5 icon-bounce transition-shadow duration-300 hover:shadow-lg hover:shadow-teal-500/10`}
                >
                  <step.icon className={`w-5 h-5 ${step.color}`} />
                </div>
                <div className={`text-xs font-bold uppercase tracking-widest ${step.color} opacity-50 mb-2`}>
                  Step {step.num}
                </div>
                <h4 className="text-base font-semibold mb-2">{step.title}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed px-2">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Scoring formula */}
        <div className="mt-16 text-center">
          <div className="inline-block rounded-2xl border border-border/50 bg-card/40 px-8 py-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3 font-medium">
              Retrieval Scoring
            </p>
            <p className="mono text-sm sm:text-base">
              <span className="text-teal-600">score</span>
              <span className="text-muted-foreground"> = </span>
              <span className="text-cyan-700">&alpha; &middot; similarity</span>
              <span className="text-muted-foreground"> + </span>
              <span className="text-amber-600">&beta; &middot; importance</span>
              <span className="text-muted-foreground"> + </span>
              <span className="text-emerald-600">&gamma; &middot; recency</span>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
