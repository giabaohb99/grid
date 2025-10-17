from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.exceptions import RequestValidationError

from core.core.config import settings
from core.core.database import engine, Base
from core.core.exceptions import APIError
from core.core.exception_handlers import (
    api_error_handler,
    request_validation_error_handler,
    generic_error_handler
)

# Import models
from grid_management.models import *

# Import routers
from grid_management.router import router as grid_router

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    exception_handlers={
        APIError: api_error_handler,
        RequestValidationError: request_validation_error_handler,
        Exception: generic_error_handler,
    }
)

# Add HTTPS Redirect Middleware if enabled
if settings.ENABLE_SSL:
    app.add_middleware(HTTPSRedirectMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(grid_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to Grid Management API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 