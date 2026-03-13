import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import KnowledgeGraph from "./KnowledgeGraph";

function AnimatedCodeBlock() {
  const lines = [
    { type: "comment", text: "// Your agent remembers automatically" },
    { type: "code", parts: [
      { text: "remember_it", cls: "text-teal-600" },
      { text: "({", cls: "text-muted-foreground" },
    ]},
    { type: "code", parts: [
      { text: "  content", cls: "text-teal-700/70" },
      { text: ": ", cls: "text-muted-foreground" },
      { text: '"OAuth PKCE needs code_verifier', cls: "text-emerald-700" },
    ]},
    { type: "code", parts: [
      { text: '    in session storage"', cls: "text-emerald-700" },
      { text: ",", cls: "text-muted-foreground" },
    ]},
    { type: "code", parts: [
      { text: "  memory_type", cls: "text-teal-700/70" },
      { text: ": ", cls: "text-muted-foreground" },
      { text: '"semantic"', cls: "text-amber-600" },
      { text: ",", cls: "text-muted-foreground" },
    ]},
    { type: "code", parts: [
      { text: "  tags", cls: "text-teal-700/70" },
      { text: ": [", cls: "text-muted-foreground" },
      { text: '"oauth"', cls: "text-emerald-700" },
      { text: ", ", cls: "text-muted-foreground" },
      { text: '"auth"', cls: "text-emerald-700" },
      { text: "]", cls: "text-muted-foreground" },
    ]},
    { type: "code", parts: [{ text: "})", cls: "text-muted-foreground" }] },
    { type: "empty", parts: [] },
    { type: "comment", text: "// And recalls across every project" },
    { type: "code", parts: [
      { text: "recall_memory", cls: "text-teal-600" },
      { text: "({", cls: "text-muted-foreground" },
    ]},
    { type: "code", parts: [
      { text: "  query", cls: "text-teal-700/70" },
      { text: ": ", cls: "text-muted-foreground" },
      { text: '"auth implementation patterns"', cls: "text-emerald-700" },
    ]},
    { type: "code", parts: [{ text: "})", cls: "text-muted-foreground" }] },
    { type: "comment", text: "// → 3 memories found, ranked by relevance" },
  ];

  const [visibleLines, setVisibleLines] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setVisibleLines((prev) => {
        if (prev >= lines.length) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative z-10">
      <div className="rounded-2xl border border-border/60 bg-card/80 backdrop-blur-md overflow-hidden shadow-2xl shadow-teal-500/5">
        <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-border/40">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
          <span className="ml-auto text-[11px] mono text-muted-foreground/50">MCP Tool Call</span>
        </div>
        <div className="p-5 mono text-[12.5px] leading-[1.85] whitespace-pre">
          {lines.slice(0, visibleLines).map((line, i) => (
            <div
              key={i}
              className="transition-all duration-300"
              style={{
                opacity: i < visibleLines ? 1 : 0,
                transform: i < visibleLines ? "translateX(0)" : "translateX(-8px)",
              }}
            >
              {line.type === "comment" ? (
                <span className="text-muted-foreground/40">{line.text}</span>
              ) : line.type === "empty" ? (
                <br />
              ) : (
                line.parts?.map((part, j) => (
                  <span key={j} className={part.cls}>{part.text}</span>
                ))
              )}
            </div>
          ))}
          <span className="inline-block w-[7px] h-[17px] bg-teal-500/50 animate-pulse ml-0.5 -mb-0.5" />
        </div>
      </div>
    </div>
  );
}

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative min-h-[80vh] flex items-center overflow-hidden">
      {/* Interactive knowledge graph background */}
      <div className="absolute inset-0">
        <KnowledgeGraph />
      </div>

      {/* Gradient overlays to ensure text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/60 to-background pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-hero pointer-events-none" />

      <div className="relative w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-14 items-center">
          {/* Left: Text content */}
          <div className="text-center lg:text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-teal-500/20 bg-teal-500/[0.06] backdrop-blur-sm text-sm mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-muted-foreground text-[13px]">
                Works with Claude Code, Cursor & any MCP client
              </span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[3.75rem] font-extrabold tracking-tight leading-[1.06] mb-6">
              Your Agent
              <br />
              <span className="text-gradient">Never Forgets</span>
            </h1>

            <p className="text-base sm:text-lg text-muted-foreground max-w-md mx-auto lg:mx-0 mb-10 leading-relaxed">
              Cross-project, cross-agent knowledge that grows with you.
              Install once, remember everything.
            </p>

            <div className="flex flex-col sm:flex-row items-center lg:items-start justify-center lg:justify-start gap-3">
              <Button
                size="lg"
                onClick={() => navigate("/dashboard")}
                className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white border-0 hover:opacity-90 h-12 px-8 rounded-xl text-[15px] font-semibold shadow-lg shadow-teal-500/15"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="h-12 px-8 rounded-xl text-[15px] font-semibold border-border/60 hover:bg-secondary/50 backdrop-blur-sm"
                onClick={() => window.open("https://github.com/jwfing/rememberit", "_blank")}
              >
                <Github className="w-4 h-4" />
                View on GitHub
              </Button>
            </div>
          </div>

          {/* Right: Code block */}
          <AnimatedCodeBlock />
        </div>
      </div>
    </section>
  );
}
