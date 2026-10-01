import { writeFile } from "fs/promises";
import path from "path";

export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file") as File;
  await writeFile(path.join(process.cwd(), "public/uploads", file.name), Buffer.from(await file.arrayBuffer()));
  return Response.json({ ok: true });
}
