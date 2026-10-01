import ExcelJS from "exceljs";
import { pool } from "@/lib/db";

export async function GET() {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("orders");
  for (let offset = 0; offset < 200000; offset += 1000) {
    const { rows } = await pool.query("SELECT * FROM orders ORDER BY id LIMIT 1000 OFFSET $1", [offset]);
    rows.forEach((r) => ws.addRow(Object.values(r)));
  }
  const buf = await wb.xlsx.writeBuffer();
  return new Response(buf);
}
