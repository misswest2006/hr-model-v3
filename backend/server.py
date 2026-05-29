import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)

from run_model import run

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "HR model backend running"}

@app.get("/api/slate")
def get_slate():
    picks = run()
    return {
        "count": len(picks),
        "picks": picks
    }