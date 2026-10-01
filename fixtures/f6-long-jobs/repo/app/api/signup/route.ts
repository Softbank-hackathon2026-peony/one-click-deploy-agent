import nodemailer from "nodemailer";
import { pool } from "@/lib/db";

const mailer = nodemailer.createTransport({ host: process.env.SMTP_HOST });

export async function POST(req: Request) {
  const { email } = await req.json();
  await pool.query("INSERT INTO users (email) VALUES ($1)", [email]);
  mailer.sendMail({ to: email, subject: "환영합니다" });
  return Response.json({ ok: true });
}
