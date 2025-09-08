from alembic import op
import sqlalchemy as sa


revision = "0001_uq_title_per_author"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
   
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("biography", sa.String, nullable=True),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("genre", sa.String, nullable=False),
        sa.Column("published_year", sa.Integer, nullable=False),

        sa.Column("isbn", sa.String(length=20), nullable=True, unique=True, index=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.Column("author_id", sa.Integer, sa.ForeignKey("authors.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_index(op.f("ix_books_created_at"), "books", ["created_at"])
    op.create_index(op.f("ix_books_updated_at"), "books", ["updated_at"])

    op.execute("CREATE UNIQUE INDEX uq_books_author_title_ci ON books (LOWER(title), author_id)")

def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_books_author_title_ci")
    op.drop_index(op.f("ix_books_updated_at"), table_name="books")
    op.drop_index(op.f("ix_books_created_at"), table_name="books")
    op.drop_table("books")
    op.drop_table("authors")
