"""Initial

Revision ID: eeb501ef3138
Revises: defbd562d3a5
Create Date: 2023-08-17 12:06:44.873733

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'eeb501ef3138'
down_revision = 'defbd562d3a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_auth_token_key', table_name='auth_token')
    op.drop_table('auth_token')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('auth_token',
    sa.Column('key', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='auth_token_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('key', name='auth_token_pkey')
    )
    op.create_index('ix_auth_token_key', 'auth_token', ['key'], unique=False)
    # ### end Alembic commands ###