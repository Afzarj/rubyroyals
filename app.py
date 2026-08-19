import os
import io
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from openpyxl import Workbook
from datetime import datetime

app = Flask(__name__)
app.secret_key = (
    os.environ.get("FLASK_SECRET")
    or os.environ.get("SECRET_KEY")
    or "dev_secret"
)

# --- Database Config ---
# Use SQLite locally, PostgreSQL on Render
database_url = os.environ.get("DATABASE_URL", "sqlite:///pledges.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Models ---
class Pledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20))
    age = db.Column(db.Integer)
    father_name = db.Column(db.String(100))
    family_name = db.Column(db.String(100))
    kids_names = db.Column(db.String(200))
    education = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(10), nullable=False)
    alt_number = db.Column(db.String(10))
    aadhar = db.Column(db.String(12), nullable=False)
    hc_claim_form = db.Column(db.String(50))
    intro = db.Column(db.String(20))
    num_ornaments = db.Column(db.Integer)
    ornaments_details = db.Column(db.Text)  # JSON string of ornaments
    pledge_date = db.Column(db.Date)
    total_amount = db.Column(db.Float)
    total_grams = db.Column(db.Float)
    return_jewellery = db.Column(db.Float, default=0)
    balance_jewellery = db.Column(db.Float)
    repayment = db.Column(db.String(20))
    repayment_details = db.Column(db.Text)  # JSON string of repayments
    repayment_total_amount = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)

# --- Auth Decorator ---
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("is_admin"):
            return fn(*args, **kwargs)
        flash("Admin login required", "danger")
        return redirect(url_for("admin_login", next=request.path))
    return wrapper

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def pledge_form():
    if request.method == "POST":
        bill_no = request.form.get("BillNo")
        phone = request.form.get("PhoneNumber")
        aadhar = request.form.get("AadharNumber")

        # Validations
        if Pledge.query.filter_by(bill_no=bill_no).first():
            return render_template("form.html", error=f"Duplicate Bill No {bill_no} already exists")

        if not phone.isdigit() or len(phone) != 10:
            return render_template("form.html", error="Phone number must be exactly 10 digits")

        if not aadhar.isdigit() or len(aadhar) != 12:
            return render_template("form.html", error="Aadhar number must be exactly 12 digits")
        repayment_total_amount = sum(
            float(value or 0)
            for key, value in request.form.items()
            if key.startswith("RepayAmount")
        )
        pledge_date_str = request.form.get("PledgeDate")
        pledge_date = None
        if pledge_date_str:
            try:
                pledge_date = datetime.strptime(pledge_date_str, "%Y-%m-%d").date()
            except ValueError:
                return render_template("form.html", error="Invalid date format")
        pledge = Pledge(
            bill_no=bill_no,
            name=request.form.get("Name"),
            gender=request.form.get("Gender"),
            age=request.form.get("Age"),
            father_name=request.form.get("FatherName"),
            family_name=request.form.get("FamilyName"),
            kids_names=",".join([request.form.get("KidsNames1",""), request.form.get("KidsNames2",""), request.form.get("KidsNames3","")]),
            education=request.form.get("Education"),
            occupation=request.form.get("Occupation"),
            address=request.form.get("Address"),
            phone=phone,
            alt_number=request.form.get("AltNumber"),
            aadhar=aadhar,
            hc_claim_form=request.form.get("HCClaimFormNumber"),
            intro=request.form.get("Intro"),
            num_ornaments=request.form.get("NumOrnaments"),
            ornaments_details=str({k:v for k,v in request.form.items() if "Ornament" in k or "Grams" in k}),
            pledge_date=pledge_date,
            total_amount=float(request.form.get("TotalAmounts")),
            total_grams=float(request.form.get("TotalGrams")),
            return_jewellery=float(request.form.get("ReturnJewellery")),
            balance_jewellery=float(request.form.get("BalanceJewellery")),
            repayment=request.form.get("Repayment"),
            repayment_details=str({k:v for k,v in request.form.items() if "Repay" in k}),
            repayment_total_amount=round(repayment_total_amount, 2),
            remarks=request.form.get("Remarks")
        )
        db.session.add(pledge)
        db.session.commit()
        return redirect(url_for("success"))

    return render_template("form.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/export")
