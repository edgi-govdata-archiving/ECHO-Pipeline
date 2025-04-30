from fastapi import Depends, HTTPException
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def validate_github_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    headers = {'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'}
    
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            url='https://api.github.com/user',
            headers=headers
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid GitHub token",
            )
        return True
