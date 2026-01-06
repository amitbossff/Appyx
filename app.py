from flask import Flask, request, jsonify, send_file
from google_play_scraper import reviews, Sort
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# ---------- HOME ----------
@app.route("/")
def home():
    return send_file("index.html")


# ---------- REVIEWS API ----------
@app.route("/reviews")
def get_reviews():
    link = request.args.get("link", "").strip()
    date_str = request.args.get("date", "").strip()

    if not link or not date_str:
        return jsonify({"status": "error", "message": "Link and date required", "data": []})

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if target_date > date.today():
        return jsonify({"status": "error", "message": "Future date not allowed", "data": []})

    # App ID extract
    if "id=" in link:
        app_id = link.split("id=")[1].split("&")[0]
    else:
        app_id = link

    result, _ = reviews(
        app_id,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=15000
    )

    users = []
    seen = set()

    for r in result:
        if r.get("at") and r["at"].date() == target_date:
            name = r.get("userName", "").strip()
            if name and name not in seen:
                seen.add(name)
                users.append({"user": name})

    return jsonify({
        "status": "success",
        "count": len(users),
        "data": users
    })


# ---------- PDF ----------
@app.route("/reviews-pdf")
def reviews_pdf():
    link = request.args.get("link")
    date_str = request.args.get("date")

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if "id=" in link:
        app_id = link.split("id=")[1].split("&")[0]
    else:
        app_id = link

    result, _ = reviews(
        app_id,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=15000
    )

    names, seen = [], set()

    for r in result:
        if r.get("at") and r["at"].date() == target_date:
            name = r["userName"]
            if name not in seen:
                seen.add(name)
                names.append(name)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Play Store Reviews")

    y -= 20
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Date: {date_str}")
    pdf.drawString(350, y, f"Total: {len(names)}")

    y -= 30
    pdf.setFont("Helvetica", 10)

    for i, name in enumerate(names, 1):
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, f"{i}. {name}")
        y -= 15

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="reviews.pdf",
                     mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