@admin_required
def export_excel():
    pledges = Pledge.query.all()

    # Build a list of dicts with ALL fields
    data = []
    for p in pledges:
        data.append({
            "ID": p.id,
            "BillNo": p.bill_no,
            "Name": p.name,
            "Gender": p.gender,
            "Age": p.age,
            "FatherName": p.father_name,
            "FamilyName": p.family_name,
            "KidsNames": p.kids_names,
            "Education": p.education,
            "Occupation": p.occupation,
            "Address": p.address,
            "Phone": p.phone,
            "AltNumber": p.alt_number,
            "Aadhar": p.aadhar,
            "HCClaimForm": p.hc_claim_form,
            "Intro": p.intro,
            "NumOrnaments": p.num_ornaments,
            "OrnamentsDetails": p.ornaments_details,
            "PledgeDate": p.pledge_date,
            "TotalAmount": p.total_amount,
            "TotalGrams": p.total_grams,
            "ReturnJewellery": p.return_jewellery,
            "BalanceJewellery": p.balance_jewellery,
            "Repayment": p.repayment,
            "RepaymentDetails": p.repayment_details,
            "RepaymentTotalAmount": p.repayment_total_amount or 0,
            "Remarks": p.remarks
        })

    output = io.BytesIO()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Pledges"

    if data:
        headers = list(data[0].keys())
        worksheet.append(headers)
        for row in data:
            worksheet.append([row[header] for header in headers])

    workbook.save(output)
    output.seek(0)
    filename = f"pledges_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)


