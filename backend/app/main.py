from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.addon.routes import router as addon_router
from app.api.routes import router as api_router

app = FastAPI(title="Cinematheque Categorizer")

# Stremio Web and the management UI call this API from the browser.
# Allowing any origin is safe here: access is controlled by tokens in the
# URL (addon) or the Authorization header (API), not by cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(addon_router)
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": "Cinematheque Categorizer API",
        "description": "Stremio addon serving personal film collections.",
        "status": "work in progress",
        "source": "https://github.com/leanardiles/cinematheque-categorizer",
    }


@app.get("/health")
def health():
    return {"status": "ok"}