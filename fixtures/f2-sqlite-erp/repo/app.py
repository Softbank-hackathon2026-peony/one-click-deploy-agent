import io
import os

from flask import Flask, request, send_file, session
from openpyxl import Workbook

from db import execute_with_retry, get_conn

app = Flask(__name__)
app.secret_key = "change-me"
UPLOAD_DIR = "uploads"


@app.route("/login", methods=["POST"])
def login():
    session["email"] = request.form["email"]
    return {"ok": True}


@app.get("/approvals")
def list_approvals():
    rows = get_conn().execute("SELECT * FROM approvals ORDER BY id DESC").fetchall()
    return {"items": [dict(r) for r in rows]}


@app.post("/approvals")
def create_approval():
    execute_with_retry("UPDATE counters SET n = n + 1 WHERE name = 'approval'")
    n = get_conn().execute("SELECT n FROM counters WHERE name = 'approval'").fetchone()["n"]
    execute_with_retry("INSERT INTO approvals (doc_no, title, status) VALUES (?, ?, 'pending')",
                       (f"AP-{n:06d}", request.json["title"]))
    return {"doc_no": f"AP-{n:06d}"}, 201


@app.post("/approvals/<int:approval_id>/approve")
def approve(approval_id):
    execute_with_retry("UPDATE approvals SET status = 'approved' WHERE id = ?", (approval_id,))
    return {"ok": True}


@app.get("/export")
def export():
    wb = Workbook()
    ws = wb.active
    for row in get_conn().execute("SELECT * FROM approvals"):
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, download_name="approvals.xlsx")


@app.post("/attachments")
def upload():
    f = request.files["file"]
    f.save(os.path.join(UPLOAD_DIR, f.filename))
    return {"ok": True}
