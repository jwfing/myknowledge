import { useRef, useEffect, useCallback } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  label: string;
  color: string;
  baseX: number;
  baseY: number;
  phase: number;
  speed: number;
}

interface Edge {
  from: number;
  to: number;
  opacity: number;
  targetOpacity: number;
  pulsePhase: number;
}

const LABELS = [
  "OAuth", "API Design", "Deploy Flow", "Auth", "Rate Limit",
  "Redis", "JWT", "WebSocket", "Docker", "CI/CD",
  "GraphQL", "REST", "Postgres", "TypeScript", "React",
  "Caching", "Queue", "Mutex", "Testing", "Logging",
  "S3", "gRPC", "Prisma", "Edge Fn", "CORS",
];

const COLORS = [
  "#0d9488", "#0d9488", "#0891b2", "#0891b2", "#059669",
  "#059669", "#ca8a04", "#0d9488", "#0891b2", "#059669",
  "#ca8a04", "#0d9488", "#0891b2", "#059669", "#ca8a04",
  "#0d9488", "#0891b2", "#059669", "#ca8a04", "#0d9488",
  "#0891b2", "#059669", "#ca8a04", "#0d9488", "#0891b2",
];

export default function KnowledgeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const frameRef = useRef(0);
  const timeRef = useRef(0);
  const sizeRef = useRef({ w: 0, h: 0 });

  const initGraph = useCallback((w: number, h: number) => {
    const nodes: Node[] = [];
    const padding = 60;

    for (let i = 0; i < LABELS.length; i++) {
      const x = padding + Math.random() * (w - padding * 2);
      const y = padding + Math.random() * (h - padding * 2);
      nodes.push({
        x, y, baseX: x, baseY: y,
        vx: 0, vy: 0,
        radius: 2.5 + Math.random() * 2.5,
        label: LABELS[i],
        color: COLORS[i],
        phase: Math.random() * Math.PI * 2,
        speed: 0.3 + Math.random() * 0.4,
      });
    }

    // Create edges between nearby nodes
    const edges: Edge[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].baseX - nodes[j].baseX;
        const dy = nodes[i].baseY - nodes[j].baseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < Math.min(w, h) * 0.35 && Math.random() > 0.4) {
          edges.push({
            from: i, to: j,
            opacity: 0.04 + Math.random() * 0.06,
            targetOpacity: 0.04 + Math.random() * 0.06,
            pulsePhase: Math.random() * Math.PI * 2,
          });
        }
      }
    }

    nodesRef.current = nodes;
    edgesRef.current = edges;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (!rect) return;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = rect.width + "px";
      canvas.style.height = rect.height + "px";
      ctx.scale(dpr, dpr);
      sizeRef.current = { w: rect.width, h: rect.height };
      initGraph(rect.width, rect.height);
    };

    resize();
    window.addEventListener("resize", resize);

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    const draw = () => {
      const { w, h } = sizeRef.current;
      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const mouse = mouseRef.current;
      const t = timeRef.current;
      timeRef.current += 0.008;

      ctx.clearRect(0, 0, w, h);

      // Update node positions (gentle floating)
      for (const node of nodes) {
        const floatX = Math.sin(t * node.speed + node.phase) * 15;
        const floatY = Math.cos(t * node.speed * 0.7 + node.phase + 1) * 12;
        let targetX = node.baseX + floatX;
        let targetY = node.baseY + floatY;

        // Mouse repulsion
        const dx = node.x - mouse.x;
        const dy = node.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const repelRadius = 120;

        if (dist < repelRadius && dist > 0) {
          const force = (1 - dist / repelRadius) * 30;
          targetX += (dx / dist) * force;
          targetY += (dy / dist) * force;
        }

        // Smooth interpolation
        node.x += (targetX - node.x) * 0.06;
        node.y += (targetY - node.y) * 0.06;
      }

      // Draw edges
      for (const edge of edges) {
        const a = nodes[edge.from];
        const b = nodes[edge.to];
        const midX = (a.x + b.x) / 2;
        const midY = (a.y + b.y) / 2;

        // Edge brightens near mouse
        const dxm = midX - mouse.x;
        const dym = midY - mouse.y;
        const distMouse = Math.sqrt(dxm * dxm + dym * dym);
        edge.targetOpacity = distMouse < 150
          ? 0.12 + (1 - distMouse / 150) * 0.15
          : 0.04 + Math.sin(t + edge.pulsePhase) * 0.02;
        edge.opacity += (edge.targetOpacity - edge.opacity) * 0.05;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = `rgba(13, 148, 136, ${edge.opacity})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Flowing particle on edge
        const particleT = ((t * 0.5 + edge.pulsePhase) % 1);
        const px = a.x + (b.x - a.x) * particleT;
        const py = a.y + (b.y - a.y) * particleT;
        if (edge.opacity > 0.08) {
          ctx.beginPath();
          ctx.arc(px, py, 1.2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(13, 148, 136, ${edge.opacity * 1.5})`;
          ctx.fill();
        }
      }

      // Draw nodes
      for (const node of nodes) {
        const dx = node.x - mouse.x;
        const dy = node.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const isNear = dist < 100;
        const scale = isNear ? 1.3 : 1;
        const r = node.radius * scale;

        // Glow
        if (isNear) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, r * 3, 0, Math.PI * 2);
          const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, r * 3);
          grad.addColorStop(0, node.color + "20");
          grad.addColorStop(1, node.color + "00");
          ctx.fillStyle = grad;
          ctx.fill();
        }

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fillStyle = node.color + (isNear ? "e0" : "70");
        ctx.fill();

        // Label
        if (isNear) {
          ctx.font = "500 11px Inter, sans-serif";
          ctx.fillStyle = node.color + "cc";
          ctx.textAlign = "center";
          ctx.fillText(node.label, node.x, node.y - r - 8);
        }
      }

      frameRef.current = requestAnimationFrame(draw);
    };

    frameRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [initGraph]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-auto"
      style={{ opacity: 0.55 }}
    />
  );
}
