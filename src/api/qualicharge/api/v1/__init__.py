"""QualiCharge API v1."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def hello():
    """A simple hello world endpoint for early integration testing."""
    return {"message": "Hello world."}
