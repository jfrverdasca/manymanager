"""empty message

Revision ID: 665799af24d8
Revises: aa1af1a3d71d
Create Date: 2022-08-26 23:20:41.681334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '665799af24d8'
down_revision = 'aa1af1a3d71d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alert', sa.Column('timestamp', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('alert', 'timestamp')
    # ### end Alembic commands ###
