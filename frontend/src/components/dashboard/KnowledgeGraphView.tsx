import { useRef, useEffect, useState, useCallback } from "react";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import { select } from "d3-selection";
import { drag as d3Drag } from "d3-drag";
import { zoom as d3Zoom, zoomIdentity } from "d3-zoom";
import { ENTITY_TYPE_COLORS } from "@/types/graph";
import type { GraphEntity, GraphRelation, SimNode, SimLink } from "@/types/graph";
import EntityDetailPanel from "./EntityDetailPanel";

interface KnowledgeGraphViewProps {
  entities: GraphEntity[];
  relations: GraphRelation[];
}

function buildSimData(
  entities: GraphEntity[],
  relations: GraphRelation[]
): { nodes: SimNode[]; links: SimLink[] } {
  const degreeMap = new Map<string, number>();
  for (const r of relations) {
    degreeMap.set(r.source_entity_id, (degreeMap.get(r.source_entity_id) || 0) + 1);
    degreeMap.set(r.target_entity_id, (degreeMap.get(r.target_entity_id) || 0) + 1);
  }

  const nodes: SimNode[] = entities.map((e) => ({
    ...e,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    fx: null,
    fy: null,
    degree: degreeMap.get(e.id) || 0,
  }));

  const nodeIds = new Set(entities.map((e) => e.id));
  const links: SimLink[] = relations
    .filter((r) => nodeIds.has(r.source_entity_id) && nodeIds.has(r.target_entity_id))
    .map((r) => ({
      source: r.source_entity_id,
      target: r.target_entity_id,
      relation_type: r.relation_type,
      id: r.id,
    }));

  return { nodes, links };
}

