"""Main application module.

This module sets up the FastAPI application with middleware, error handlers,
and API route registration. It serves as the entry point for the contacts
management application.

The module configures:
- FastAPI application instance
- CORS middleware for cross-origin requests
- Rate limiting middleware and error handling
- API route registration for contacts, auth, and users
- Development server configuration
"""

import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api import contacts, auth, users
from src.middlewares.limiter import limiter


app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions.

    Args:
        request (Request): The HTTP request that triggered the rate limit
        exc (RateLimitExceeded): The rate limit exception

    Returns:
        JSONResponse: 429 status with error message
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Request limit exceeded. Try again later"},
    )


origins = ["http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
