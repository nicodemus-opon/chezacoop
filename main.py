import logging

from fastapi import FastAPI

from app.db.seed import seed_roles

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
def seed_default_roles() -> None:
    try:
        created = seed_roles()
        logger.info("Seeded %s roles", created)
    except Exception as exc:
        logger.warning("Skipping role seeding: %s", exc)
    


@app.get("/")
def read_root():
    return {"Hello": "World"}
