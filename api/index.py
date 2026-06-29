from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

EMAIL = "23f2000085@ds.study.iitm.ac.in"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

WINDOW = 10
LIMIT = 11
clients = {}

@app.middleware("http")
async def middleware(request: Request, call_next):

    req_id = request.headers.get("X-Request-ID")

    if not req_id:
        req_id = str(uuid.uuid4())

    # IMPORTANT: set BEFORE call_next()
    request.state.request_id = req_id

    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client not in clients:
        clients[client] = []

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = req_id

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
