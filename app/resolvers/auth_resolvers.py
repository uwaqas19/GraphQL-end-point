from app.services.auth_service import generate_jwt_token

# ✅ Handles login query to return JWT token
class AuthQuery:

    @staticmethod
    def resolve_login(_, info, username: str, role: str) -> str:
        """
        Resolves login mutation/query.
        Generates JWT token with provided username and role.
        """
        return generate_jwt_token(username, role)