export default function KnowledgeGraphView({
  entities,
  relations,
}: KnowledgeGraphViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simRef = useRef<Simulation<SimNode, SimulationLinkDatum<SimNode>> | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const linksRef = useRef<SimLink[]>([]);
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const hoveredRef = useRef<SimNode | null>(null);

  const [selectedEntity, setSelectedEntity] = useState<GraphEntity | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 560 });
  const [tooltip, setTooltip] = useState<{
    show: boolean;
    x: number;
    y: number;
    name: string;
    type: string;
  }>({ show: false, x: 0, y: 0, name: "", type: "" });

  // Observe container size
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // Node radius based on degree
  const getRadius = useCallback(
    (node: SimNode) => Math.max(4, Math.min(16, 4 + node.degree * 1.2)),
    []
  );

  // Draw frame
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width, height } = dimensions;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const t = transformRef.current;
    ctx.clearRect(0, 0, width, height);
    ctx.save();
    ctx.translate(t.x, t.y);
    ctx.scale(t.k, t.k);

    const nodes = nodesRef.current;
    const links = linksRef.current;
    const hovered = hoveredRef.current;

    const connectedIds = new Set<string>();
    if (hovered) {
      connectedIds.add(hovered.id);
      for (const link of links) {
        const s = link.source as SimNode;
        const tgt = link.target as SimNode;
        if (s.id === hovered.id) connectedIds.add(tgt.id);
        if (tgt.id === hovered.id) connectedIds.add(s.id);
      }
    }

    // Draw links
    for (const link of links) {
      const source = link.source as SimNode;
      const target = link.target as SimNode;

      const isHighlighted =
        hovered &&
        (source.id === hovered.id || target.id === hovered.id);

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.strokeStyle = isHighlighted
        ? "rgba(13, 148, 136, 0.6)"
        : hovered
        ? "rgba(100, 116, 139, 0.06)"
        : "rgba(100, 116, 139, 0.15)";
      ctx.lineWidth = isHighlighted ? 1.5 : 0.5;
      ctx.stroke();

      // Edge label on hover
      if (isHighlighted && t.k > 0.6) {
        const mx = (source.x + target.x) / 2;
        const my = (source.y + target.y) / 2;
        ctx.font = "9px system-ui, sans-serif";
        ctx.fillStyle = "rgba(13, 148, 136, 0.8)";
        ctx.textAlign = "center";
        ctx.fillText(link.relation_type, mx, my - 3);
      }
    }

    // Draw nodes
    for (const node of nodes) {
      const r = getRadius(node);
      const color = ENTITY_TYPE_COLORS[node.entity_type] || "#6b7280";

      const dimmed = hovered && !connectedIds.has(node.id);

      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = dimmed
        ? "rgba(100, 116, 139, 0.1)"
        : color;
      ctx.globalAlpha = dimmed ? 0.3 : 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Stroke for hovered
      if (hovered && node.id === hovered.id) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Label for nodes with high degree or when zoomed in
      if (!dimmed && (node.degree >= 4 || t.k > 1.2)) {
        ctx.font = `${Math.max(9, 10 / Math.max(t.k, 0.6))}px system-ui, sans-serif`;
        ctx.fillStyle = dimmed
          ? "rgba(148, 163, 184, 0.2)"
          : "rgba(226, 232, 240, 0.9)";
        ctx.textAlign = "center";
        ctx.fillText(node.name, node.x, node.y + r + 11);
      }
    }

    ctx.restore();
  }, [dimensions, getRadius]);

  // Initialize simulation
  useEffect(() => {
    if (entities.length === 0) return;

    const { nodes, links } = buildSimData(entities, relations);
    nodesRef.current = nodes;
    linksRef.current = links;

    // Spread initial positions
    const { width, height } = dimensions;
    for (const node of nodes) {
      node.x = width / 2 + (Math.random() - 0.5) * width * 0.6;
      node.y = height / 2 + (Math.random() - 0.5) * height * 0.6;
    }

    const sim = forceSimulation<SimNode>(nodes)
      .force(
        "link",
        forceLink<SimNode, SimulationLinkDatum<SimNode>>(links as unknown as SimulationLinkDatum<SimNode>[])
          .id((d) => (d as SimNode).id)
          .distance(60)
          .strength(0.3)
      )
      .force("charge", forceManyBody().strength(-120).distanceMax(300))
      .force("center", forceCenter(width / 2, height / 2).strength(0.05))
      .force("collide", forceCollide<SimNode>().radius((d) => getRadius(d as SimNode) + 2))
      .alphaDecay(0.02)
      .on("tick", draw);

    simRef.current = sim;

    return () => {
      sim.stop();
    };
  }, [entities, relations, dimensions, draw, getRadius]);

  // Zoom & drag setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const sel = select<HTMLCanvasElement, unknown>(canvas);

    // Zoom
    const zoomBehavior = d3Zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.2, 5])
      .on("zoom", (event) => {
        transformRef.current = event.transform;
        draw();
      });

    sel.call(zoomBehavior);

    // Reset transform
    sel.call(zoomBehavior.transform, zoomIdentity);
    transformRef.current = { x: 0, y: 0, k: 1 };

    // Find node under mouse
    const findNode = (mx: number, my: number): SimNode | null => {
      const t = transformRef.current;
      const x = (mx - t.x) / t.k;
      const y = (my - t.y) / t.k;

      for (let i = nodesRef.current.length - 1; i >= 0; i--) {
        const node = nodesRef.current[i];
        const r = getRadius(node);
        const dx = x - node.x;
        const dy = y - node.y;
        if (dx * dx + dy * dy < (r + 4) * (r + 4)) return node;
      }
      return null;
    };

    // Drag
    const dragBehavior = d3Drag<HTMLCanvasElement, unknown>()
      .subject((event) => {
        const rect = canvas.getBoundingClientRect();
        const node = findNode(
          event.sourceEvent.clientX - rect.left,
          event.sourceEvent.clientY - rect.top
        );
        if (node) {
          node.fx = node.x;
          node.fy = node.y;
        }
        return node as SimulationNodeDatum | undefined;
      })
      .on("drag", (event) => {
        const t = transformRef.current;
        const node = event.subject as SimNode;
        node.fx = (event.sourceEvent.offsetX - t.x) / t.k;
        node.fy = (event.sourceEvent.offsetY - t.y) / t.k;
        simRef.current?.alpha(0.3).restart();
      })
      .on("end", (event) => {
        const node = event.subject as SimNode;
        node.fx = null;
        node.fy = null;
        simRef.current?.alpha(0.3).restart();
      });

    sel.call(dragBehavior as unknown as (selection: typeof sel) => void);

    // Hover / click
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const node = findNode(mx, my);
      const prev = hoveredRef.current;
      hoveredRef.current = node;
      canvas.style.cursor = node ? "pointer" : "grab";

      if (node) {
        setTooltip({
          show: true,
          x: mx + 12,
          y: my - 8,
          name: node.name,
          type: node.entity_type,
        });
      } else {
        setTooltip((prev) => (prev.show ? { ...prev, show: false } : prev));
      }

      if (prev !== node) draw();
    };

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const node = findNode(e.clientX - rect.left, e.clientY - rect.top);
      if (node) {
        setSelectedEntity(node);
      }
    };

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("click", handleClick);

    return () => {
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("click", handleClick);
    };
  }, [draw, getRadius]);

  return (
    <div ref={containerRef} className="relative w-full h-[560px] rounded-xl border border-border/50 bg-card/30 overflow-hidden">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ width: dimensions.width, height: dimensions.height }}
      />

      {/* Tooltip */}
      {tooltip.show && (
        <div
          className="absolute pointer-events-none z-10 rounded-lg border border-border/50 bg-card/95 backdrop-blur-md px-3 py-2 text-xs shadow-lg"
          style={{ left: tooltip.x, top: tooltip.y, maxWidth: 220 }}
        >
          <div className="font-medium">{tooltip.name}</div>
          <div className="text-muted-foreground">{tooltip.type}</div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-2 z-10">
        {Object.entries(ENTITY_TYPE_COLORS).map(([type, color]) => (
          <span
            key={type}
            className="inline-flex items-center gap-1 text-[10px] text-muted-foreground bg-background/60 backdrop-blur-sm rounded px-1.5 py-0.5"
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: color }}
            />
            {type}
          </span>
        ))}
      </div>

      {/* Entity Detail Panel */}
      <EntityDetailPanel
        entity={selectedEntity}
        relations={relations}
        entities={entities}
        onClose={() => setSelectedEntity(null)}
      />

      {/* Empty state */}
      {entities.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">No entities found</p>
        </div>
      )}
    </div>
  );
}
