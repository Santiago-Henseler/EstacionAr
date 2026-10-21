from pydantic import BaseModel, EmailStr, Field,field_validator, model_validator
import re

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(...,min_length=8,max_length=128)
    confirm_password: str = Field(...,min_length=8,max_length=128)

    @field_validator("new_password")
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
    
    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("passwords must be equal")
        return self


class ResetPasswordResponse(BaseModel):
    message: str