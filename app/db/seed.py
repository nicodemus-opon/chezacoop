from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.db import get_engine
from app.models import Role

DEFAULT_ROLES: tuple[str, ...] = (
    "member",
    "loan officer",
    "admin",
    "super admin",
)


def seed_roles(role_names: Iterable[str] = DEFAULT_ROLES) -> int:
    """Seed missing roles and return the number of created records."""
    created_count = 0
    role_names = tuple(role_names)

    with Session(get_engine()) as session:
        existing_roles = set(
            session.execute(
                select(Role.role_name).where(Role.role_name.in_(role_names))
            ).scalars()
        )

        missing_roles = [Role(role_name=name) for name in role_names if name not in existing_roles]
        if missing_roles:
            session.add_all(missing_roles)
            session.commit()
            created_count = len(missing_roles)
    return created_count
