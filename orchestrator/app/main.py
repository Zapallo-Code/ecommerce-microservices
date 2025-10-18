from fastapi import FastAPI

app = FastAPI(
    title="Orchestrator Microservice",
    description="This microservice handles orchestration tasks within the system.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}
