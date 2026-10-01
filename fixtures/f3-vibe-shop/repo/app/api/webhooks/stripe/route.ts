import { db } from "@/lib/db";

export async function POST(req: Request) {
  const event = await req.json();
  if (event.type === "payment_intent.succeeded") {
    db.prepare("INSERT INTO orders (intent_id) VALUES (?)").run(event.data.object.id);
  }
  return new Response("ok");
}
