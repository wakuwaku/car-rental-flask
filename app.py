from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "dev"

db = SQLAlchemy(app)


@app.context_processor
def inject_datetime():
    return {"datetime": datetime}


@app.get("/img/<path:filename>")
def local_image(filename):
    # Allowed filenames located in the project root
    allowed = {"red.jpg", "white.jpg", "white.png", "blue.webp", "blue.wbp"}
    if filename not in allowed:
        abort(404)
    file_path = os.path.join(app.root_path, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(app.root_path, filename)


def ensure_local_images():
    # Map colors to preferred filenames; fallback if first choice missing
    color_map = {
        "red": ["red.jpg"],
        "white": ["white.jpg", "white.png"],
        "blue": ["blue.wbp", "blue.webp"],
    }
    changed = False
    for c in Car.query.all():
        key = (c.color or "").lower()
        candidates = color_map.get(key, [])
        chosen = None
        for fname in candidates:
            if os.path.exists(os.path.join(app.root_path, fname)):
                chosen = fname
                break
        if chosen:
            url = f"/img/{chosen}"
            if c.image_url != url:
                c.image_url = url
                changed = True
    if changed:
        db.session.commit()


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    weekday_price = db.Column(db.Integer, nullable=False, default=100)  # €100 Mon-Fri
    weekend_price = db.Column(db.Integer, nullable=False, default=200)  # €200 Sat/Sun
    image_url = db.Column(db.String(255), nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)  # inclusive
    end_date = db.Column(db.Date, nullable=False)    # inclusive
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    car = db.relationship("Car", backref=db.backref("bookings", lazy=True))


def seed_cars():
    if Car.query.count() == 0:
        # Unsplash images as placeholders. You can replace with your own assets.
        cars = [
            Car(
                name="Tesla Model 3 Performance",
                color="Red",
                #image_url="https://images.unsplash.com/photo-1511396275271-b66e60116917?q=80&w=1600&auto=format&fit=crop"
                image_url="https://media.autoexpress.co.uk/image/private/s--X-WVjvBW--/f_auto,t_content-image-full-desktop@1/v1562246899/autoexpress/2018/09/model-3-performance-red-front-motion-sf-skyline.jpg"
            ),
            Car(
                name="Tesla Model 3 Performance",
                color="White",
                image_url="https://images.unsplash.com/photo-1552519507-da3b142c6e3d?q=80&w=1600&auto=format&fit=crop"
            ),
            Car(
                name="Tesla Model 3 Performance",
                color="Blue",
                image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1600&auto=format&fit=crop"
            ),
            Car(
                name="Tesla Model 3 Performance",
                color="Red",
                #image_url="https://images.unsplash.com/photo-1511396275271-b66e60116917?q=80&w=1600&auto=format&fit=crop"
                image_url="https://media.autoexpress.co.uk/image/private/s--X-WVjvBW--/f_auto,t_content-image-full-desktop@1/v1562246899/autoexpress/2018/09/model-3-performance-red-front-motion-sf-skyline.jpg"
            ),
        ]
        db.session.add_all(cars)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_cars()
    ensure_local_images()


def daterange(start_d: date, end_d: date):
    for n in range((end_d - start_d).days + 1):
        yield start_d + timedelta(days=n)


def compute_price(car: Car, start_d: date, end_d: date):
    total = 0
    days = 0
    for d in daterange(start_d, end_d):
        days += 1
        # Python weekday: Monday=0 ... Sunday=6; weekend is 5,6
        if d.weekday() >= 5:
            total += car.weekend_price
        else:
            total += car.weekday_price
    return total, days


def has_overlap(car_id: int, new_start: date, new_end: date) -> bool:
    # Overlap if: new_start <= existing_end and new_end >= existing_start
    overlap = (
        Booking.query.filter(
            Booking.car_id == car_id,
            Booking.start_date <= new_end,
            Booking.end_date >= new_start,
        ).first()
        is not None
    )
    return overlap


@app.route("/")
def index():
    cars = Car.query.order_by(Car.id.asc()).all()
    return render_template("index.html", cars=cars)


@app.route("/cars/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car_detail.html", car=car)


@app.get("/api/cars/<int:car_id>/disabled-dates")
def api_disabled_dates(car_id):
    # Return array of {from: "YYYY-MM-DD", to: "YYYY-MM-DD"}
    car = Car.query.get_or_404(car_id)
    bookings = (
        Booking.query.filter_by(car_id=car.id)
        .order_by(Booking.start_date.asc())
        .all()
    )
    ranges = []
    for b in bookings:
        ranges.append(
            {"from": b.start_date.isoformat(), "to": b.end_date.isoformat()}
        )
    return jsonify(ranges)


@app.get("/api/quote")
def api_quote():
    try:
        car_id = int(request.args.get("car_id", ""))
        start_s = request.args.get("start")
        end_s = request.args.get("end")
        if not (car_id and start_s and end_s):
            return jsonify({"error": "Missing parameters"}), 400

        start_d = date.fromisoformat(start_s)
        end_d = date.fromisoformat(end_s)
        if end_d < start_d:
            return jsonify({"error": "End date before start date"}), 400

        car = Car.query.get_or_404(car_id)
        total, days = compute_price(car, start_d, end_d)
        return jsonify({"car_id": car_id, "start": start_s, "end": end_s, "days": days, "total": total})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/book")
def book():
    form = request.form
    try:
        car_id = int(form.get("car_id", ""))
        name = (form.get("customer_name") or "").strip()
        email = (form.get("customer_email") or "").strip()
        start_s = form.get("start_date")
        end_s = form.get("end_date")

        if not all([car_id, name, email, start_s, end_s]):
            return render_template(
                "error.html",
                message="Missing required fields.",
                back_url=url_for("car_detail", car_id=car_id) if car_id else url_for("index"),
            ), 400

        start_d = date.fromisoformat(start_s)
        end_d = date.fromisoformat(end_s)
        if end_d < start_d:
            return render_template(
                "error.html",
                message="End date cannot be before start date.",
                back_url=url_for("car_detail", car_id=car_id),
            ), 400

        # Optional: enforce rentals cannot start in the past
        # if start_d < date.today():
        #     return render_template("error.html", message="Start date cannot be in the past.", back_url=url_for("car_detail", car_id=car_id)), 400

        car = Car.query.get_or_404(car_id)

        if has_overlap(car.id, start_d, end_d):
            return render_template(
                "error.html",
                message="Selected period overlaps an existing booking. Please choose different dates.",
                back_url=url_for("car_detail", car_id=car_id),
            ), 409

        total, days = compute_price(car, start_d, end_d)

        booking = Booking(
            car_id=car.id,
            start_date=start_d,
            end_date=end_d,
            customer_name=name,
            customer_email=email,
        )
        db.session.add(booking)
        db.session.commit()

        return redirect(url_for("confirm", booking_id=booking.id))
    except Exception as e:
        return render_template(
            "error.html",
            message=f"An error occurred: {e}",
            back_url=url_for("index"),
        ), 400


@app.get("/confirm/<int:booking_id>")
def confirm(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    total, days = compute_price(booking.car, booking.start_date, booking.end_date)
    return render_template("confirmation.html", booking=booking, total=total, days=days)


@app.get("/admin/bookings")
def admin_bookings():
    bookings = (
        Booking.query.order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("admin_bookings.html", bookings=bookings)


# Templates (Jinja) stored in templates/ and Tailwind/Flatpickr via CDN in base.html

if __name__ == "__main__":
    # For local development only
    #app.run(debug=True)
    # For Lan only
    app.run(host='0.0.0.0', port=5001)
