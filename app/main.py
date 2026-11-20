from fastapi import FastAPI

from .routers import auth

app = FastAPI(title="Library Service", version="1.0.0")

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
