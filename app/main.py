from fastapi import FastAPI

from .routers import auth, books, rentals, users

app = FastAPI(title="Library Service", version="1.0.0")

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(rentals.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok"}
