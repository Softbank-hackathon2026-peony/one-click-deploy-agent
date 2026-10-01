import Stripe from "stripe";
import { db } from "@/lib/db";

const stripe = new Stripe(process.env.STRIPE_KEY!);

export async function POST(req: Request) {
  const { productId } = await req.json();
  const p = db.prepare("SELECT stock, price FROM products WHERE id = ?").get(productId) as any;
  if (p.stock > 0) {
    db.prepare("UPDATE products SET stock = stock - 1 WHERE id = ?").run(productId);
  }
  const intent = await stripe.paymentIntents.create({ amount: p.price, currency: "krw" });
  return Response.json({ clientSecret: intent.client_secret });
}
