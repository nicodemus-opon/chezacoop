# Chezacoop (Prototype)

Brief instructions to run the app locally.

## 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Configure environment

Create a `.env` file in the project root with at least:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/chezacoop
JWT_SECRET=change-me
BULKSMS_API_KEY=api_key
```

Optional (for SMS):

```env
BULKSMS_API_KEY=your_api_key
```

## 4) Run database migrations

```bash
alembic upgrade head
```

## 5) Start the API

```bash
uvicorn main:app --reload
```

The API will be available at:
- http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## Notes

- The root endpoint `/` is protected and requires authentication.
- On startup, default roles are seeded automatically.
