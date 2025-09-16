from fastapi import HTTPException, status, Depends, Request 

from src.database.models import Role, User
from src.services.auth import get_current_user

class RoleAccess:
  def __init__(self, allowed_roles: list[Role]):
    self.allowed_roles = allowed_roles

  async def __call__(self, request: Request, user: User = Depends(get_current_user)) -> None:
    if user.role not in self.allowed_roles:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not allowed. Please contact the admin.")