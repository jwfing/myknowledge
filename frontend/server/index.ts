import express from "express";
import cors from "cors";
import pg from "pg";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const app = express();
app.use(cors());
app.use(express.json());

// Strip "+asyncpg" from SQLAlchemy-style URL for node-postgres compatibility
const connectionString = process.env.DATABASE_URL?.replace("+asyncpg", "");

const pool = new pg.Pool({
  connectionString,
  ssl: { rejectUnauthorized: false },
});

// ── Memories ──────────────────────────────────────────────

app.get("/api/memories", async (req, res) => {
  try {
    const { memory_type, project_id, search, limit = "50" } = req.query;
    const params: unknown[] = [];
    let idx = 1;
    const conditions: string[] = [];

    if (memory_type) {
      conditions.push(`m.memory_type = $${idx++}`);
      params.push(memory_type);
    }
    if (project_id) {
      conditions.push(`m.project_id = $${idx++}`);
      params.push(project_id);
    }
    if (search) {
      conditions.push(`m.content ILIKE $${idx++}`);
      params.push(`%${search}%`);
    }

    const where = conditions.length ? "WHERE " + conditions.join(" AND ") : "";

    const query = `
      SELECT m.id, m.content, m.memory_type, m.importance, m.project_id,
             m.tags, m.source_session_id, m.created_at, m.updated_at,
             json_build_object('name', p.name) AS project
      FROM memories m
      LEFT JOIN projects p ON m.project_id = p.id
      ${where}
      ORDER BY m.created_at DESC
      LIMIT $${idx}
    `;
    params.push(Number(limit));

    const { rows } = await pool.query(query, params);
    res.json(rows);
  } catch (err) {
    console.error("GET /api/memories error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/memory-stats", async (_req, res) => {
  try {
    const [memoriesRes, projectsRes] = await Promise.all([
      pool.query("SELECT memory_type FROM memories"),
      pool.query(
        "SELECT id, name, description, tech_stack, created_at FROM projects ORDER BY name ASC"
      ),
    ]);

    const memories = memoriesRes.rows as { memory_type: string }[];
    const projects = projectsRes.rows;

    res.json({
      total: memories.length,
      semantic: memories.filter((m) => m.memory_type === "semantic").length,
      episodic: memories.filter((m) => m.memory_type === "episodic").length,
      procedural: memories.filter((m) => m.memory_type === "procedural").length,
      projects,
    });
  } catch (err) {
    console.error("GET /api/memory-stats error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// ── Entities & Relations (Knowledge Graph) ────────────────

app.get("/api/entities", async (req, res) => {
  try {
    const { project_id, entity_type } = req.query;
    const params: unknown[] = [];
    let idx = 1;
    const conditions: string[] = [];

    if (project_id) {
      conditions.push(`e.project_id = $${idx++}`);
      params.push(project_id);
    }
    if (entity_type) {
      conditions.push(`e.entity_type = $${idx++}`);
      params.push(entity_type);
    }

    const where = conditions.length ? "WHERE " + conditions.join(" AND ") : "";

    const query = `
      SELECT e.id, e.name, e.entity_type, e.project_id, e.description,
             json_build_object('name', p.name) AS project
      FROM entities e
      LEFT JOIN projects p ON e.project_id = p.id
      ${where}
    `;

    const { rows } = await pool.query(query, params);
    res.json(rows);
  } catch (err) {
    console.error("GET /api/entities error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/relations", async (_req, res) => {
  try {
    const { rows } = await pool.query(
      "SELECT id, source_entity_id, target_entity_id, relation_type, description FROM relations"
    );
    res.json(rows);
  } catch (err) {
    console.error("GET /api/relations error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/graph-stats", async (_req, res) => {
  try {
    const [entitiesRes, relationsRes] = await Promise.all([
      pool.query("SELECT entity_type FROM entities"),
      pool.query("SELECT id FROM relations"),
    ]);

    const entities = entitiesRes.rows as { entity_type: string }[];
    const relations = relationsRes.rows;

    const entityTypeCounts: Record<string, number> = {};
    for (const e of entities) {
      entityTypeCounts[e.entity_type] =
        (entityTypeCounts[e.entity_type] || 0) + 1;
    }

    res.json({
      totalEntities: entities.length,
      totalRelations: relations.length,
      entityTypeCounts,
    });
  } catch (err) {
    console.error("GET /api/graph-stats error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/entity-memories/:entityId", async (req, res) => {
  try {
    const { entityId } = req.params;
    const { rows } = await pool.query(
      `SELECT m.id, m.content, m.memory_type, m.importance, m.created_at
       FROM memory_entity_links mel
       JOIN memories m ON mel.memory_id = m.id
       WHERE mel.entity_id = $1
       LIMIT 20`,
      [entityId]
    );
    res.json(rows);
  } catch (err) {
    console.error("GET /api/entity-memories error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// ── Start ─────────────────────────────────────────────────

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`API server running on http://localhost:${PORT}`);
});
