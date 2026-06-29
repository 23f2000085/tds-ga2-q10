from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
import uuid
import time

EMAIL = "23f2000085@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-ziiy19.example.com",
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 11
WINDOW = 10

app = FastAPI()

# ---------------- CORS ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ---------------- Request Context ----------------

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestContextMiddleware)

# ---------------- Rate Limiter ----------------

buckets = defaultdict(deque)

class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        client = request.headers.get("X-Client-Id", "__anonymous__")

        now = time.time()

        q = buckets[client]

        while q and q[0] <= now - WINDOW:
            q.popleft()

        if len(q) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"}
            )

            response.headers["X-Request-ID"] = request.state.request_id

            return response

        q.append(now)

        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

# ---------------- OPTIONS ----------------

@app.options("/ping")
async def options_ping():
    return {}

# ---------------- Routes ----------------

@app.get("/")
def root():
    return {
        "status": "ok"
    }

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
