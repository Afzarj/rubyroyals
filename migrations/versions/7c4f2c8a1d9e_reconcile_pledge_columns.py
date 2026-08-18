"""Reconcile pledge columns with the current model.

Revision ID: 7c4f2c8a1d9e
Revises: 50b70ec626f4
Create Date: 2026-08-19

"""
from alembic import op
import sqlalchemy as sa


revision = "7c4f2c8a1d9e"
down_revision = "50b70ec626f4"
branch_labels = None
depends_on = None


PLEDGE_COLUMNS = {
    "gender": sa.String(length=20),
    "age": sa.Integer(),
    "father_name": sa.String(length=100),
    "family_name": sa.String(length=100),
    "kids_names": sa.String(length=200),
    "education": sa.String(length=100),
    "occupation": sa.String(length=100),
    "address": sa.String(length=200),
    "phone": sa.String(length=10),
    "alt_number": sa.String(length=10),
    "aadhar": sa.String(length=12),
    "hc_claim_form": sa.String(length=50),
    "intro": sa.String(length=20),
    "num_ornaments": sa.Integer(),
    "ornaments_details": sa.Text(),
    "pledge_date": sa.Date(),
    "total_amount": sa.Float(),
    "total_grams": sa.Float(),
    "return_jewellery": sa.Float(),
    "balance_jewellery": sa.Float(),
    "repayment": sa.String(length=20),
    "repayment_details": sa.Text(),
    "remarks": sa.Text(),
}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("pledge")}

    for name, column_type in PLEDGE_COLUMNS.items():
        if name not in existing_columns:
            op.add_column("pledge", sa.Column(name, column_type, nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("pledge")}

    for name in reversed(list(PLEDGE_COLUMNS)):
        if name in existing_columns:
            op.drop_column("pledge", name)
