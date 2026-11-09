"""Errors whose message was written for the user and is safe to return."""


class UserFacingError(ValueError):
    """An error whose ``detail`` was written for the user and is safe to show."""

    @property
    def detail(self) -> str:
        return str(self.args[0]) if self.args else ""
