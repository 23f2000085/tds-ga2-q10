from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uuid
import time

EMAIL = "23f2000085@ds.study.iitm.ac.in"

app = FastAPI()

# ONLY these two origins are allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-ziiy19.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Handle browser preflight
@app.options("/ping")
async def options_ping():
    return Response(status_code=200)

# Rate limit configuration
WINDOW = 10
LIMIT = 11
clients = {}

@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limiting
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    if client_id not in clients:
        clients[client_id] = []

    # Remove expired timestamps
    clients[client_id] = [
        t for t in clients[client_id]
        if now - t < WINDOW
    ]

    if len(clients[client_id]) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
        response.headers["X-Request-ID"] = request_id
        return response

    clients[client_id].append(now)

    response = await call_next(request)

    # Always return request id header
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
