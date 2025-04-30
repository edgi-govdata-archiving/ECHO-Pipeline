from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os
from dotenv import load_dotenv

router = APIRouter()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@router.get('/github-auth')
def github_login():
    return RedirectResponse(
        f'https://github.com/login/oauth/authorize?scope=user:email&client_id={GITHUB_CLIENT_ID}',
        status_code=302
    )

@router.get('/github-code')
async def create_token(code: str):
    params = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code
    }

    headers = {'Accept': 'application/json'}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url='https://github.com/login/oauth/access_token',
            params=params,
            headers=headers
        )

        response_json = response.json()
        access_token = response_json.get('access_token')

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        headers.update({
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github+json'
        })

        user_response = await client.get('https://api.github.com/user/emails', headers=headers)

        if user_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")

        user_email_response = user_response.json()
        email = user_email_response[0]['email'] if user_email_response else None

        if not email:
            raise HTTPException(status_code=400, detail="Failed to get user email")

        return {"access_token": access_token, "email": email}
