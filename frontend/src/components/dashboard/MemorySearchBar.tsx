import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";

interface MemorySearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export default function MemorySearchBar({
  value,
  onChange,
}: MemorySearchBarProps) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(local);
    }, 300);
    return () => clearTimeout(timer);
  }, [local, onChange]);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
      <Input
        placeholder="Search memories..."
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        className="pl-9 bg-card/50"
      />
    </div>
  );
}