@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password")
        if pw == os.environ.get("ADMIN_PASSWORD","admin123"):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid password","danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("pledge_form"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q = request.args.get("q", "").lower()
    all_pledges = Pledge.query.all()
    selected_year = request.args.get("year", "")
    pledges = all_pledges

    if q:
        pledges = [p for p in pledges if q in str(p.__dict__).lower()]

    if selected_year.isdigit():
        pledges = [p for p in pledges if p.pledge_date and p.pledge_date.year == int(selected_year)]

    total_bills = len(pledges)
    total_amount = round(sum(p.total_amount or 0 for p in pledges), 2)
    total_grams = round(sum(p.total_grams or 0 for p in pledges), 2)
    outstanding_grams = round(sum(p.balance_jewellery or 0 for p in pledges), 2)
    average_amount = round(total_amount / total_bills, 2) if total_bills else 0
    average_age = round(sum(p.age or 0 for p in pledges) / total_bills, 1) if total_bills else 0
    repayment_counts = {"Full": 0, "Partial": 0, "Nil": 0}
    for p in pledges:
        if p.repayment in repayment_counts:
            repayment_counts[p.repayment] += 1

    gender_counts = {"Male": 0, "Female": 0, "Other": 0}
    for p in pledges:
        if p.gender in gender_counts:
            gender_counts[p.gender] += 1

    monthly_counts = {}
    for pledge in pledges:
        if pledge.pledge_date:
            month_key = pledge.pledge_date.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
    monthly_activity = [
        {"label": datetime.strptime(month, "%Y-%m").strftime("%b %Y"), "count": monthly_counts[month]}
        for month in sorted(monthly_counts)[-6:]
    ]
    max_monthly_count = max((item["count"] for item in monthly_activity), default=1)
    repayment_rate = round((repayment_counts["Full"] / total_bills) * 100) if total_bills else 0

    yearly_source = all_pledges
    if q:
        yearly_source = [p for p in yearly_source if q in str(p.__dict__).lower()]
    yearly_groups = {}
    for pledge in yearly_source:
        if pledge.pledge_date:
            year = pledge.pledge_date.year
            yearly_groups.setdefault(year, []).append(pledge)

    yearly_metrics = []
    previous_count = None
    for year in sorted(yearly_groups):
        year_records = yearly_groups[year]
        year_count = len(year_records)
        year_repayment = {"Full": 0, "Partial": 0, "Nil": 0}
        for pledge in year_records:
            if pledge.repayment in year_repayment:
                year_repayment[pledge.repayment] += 1
        yearly_metrics.append({
            "year": year,
            "count": year_count,
            "amount": round(sum(p.total_amount or 0 for p in year_records), 2),
            "grams": round(sum(p.total_grams or 0 for p in year_records), 2),
            "returned": round(sum(p.return_jewellery or 0 for p in year_records), 2),
            "balance": round(sum(p.balance_jewellery or 0 for p in year_records), 2),
            "full": year_repayment["Full"],
            "partial": year_repayment["Partial"],
            "nil": year_repayment["Nil"],
            "growth": round(((year_count - previous_count) / previous_count) * 100, 1) if previous_count else None
        })
        previous_count = year_count

    year_options = sorted({item["year"] for item in yearly_metrics}, reverse=True)
    max_year_count = max((item["count"] for item in yearly_metrics), default=1)
    all_time_count = len(all_pledges)
    all_time_amount = round(sum(p.total_amount or 0 for p in all_pledges), 2)
    all_time_grams = round(sum(p.total_grams or 0 for p in all_pledges), 2)

    return render_template("admin_dashboard.html",
                           records=pledges,
                           total_bills=total_bills,
                           total_amount=total_amount,
                           total_grams=total_grams,
                           outstanding_grams=outstanding_grams,
                           average_amount=average_amount,
                           average_age=average_age,
                           repayment_counts=repayment_counts,
                           repayment_rate=repayment_rate,
                           gender_counts=gender_counts,
                           monthly_activity=monthly_activity,
                           max_monthly_count=max_monthly_count,
                           search_query=request.args.get("q", ""),
                           selected_year=selected_year,
                           year_options=year_options,
                           yearly_metrics=yearly_metrics,
                           max_year_count=max_year_count,
                           all_time_count=all_time_count,
                           all_time_amount=all_time_amount,
                           all_time_grams=all_time_grams)
@app.route("/admin/delete/<int:pledge_id>")
@admin_required
def admin_delete(pledge_id):
    pledge = Pledge.query.get_or_404(pledge_id)
    db.session.delete(pledge)
    db.session.commit()
    flash("Pledge deleted", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit/<int:pledge_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(pledge_id):
    pledge = Pledge.query.get_or_404(pledge_id)
    if request.method == "POST":
        pledge.gender = request.form.get("Gender")
        pledge.name = request.form.get("Name")
        pledge.age = request.form.get("Age") or None
        pledge.father_name = request.form.get("FatherName")
        pledge.family_name = request.form.get("FamilyName")
        pledge.kids_names = ",".join([
            request.form.get("KidsNames1", ""),
            request.form.get("KidsNames2", ""),
            request.form.get("KidsNames3", "")
        ])
        pledge.education = request.form.get("Education")
        pledge.occupation = request.form.get("Occupation")
        pledge.address = request.form.get("Address")
        pledge.phone = request.form.get("PhoneNumber")
        pledge.alt_number = request.form.get("AltNumber")
        pledge.aadhar = request.form.get("AadharNumber")
        pledge.hc_claim_form = request.form.get("HCClaimFormNumber")
        pledge.intro = request.form.get("Intro")
        pledge.num_ornaments = request.form.get("NumOrnaments") or None
        pledge.ornaments_details = str({k: v for k, v in request.form.items() if "Ornament" in k or "Grams" in k})
        pledge.pledge_date = datetime.strptime(request.form.get("PledgeDate"), "%Y-%m-%d").date() if request.form.get("PledgeDate") else None
        pledge.total_amount = float(request.form.get("TotalAmounts") or 0)
        pledge.total_grams = float(request.form.get("TotalGrams") or 0)
        pledge.return_jewellery = float(request.form.get("ReturnJewellery") or 0)
        pledge.balance_jewellery = float(request.form.get("BalanceJewellery") or 0)
        pledge.repayment = request.form.get("Repayment")
        pledge.repayment_details = str({k: v for k, v in request.form.items() if "Repay" in k})
        pledge.repayment_total_amount = round(sum(
            float(value or 0)
            for key, value in request.form.items()
            if key.startswith("RepayAmount")
        ), 2)
        pledge.remarks = request.form.get("Remarks")
        db.session.commit()
        flash("Pledge updated", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("form.html", data=pledge, edit=True)



if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
