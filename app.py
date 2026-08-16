import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from io import BytesIO
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from flask_migrate import Migrate


# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET', os.urandom(24))

# Use PostgreSQL in production (Render provides DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///pledges.db'  # fallback for local dev
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# --- Model ---
class Pledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    sex = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    father_or_husband = db.Column(db.String, nullable=False)
    family_details = db.Column(JSON, nullable=False)
    education = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    occupation = db.Column(db.String, nullable=False)
    intro = db.Column(db.String, nullable=False)
    pledge_details = db.Column(db.String, nullable=False)
    pledge_date = db.Column(db.Date, nullable=False)
    pledge_amounts = db.Column(db.Float, nullable=False)
    bill_no = db.Column(db.String, nullable=False, unique=True)  # enforce uniqueness
    repayment = db.Column(db.String, nullable=False)
    repayment_details = db.Column(db.Integer, nullable=True)
    repayment_schedule = db.Column(JSON, nullable=True)
    total_grams_pending = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    alt_number = db.Column(db.String, nullable=True)
    return_jewellary = db.Column(db.String, nullable=True)
    balance_jewellary = db.Column(db.String, nullable=True)
    hc_claim_form_number = db.Column(db.String, nullable=True)
    comments = db.Column(db.String, nullable=True)
    remarks = db.Column(db.String, nullable=True)
    aadhar_number = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helpers ---
def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

# --- Routes ---
@app.route('/', methods=['GET'])
def form():
    return render_template('form_modern.html')

@app.route('/submit', methods=['POST'])
def submit():
    required = [
        'name','sex','age','father_or_husband','family_father','education',
        'address','occupation','intro','pledge_details','pledge_date',
        'pledge_amounts','bill_no','repayment','total_grams_pending','phone_number','aadhar_number'
    ]
    for r in required:
        if not request.form.get(r):
            flash(f"Missing required field: {r}", "danger")
            return redirect(url_for('form'))

    # Duplicate BILL_NO check
    bill_no = request.form.get('bill_no')
    if Pledge.query.filter_by(bill_no=bill_no).first():
        flash(f"Duplicate BILL_NO: {bill_no} already exists", "danger")
        return redirect(url_for('form'))

    family = {
        "father_or_husband": request.form.get('family_father'),
        "kids": [k.strip() for k in request.form.get('family_kids','').split(',') if k.strip()]
    }

    repayment = request.form.get('repayment')
    repayment_details = request.form.get('repayment_details')
    schedule = None
    if repayment in ('Full','Partial') and repayment_details:
        try:
            n = int(repayment_details)
        except Exception:
            n = 0
        schedule = []
        for i in range(1, n+1):
            amt = request.form.get(f'repay_amount_{i}')
            date = request.form.get(f'repay_date_{i}')
            if not amt or not date:
                flash("Missing repayment schedule fields", "danger")
                return redirect(url_for('form'))
            try:
                amt_val = float(amt)
            except Exception:
                flash("Invalid repayment amount", "danger")
                return redirect(url_for('form'))
            schedule.append({"amount": amt_val, "date": date})

    p = Pledge(
        name=request.form.get('name'),
        sex=request.form.get('sex'),
        age=int(request.form.get('age')),
        aadhar_number=request.form.get('aadhar_number'),
        father_or_husband=request.form.get('father_or_husband'),
        family_details=family,
        education=request.form.get('education'),
        address=request.form.get('address'),
        occupation=request.form.get('occupation'),
        intro=request.form.get('intro'),
        pledge_details=request.form.get('pledge_details'),
        pledge_date=parse_date(request.form.get('pledge_date')),
        pledge_amounts=float(request.form.get('pledge_amounts')),
        bill_no=bill_no,
        repayment=repayment,
        repayment_details=int(repayment_details) if repayment_details else None,
        repayment_schedule=schedule,
        total_grams_pending=float(request.form.get('total_grams_pending')),
        phone_number=request.form.get('phone_number'),
        alt_number=request.form.get('alt_number'),
        return_jewellary=request.form.get('return_jewellary'),
        balance_jewellary=request.form.get('balance_jewellary'),
        hc_claim_form_number=request.form.get('hc_claim_form_number'),
        comments=request.form.get('comments'),
        remarks=request.form.get('remarks')
    )
    db.session.add(p)
    db.session.commit()
    flash("Pledge saved successfully", "success")
    return redirect(url_for('form'))

# --- Admin auth ---
def admin_required(fn):
    def wrapper(*args, **kwargs):
        if session.get('is_admin'):
            return fn(*args, **kwargs)
        return redirect(url_for('admin_login', next=request.path))
    wrapper.__name__ = fn.__name__
    return wrapper

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('password','')
        if pw and pw == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['is_admin'] = True
            flash("Logged in as admin", "success")
            nxt = request.args.get('next') or url_for('admin_list')
            return redirect(nxt)
        flash("Invalid password", "danger")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash("Logged out", "info")
    return redirect(url_for('form'))

@app.route('/admin', methods=['GET'])
@admin_required
def admin_list():
    page = int(request.args.get('page', 1))
    per_page = 12
    q = Pledge.query.order_by(Pledge.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_list.html', pagination=pagination)

@app.route('/admin/export', methods=['GET'])
@admin_required
def admin_export():
    pledges = Pledge.query.order_by(Pledge.created_at.desc()).all()
    rows = []
    for pl in pledges:
        rows.append({
            "ID": pl.id,
            "NAME": pl.name,
            "GENDER": pl.sex,
            "AGE": pl.age,
            "AADHAR_NUMBER": pl.aadhar_number,
            "FATHER_OR_HUSBAND": pl.father_or_husband,
            "FAMILY_HUSBAND_OR_WIFE": pl.family_details.get("father_or_husband"),
            "FAMILY_KIDS": ",".join(pl.family_details.get("kids", [])),
            "EDUCATION": pl.education,
            "ADDRESS": pl.address,
            "OCCUPATION": pl.occupation,
            "INTRO": pl.intro,
            "BILL_NO": pl.bill_no,
            "HC_CLAIM_FORM_NUMBER": pl.hc_claim_form_number,
            "PLEDGE_DETAILS": pl.pledge_details,
            "PLEDGE_DATE": pl.pledge_date,
            "PLEDGE_AMOUNTS": pl.pledge_amounts,
            "REPAYMENT": pl.repayment,
            "REPAYMENT_DETAILS": pl.repayment_details,
            "REPAYMENT_SCHEDULE": str(pl.repayment_schedule),
            "TOTAL_GRAMS_PENDING": pl.total_grams_pending,
            "PHONE_NUMBER": pl.phone_number,
            "ALT_NUMBER": pl.alt_number,
            "RETURN_JEWELLARY": pl.return_jewellary,
            "BALANCE_JEWELLARY": pl.balance_jewellary,
            "COMMENTS": pl.comments,
            "REMARKS": pl.remarks,
            "CREATED_AT": pl.created_at
        })
    df = pd.DataFrame(rows)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    filename = f"pledges_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )