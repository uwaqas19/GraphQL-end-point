import jwt
import datetime

SECRET_KEY = "your-secret-key"  # 🔐 Replace with a secure, private key in production
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 60  # ⏱ Token expires in 1 hour

# 🔐 Service to generate a JWT token for a user
def generate_jwt_token(username: str, role: str) -> str:
    payload = {
        "sub": username,  # 👤 Subject (user ID)
        "role": role,     # 🧱 User role
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        # ✅ Fixed: use utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
