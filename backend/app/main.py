from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.addon.routes import router as addon_router

app = FastAPI(title="Cinematheque Categorizer")

# Stremio Web fetches addon routes from the browser, so CORS must allow any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(addon_router)


@app.get("/health")
def health():
    return {"status": "ok"}