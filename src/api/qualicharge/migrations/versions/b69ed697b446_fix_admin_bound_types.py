"""fix_admin_bound_types

Revision ID: b69ed697b446
Revises: 161e8a262e0a
Create Date: 2024-10-08 16:04:02.172208

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b69ed697b446"
down_revision: Union[str, None] = "161e8a262e0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "city",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "city",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "city",
        "id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="id::uuid",
        nullable=False,
    )
    op.alter_column(
        "city",
        "name",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "city",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=False,
    )
    op.alter_column(
        "city",
        "population",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "area",
        existing_type=sa.TEXT(),
        type_=sa.Float(),
        postgresql_using="area::float",
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "code",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "city",
        "department_id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="department_id::uuid",
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "epci_id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="epci_id::uuid",
        existing_nullable=True,
    )
    op.create_index(op.f("ix_city_code"), "city", ["code"], unique=True)
    op.alter_column(
        "department",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "department",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "department",
        "id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="id::uuid",
        nullable=False,
    )
    op.alter_column(
        "department",
        "name",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "department",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=False,
    )
    op.alter_column(
        "department",
        "population",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "department",
        "area",
        existing_type=sa.TEXT(),
        type_=sa.Float(),
        postgresql_using="area::float",
        existing_nullable=True,
    )
    op.alter_column(
        "department",
        "code",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "department",
        "region_id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="region_id::uuid",
        existing_nullable=True,
    )
    op.create_index(op.f("ix_department_code"), "department", ["code"], unique=True)
    op.alter_column(
        "epci",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "epci",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "epci",
        "id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="id::uuid",
        nullable=False,
    )
    op.alter_column(
        "epci",
        "name",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "epci",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=False,
    )
    op.alter_column(
        "epci",
        "population",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "epci",
        "code",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.create_index(op.f("ix_epci_code"), "epci", ["code"], unique=True)
    op.alter_column(
        "region",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "region",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "region",
        "id",
        existing_type=sa.TEXT(),
        type_=sa.Uuid(),
        postgresql_using="id::uuid",
        nullable=False,
    )
    op.alter_column(
        "region",
        "name",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.alter_column(
        "region",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=False,
    )
    op.alter_column(
        "region",
        "population",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "region",
        "area",
        existing_type=sa.TEXT(),
        type_=sa.Float(),
        postgresql_using="area::float",
        existing_nullable=True,
    )
    op.alter_column(
        "region",
        "code",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.create_index(op.f("ix_region_code"), "region", ["code"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_region_code"), table_name="region")
    op.alter_column(
        "region",
        "code",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "region",
        "area",
        existing_type=sa.Float(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "region",
        "population",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        existing_nullable=True,
    )
    op.alter_column(
        "region",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=True,
    )
    op.alter_column(
        "region",
        "name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "region", "id", existing_type=sa.Uuid(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "region",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "region",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.drop_index(op.f("ix_epci_code"), table_name="epci")
    op.alter_column(
        "epci",
        "code",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "epci",
        "population",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        existing_nullable=True,
    )
    op.alter_column(
        "epci",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=True,
    )
    op.alter_column(
        "epci",
        "name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "epci", "id", existing_type=sa.Uuid(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "epci",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "epci",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.drop_constraint(None, "department", type_="foreignkey")
    op.drop_index(op.f("ix_department_code"), table_name="department")
    op.alter_column(
        "department",
        "region_id",
        existing_type=sa.Uuid(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "department",
        "code",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "department",
        "area",
        existing_type=sa.Float(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "department",
        "population",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        existing_nullable=True,
    )
    op.alter_column(
        "department",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=True,
    )
    op.alter_column(
        "department",
        "name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "department", "id", existing_type=sa.Uuid(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "department",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "department",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.drop_constraint(None, "city", type_="foreignkey")
    op.drop_constraint(None, "city", type_="foreignkey")
    op.drop_index(op.f("ix_city_code"), table_name="city")
    op.alter_column(
        "city",
        "epci_id",
        existing_type=sa.Uuid(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "department_id",
        existing_type=sa.Uuid(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "code",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "city",
        "area",
        existing_type=sa.Float(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "population",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        existing_nullable=True,
    )
    op.alter_column(
        "city",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        nullable=True,
    )
    op.alter_column(
        "city",
        "name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "city", "id", existing_type=sa.Uuid(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "city",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "city",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # ### end Alembic commands ###
