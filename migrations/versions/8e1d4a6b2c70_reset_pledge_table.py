"""Reset pledge table to the current model schema.

This migration intentionally deletes all existing pledge records.

Revision ID: 8e1d4a6b2c70
Revises: 7c4f2c8a1d9e
Create Date: 2026-08-19

"""
from alembic import op
import sqlalchemy as sa


revision = "8e1d4a6b2c70"
down_revision = "7c4f2c8a1d9e"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "pledge" in inspector.get_table_names():
        op.drop_table("pledge")

    op.create_table(
        "pledge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_no", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("father_name", sa.String(length=100), nullable=True),
        sa.Column("family_name", sa.String(length=100), nullable=True),
        sa.Column("kids_names", sa.String(length=200), nullable=True),
        sa.Column("education", sa.String(length=100), nullable=True),
        sa.Column("occupation", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=10), nullable=False),
        sa.Column("alt_number", sa.String(length=10), nullable=True),
        sa.Column("aadhar", sa.String(length=12), nullable=False),
        sa.Column("hc_claim_form", sa.String(length=50), nullable=True),
        sa.Column("intro", sa.String(length=20), nullable=True),
        sa.Column("num_ornaments", sa.Integer(), nullable=True),
        sa.Column("ornaments_details", sa.Text(), nullable=True),
        sa.Column("pledge_date", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("total_grams", sa.Float(), nullable=True),
        sa.Column("return_jewellery", sa.Float(), nullable=True),
        sa.Column("balance_jewellery", sa.Float(), nullable=True),
        sa.Column("repayment", sa.String(length=20), nullable=True),
        sa.Column("repayment_details", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bill_no"),
    )


def downgrade():
    op.drop_table("pledge")
