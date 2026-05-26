import logging

from fastapi import Depends, FastAPI

from app.auth import get_current_user, router as auth_router
from app.db.seed import seed_roles
from app.models import User

app = FastAPI()
logger = logging.getLogger(__name__)
app.include_router(auth_router)


@app.on_event("startup")
def seed_default_roles() -> None:
    try:
        created = seed_roles()
        logger.info("Seeded %s roles", created)
    except Exception as exc:
        logger.warning("Skipping role seeding: %s", exc)
    


@app.get("/")
def read_root(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome {current_user.name}"}
