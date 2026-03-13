import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CTASection() {
  const navigate = useNavigate();

  return (
    <section className="py-24 sm:py-32 border-t border-border/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl border border-violet-500/15 bg-gradient-to-b from-violet-500/[0.06] to-transparent overflow-hidden">
          {/* Glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-violet-500/10 rounded-full blur-[80px]" />

          <div className="relative px-8 py-16 sm:px-16 sm:py-20 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Start building with
              <br />
              <span className="text-gradient">persistent knowledge</span>
            </h2>
            <p className="text-base text-muted-foreground max-w-md mx-auto mb-8">
              Free for personal use. Set up in under 2 minutes.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
              <Button
                size="lg"
                onClick={() => navigate("/dashboard")}
                className="bg-gradient-to-r from-violet-500 to-cyan-500 text-white border-0 hover:opacity-90 h-12 px-8 rounded-xl text-[15px] font-semibold shadow-lg shadow-violet-500/20"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>

            <div className="inline-block rounded-xl border border-border/50 bg-card/50 px-6 py-3 mono text-sm text-muted-foreground">
              <span className="text-cyan-400">$</span>{" "}
              <span className="text-foreground">npx rememberit init</span>
            </div>

            <p className="mt-4 text-xs text-muted-foreground/50">
              Works with Claude Code, Cursor, and any MCP client
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
