from fastapi import APIRouter, Depends

from app.api.dependencies import get_request_identity
from app.models.schemas import IdentityRead
from app.services.identity import RequestIdentity


router = APIRouter(prefix="/identity", tags=["identity"])


@router.get("", response_model=IdentityRead)
async def read_identity(
    identity: RequestIdentity = Depends(get_request_identity),
):
    return identity.public_dict()
