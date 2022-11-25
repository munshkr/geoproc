from fastapi import FastAPI
import uuid

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/map")
async def map():
    id = uuid.uuid4()
    return {
        "detail": {
            "id": id,
            "tiles_url": "http://localhost:8000/tiles/{id}/{{z}}/{{x}}/{{y}}.png",
        }
    }
