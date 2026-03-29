class AuthSessionNotFoundError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    def __init__(self) -> None:
        super().__init__("이메일 또는 비밀번호가 올바르지 않습니다.")


class UserAlreadyExistsError(ValueError):
    def __init__(self, email: str) -> None:
        super().__init__(f"이미 사용 중인 이메일입니다: {email}")
        self.email = email


class AuthenticationRequiredError(ValueError):
    def __init__(self) -> None:
        super().__init__("로그인이 필요합니다.")
