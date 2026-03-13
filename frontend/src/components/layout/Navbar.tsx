import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-border/40 bg-background/70 backdrop-blur-2xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <svg width="26" height="26" viewBox="0 0 32 32" fill="none" className="transition-transform group-hover:scale-105">
            <circle cx="16" cy="16" r="13" stroke="url(#nav-g)" strokeWidth="2" />
            <circle cx="16" cy="11" r="2.5" fill="#0d9488" />
            <circle cx="10.5" cy="19.5" r="2" fill="#0891b2" />
            <circle cx="21.5" cy="19.5" r="2" fill="#059669" />
            <line x1="16" y1="13.5" x2="10.5" y2="17.5" stroke="#0d9488" strokeOpacity="0.2" strokeWidth="1" />
            <line x1="16" y1="13.5" x2="21.5" y2="17.5" stroke="#0d9488" strokeOpacity="0.2" strokeWidth="1" />
            <line x1="10.5" y1="19.5" x2="21.5" y2="19.5" stroke="#0d9488" strokeOpacity="0.15" strokeWidth="1" />
            <defs>
              <linearGradient id="nav-g" x1="0" y1="0" x2="32" y2="32">
                <stop stopColor="#0d9488" />
                <stop offset="1" stopColor="#0891b2" />
              </linearGradient>
            </defs>
          </svg>
          <span className="text-lg font-bold tracking-tight">RememberIt</span>
        </Link>

        <div className="hidden sm:flex items-center gap-6">
          <button onClick={() => scrollTo("features")} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Features
          </button>
          <button onClick={() => scrollTo("how-it-works")} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            How It Works
          </button>
          <button onClick={() => scrollTo("architecture")} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Architecture
          </button>
          <button onClick={() => scrollTo("memory")} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Memory
          </button>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/dashboard">
            <Button variant="ghost" size="sm">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
