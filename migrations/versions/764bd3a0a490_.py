"""empty message

Revision ID: 764bd3a0a490
Revises: eb7481bc48c7
Create Date: 2022-08-19 11:11:24.255527

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '764bd3a0a490'
down_revision = 'eb7481bc48c7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('share', sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False))
    op.add_column('share', sa.Column('user_id', sa.BigInteger(), nullable=True))
    op.drop_constraint('share_right_user_id_fkey', 'share', type_='foreignkey')
    op.drop_constraint('share_left_user_id_fkey', 'share', type_='foreignkey')
    op.create_foreign_key(None, 'share', 'user', ['user_id'], ['id'])
    op.drop_column('share', 'left_user_id')
    op.drop_column('share', 'right_user_id')
    op.drop_column('share', 'active')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('share', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('share', sa.Column('right_user_id', sa.BIGINT(), autoincrement=False, nullable=False))
    op.add_column('share', sa.Column('left_user_id', sa.BIGINT(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'share', type_='foreignkey')
    op.create_foreign_key('share_left_user_id_fkey', 'share', 'user', ['left_user_id'], ['id'])
    op.create_foreign_key('share_right_user_id_fkey', 'share', 'user', ['right_user_id'], ['id'])
    op.drop_column('share', 'user_id')
    op.drop_column('share', 'id')
    # ### end Alembic commands ###
