from fastapi import HTTPException, status

class ECDATException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class ResourceNotFoundException(ECDATException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            detail=f"{resource} with ID '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ValidationException(ECDATException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

class AuthenticationException(ECDATException):
    def __init__(self, detail: str = "Invalid credentials or token"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)

class AuthorizationException(ECDATException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)
