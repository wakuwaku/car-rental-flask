# Tesla Model 3 Performance Rental (Flask)

A simple car rental website built with Python (Flask) featuring:
- 3 Tesla Model 3 Performance cars (Red, White, Blue)
- Date range picker with disabled/unavailable dates
- Pricing: €100/day on weekdays, €200/day on Saturday and Sunday
- Live price quote as the user selects dates
- Vibrant UI with Tailwind CSS and Flatpickr
- SQLite database with automatic seeding of cars

## Tech Stack
- Python 3.10+ (tested on macOS)
- Flask + SQLAlchemy (SQLite)
- Jinja2 templates
- Tailwind (CDN) for styles
- Flatpickr (CDN) for date range picker

## Features
- Home page: list of cars with images and quick info
- Car detail page: select rental period via date range picker; unavailable dates are disabled
- Live pricing via server API (/api/quote)
- Booking creation with server-side overlap validation
- Confirmation page with booking summary
- Simple admin list of bookings (/admin/bookings)

## Pricing Rules
- Weekdays (Mon–Fri): €100/day
- Weekends (Sat, Sun): €200/day
- Pricing calculates per day across the inclusive date range

## Availability Rules
- Dates are inclusive (start and end)
- A new booking is rejected if it overlaps any existing booking for the same car
- Frontend datepicker disables already booked date ranges

## Run Locally
1) Create and activate a virtual environment
- macOS/Linux:
  python3 -m venv venv
  source venv/bin/activate

- Windows (PowerShell):
  python -m venv venv
  venv\Scripts\Activate.ps1

2) Install dependencies
  pip install -r requirements.txt

3) Start the app
  python app.py

4) Open in your browser
  http://127.0.0.1:5001/

On first run, the database (app.db) is created and 3 Tesla cars are seeded automatically.

## Endpoints
- GET /: list cars
- GET /cars/<id>: car details + booking form
- GET /api/cars/<id>/disabled-dates: returns booked date ranges to disable
- GET /api/quote?car_id=...&start=YYYY-MM-DD&end=YYYY-MM-DD: live price
- POST /book: create a booking (server validates overlap and recalculates price)
- GET /confirm/<booking_id>: booking confirmation
- GET /admin/bookings: simple read-only list of all bookings

## Data Model
- Car(id, name, color, weekday_price=100, weekend_price=200, image_url)
- Booking(id, car_id, start_date, end_date, customer_name, customer_email, created_at)

## Resetting Data
To reset all data, stop the app and delete the SQLite file:
- rm app.db
Then start the app again (it will re-seed cars).

## Customization
- You can change colors, images, and branding in templates/base.html and templates/index.html
- Pricing defaults can be adjusted in app.py (Car model defaults)
- To pre-block dates (e.g., maintenance), create corresponding Booking rows

## Notes
- This demo uses CDN links for Tailwind and Flatpickr.
- Prices are displayed as euros; formatting uses Intl.NumberFormat in the browser.
- Server-side validation is the source of truth for availability and pricing.
