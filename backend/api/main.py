from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routers import chat, calculator, outlets, products

def create_app() -> FastAPI:
    app = FastAPI(title="Mindhive Assessment API", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(calculator.router, prefix="/api/v1", tags=["calculator"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(products.router, prefix="/api/v1", tags=["products"])
    app.include_router(outlets.router, prefix="/api/v1", tags=["outlets"])

    return app

app = create_app()