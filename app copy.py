import os
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import io
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

# In-memory storage (replace with DB if needed)
records = []

@app.route("/", methods=["GET", "POST"])
def pledge_form():
    if request.method == "POST":
        form_data = request.form.to_dict(flat=False)

        # --- Validation rules ---
        bill_no = form_data.get("BillNo", [""])[0]
        phone = form_data.get("PhoneNumber", [""])[0]
        aadhar = form_data.get("AadharNumber", [""])[0]

        # 1. Bill No must be unique
        for rec in records:
            if rec.get("BillNo", [""])[0] == bill_no:
                return render_template("form.html",
                                       error=f"Duplicate Bill No {bill_no} already exists",
                                       data=form_data)

        # 2. Phone must be exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            return render_template("form.html",
                                   error="Phone number must be exactly 10 digits",
                                   data=form_data)

        # 3. Aadhar must be exactly 12 digits
        if not aadhar.isdigit() or len(aadhar) != 12:
            return render_template("form.html",
                                   error="Aadhar number must be exactly 12 digits",
                                   data=form_data)

        # 4. No spaces in numeric fields
        numeric_fields = ["Age", "AadharNumber", "BillNo", "HCClaimFormNumber",
                          "TotalAmounts", "TotalGrams", "ReturnJewellery", "BalanceJewellery"]
        for field in numeric_fields:
            if field in form_data and any(" " in val for val in form_data[field]):
                return render_template("form.html",
                                       error=f"Spaces not allowed in {field}",
                                       data=form_data)

        # If all validations pass, save record
        records.append(form_data)
        return redirect(url_for("success"))

    return render_template("form.html")


@app.route("/success")
def success():
    return render_template("success.html")

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("is_admin"):
            return fn(*args, **kwargs)
        flash("Admin login required", "danger")
        return redirect(url_for("admin_login", next=request.path))
    return wrapper

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw and pw == os.environ.get("ADMIN_PASSWORD", "admin123"):
            session["is_admin"] = True
            flash("Logged in as admin", "success")
            nxt = request.args.get("next") or url_for("admin_dashboard")
            return redirect(nxt)
        flash("Invalid password", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out", "info")
    return redirect(url_for("pledge_form"))

@app.route("/export")
@admin_required
def export_excel():
    flat_records = []
    for rec in records:
        flat_records.append({k: ",".join(v) for k, v in rec.items()})

    df = pd.DataFrame(flat_records)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output,
                     download_name="pledge_records.xlsx",
                     as_attachment=True)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    flat_records = []
    for rec in records:
        flat_records.append({k: ",".join(v) for k, v in rec.items()})

    total_bills = len(flat_records)
    total_amount = round(sum(float(r.get("TotalAmounts", "0")) for r in flat_records), 2)
    total_grams = round(sum(float(r.get("TotalGrams", "0")) for r in flat_records), 2)

    repayment_counts = {"Full": 0, "Partial": 0, "Nil": 0}
    for r in flat_records:
        rep = r.get("Repayment", "")
        if rep in repayment_counts:
            repayment_counts[rep] += 1

    return render_template("admin_dashboard.html",
                           records=flat_records,
                           total_bills=total_bills,
                           total_amount=total_amount,
                           total_grams=total_grams,
                           repayment_counts=repayment_counts)


@app.route("/admin/delete/<int:idx>")
@admin_required
def admin_delete(idx):
    if 0 <= idx < len(records):
        records.pop(idx)
        flash("Pledge deleted", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit/<int:idx>", methods=["GET", "POST"])
@admin_required
def admin_edit(idx):
    if 0 <= idx < len(records):
        if request.method == "POST":
            records[idx] = request.form.to_dict(flat=False)
            flash("Pledge updated", "success")
            return redirect(url_for("admin_dashboard"))
        return render_template("form.html", data=records[idx], edit=True)
    flash("Invalid record", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/search")
@admin_required
def admin_search():
    q = request.args.get("q", "").lower()
    flat_records = []
    for i, rec in enumerate(records):
        flat = {k: ",".join(v) for k, v in rec.items()}
        if q in str(flat).lower():
            flat["index"] = i
            flat_records.append(flat)

    return render_template("admin_dashboard.html",
                           records=flat_records,
                           total_bills=len(flat_records),
                           total_amount=sum(float(r.get("TotalAmounts", "0")) for r in flat_records),
                           total_grams=sum(float(r.get("TotalGrams", "0")) for r in flat_records),
                           repayment_counts={"Full": sum(1 for r in flat_records if r.get("Repayment")=="Full"),
                                             "Partial": sum(1 for r in flat_records if r.get("Repayment")=="Partial"),
                                             "Nil": sum(1 for r in flat_records if r.get("Repayment")=="Nil")})


if __name__ == "__main__":
    app.run(debug=True)
