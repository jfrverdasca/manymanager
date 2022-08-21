"""empty message

Revision ID: f42719617e8b
Revises: a2a4de209eda
Create Date: 2022-08-19 12:06:01.623540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f42719617e8b'
down_revision = 'a2a4de209eda'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('share', sa.Column('left_id', sa.BigInteger(), nullable=False))
    op.add_column('share', sa.Column('right_id', sa.BigInteger(), nullable=False))
    op.drop_constraint('share_shared_user_id_fkey', 'share', type_='foreignkey')
    op.drop_constraint('share_user_id_fkey', 'share', type_='foreignkey')
    op.create_foreign_key(None, 'share', 'user', ['right_id'], ['id'])
    op.create_foreign_key(None, 'share', 'user', ['left_id'], ['id'])
    op.drop_column('share', 'shared_user_id')
    op.drop_column('share', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('share', sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=False))
    op.add_column('share', sa.Column('shared_user_id', sa.BIGINT(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'share', type_='foreignkey')
    op.drop_constraint(None, 'share', type_='foreignkey')
    op.create_foreign_key('share_user_id_fkey', 'share', 'user', ['user_id'], ['id'])
    op.create_foreign_key('share_shared_user_id_fkey', 'share', 'user', ['shared_user_id'], ['id'])
    op.drop_column('share', 'right_id')
    op.drop_column('share', 'left_id')
    # ### end Alembic commands ###