import { Brain } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import MemoryCard from "./MemoryCard";
import type { Memory } from "@/types/memory";

interface MemoryListProps {
  memories: Memory[];
  isLoading: boolean;
}

export default function MemoryList({ memories, isLoading }: MemoryListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-border/50 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
          <Brain className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No memories found</h3>
        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
          Your memories will appear here once your agents start saving knowledge
          via the MCP remember_this tool.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {memories.map((memory) => (
        <MemoryCard key={memory.id} memory={memory} />
      ))}
    </div>
  );
}
