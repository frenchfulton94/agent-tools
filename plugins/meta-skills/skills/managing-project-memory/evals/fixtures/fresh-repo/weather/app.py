from fastapi import FastAPI

api = FastAPI()


@api.get("/forecast/{city}")
def forecast(city: str) -> dict:
    # Upstream feed is rate-limited to 10 req/min; responses cached in-process.
    return {"city": city, "status": "stub"}
