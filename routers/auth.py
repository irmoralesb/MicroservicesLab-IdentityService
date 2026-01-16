from fastapi import APIRouter, status

router = APIRouter(
    prefix='/api/v1/auth',
    tags=["auth"]
)

@router.get("",status_code=status.HTTP_200_OK)
async def get_user():
    return {"user": "authenticated"}