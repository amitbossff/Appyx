from flask import Flask, request, jsonify, send_file
from google_play_scraper import reviews, Sort
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)

# ---------- HOME ----------
@app.route("/")
def home():
    return send_file(os.path.join(os.getcwd(), "pdf1.html"))


# ---------- REVIEWS API ----------
@app.route("/reviews")
def get_reviews():
    link = request.args.get("link", "").strip()
    date_str = request.args.get("date", "").strip()

    if not link or not date_str:
        return jsonify({
            "status": "error",
            "message": "Link/App ID and Date required",
            "data": []
        })

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if target_date > date.today():
            return jsonify({
                "status": "error",
                "message": "Future date not allowed",
                "data": []
            })

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

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        })


# ---------- PDF DOWNLOAD ----------
@app.route("/reviews-pdf")
def reviews_pdf():
    link = request.args.get("link", "").strip()
    date_str = request.args.get("date", "").strip()

    if not link or not date_str:
        return "Invalid input", 400

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

    names = []
    seen = set()

    for r in result:
        if r.get("at") and r["at"].date() == target_date:
            name = r.get("userName", "")
            if name and name not in seen:
                seen.add(name)
                names.append(name)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Play Store Review Names")

    y -= 25
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Date: {date_str}")
    pdf.drawString(350, y, f"Total: {len(names)}")

    y -= 30
    pdf.setFont("Helvetica", 10)

    for i, name in enumerate(names, start=1):
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

        pdf.drawString(50, y, f"{i}. {name}")
        y -= 18

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="playstore_reviews.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
