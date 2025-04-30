from dotenv import load_dotenv
load_dotenv()  # Load all variables from .env into os.environ

from fastapi import FastAPI, Depends
from app.routes import echo_router  # Make sure the path is correct
from app.db.session import init_db
from app.auth.github import validate_github_token
from app.services.RateLimiter import RateLimiter
from app.auth import github_oauth


app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

    
@app.get("/", dependencies=[
    Depends(validate_github_token),
    Depends(RateLimiter(requests_limit=1, time_window=5))
    ])
def read_root():
    return {"msg": "You now have access to the API!"}

app.include_router(github_oauth.router)
app.include_router(echo_router, prefix="/echo", tags=["echo"])