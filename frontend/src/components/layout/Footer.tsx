export default function Footer() {
  return (
    <footer className="border-t border-border/30 bg-background/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="13" stroke="url(#ft-g)" strokeWidth="2" />
              <circle cx="16" cy="11" r="2.5" fill="#0d9488" />
              <circle cx="10.5" cy="19.5" r="2" fill="#0891b2" />
              <circle cx="21.5" cy="19.5" r="2" fill="#059669" />
              <defs>
                <linearGradient id="ft-g" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#0d9488" />
                  <stop offset="1" stopColor="#0891b2" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-sm font-semibold">RememberIt</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="https://github.com/jwfing/rememberit" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              GitHub
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Docs
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Discord
            </a>
          </div>
          <p className="text-xs text-muted-foreground/60">
            Built for developers who build with AI.
          </p>
        </div>
      </div>
    </footer>
  );
}
