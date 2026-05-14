"""
Exceptions personnalisées.
"""
from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Exception pour ressource non trouvée."""
    def __init__(self, detail: str = "Ressource non trouvée"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    """Exception pour requête invalide."""
    def __init__(self, detail: str = "Requête invalide"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(HTTPException):
    """Exception pour non authentifié."""
    def __init__(self, detail: str = "Non authentifié"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    """Exception pour accès interdit."""
    def __init__(self, detail: str = "Accès interdit"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(HTTPException):
    """Exception pour conflit."""
    def __init__(self, detail: str = "Conflit avec une ressource existante"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)