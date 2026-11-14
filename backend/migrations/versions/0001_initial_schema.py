"""Create the initial Melodia schema.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "tracks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("artist", sa.String(length=180), nullable=False),
        sa.Column("genre", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("listening_url", sa.String(length=1000), nullable=True),
        sa.Column("emotion_scores", sa.JSON(), nullable=False),
        sa.Column("embedding", VECTOR(384), nullable=True),
        sa.Column("embedding_model", sa.String(length=250), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tracks_title", "tracks", ["title"])
    op.create_index("ix_tracks_artist", "tracks", ["artist"])
    op.create_index("ix_tracks_genre", "tracks", ["genre"])
    op.create_table(
        "favorites",
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("track_id", sa.Uuid(as_uuid=True), sa.ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "search_history",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_search_history_user_id", table_name="search_history")
    op.drop_table("search_history")
    op.drop_table("favorites")
    op.drop_index("ix_tracks_genre", table_name="tracks")
    op.drop_index("ix_tracks_artist", table_name="tracks")
    op.drop_index("ix_tracks_title", table_name="tracks")
    op.drop_table("tracks")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
