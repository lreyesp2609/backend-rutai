from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    correo: EmailStr
    contrasenia: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    sesion_id: str

class ForgotPasswordRequest(BaseModel):
    correo: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    nueva_contrasenia: str
