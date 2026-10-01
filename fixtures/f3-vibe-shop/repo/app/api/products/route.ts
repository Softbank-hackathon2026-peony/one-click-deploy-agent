import { db } from "@/lib/db";

export async function GET() {
  const rows = db.prepare("SELECT * FROM products").all();
  return Response.json(rows);
}
