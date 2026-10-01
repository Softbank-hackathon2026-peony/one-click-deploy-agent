const express = require("express");
const { Pool } = require("pg");

const app = express();
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

app.get("/health", (req, res) => res.send("ok"));

app.get("/reports", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM reports ORDER BY created_at DESC LIMIT 50");
  res.json(rows);
});

app.listen(process.env.PORT || 3000);
