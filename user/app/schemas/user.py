from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

class UserCreate(BaseModel):
    name: str = Field(...,min_length=4,max_length=100)
    email:EmailStr
    password: str = Field(...,min_length=8,max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("password must contain at least one number")
        if not re.search(r'[@$!%*?&._\-#]', value):
            raise ValueError("password must contain at least one special character")
        return value
    
class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=4, max_length=100)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
