"""Main entrypoint for Voltix TechStore FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, API_PREFIX
from database import engine, Base, get_db
from routers import products, orders, promos, recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception handler for database constraint violations (Requirement 16)
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violation occurred.", "orig": str(exc.orig) if hasattr(exc, "orig") else str(exc)},
    )

# Configure CORS to allow frontend communication from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include resource routers under /api prefix
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(promos.router, prefix=API_PREFIX)
app.include_router(recommend.router, prefix=API_PREFIX)

# Mount local assets for static product images
from fastapi.staticfiles import StaticFiles
from pathlib import Path

TECHSTORE_DIR = Path(__file__).resolve().parent.parent / "techstore"
ASSETS_DIR = TECHSTORE_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.post(
    f"{API_PREFIX}/carts/add",
    status_code=status.HTTP_201_CREATED,
    tags=["Frontend Compatibility"],
    summary="Legacy carts/add compatibility endpoint",
)
def compatibility_cart_add(payload: dict, db: Session = Depends(get_db)):
    """Direct bridge for techstore script.js fetch('/carts/add') POST request."""
    from routers.orders import create_cart_order_compatibility
    return create_cart_order_compatibility(payload, db=db)


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
)
def health_check():
    """Returns operational status of the API server."""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


@app.get(
    "/",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Root landing page",
)
def root():
    """Welcome route directing users and evaluators to interactive Swagger docs."""
    return {
        "message": f"Welcome to {APP_TITLE}!",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "products": f"{API_PREFIX}/products",
            "categories": f"{API_PREFIX}/categories",
            "orders": f"{API_PREFIX}/orders",
            "promotions": f"{API_PREFIX}/promos",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
