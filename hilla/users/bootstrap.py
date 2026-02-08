import os
import sys


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin12345"
DEFAULT_ADMIN_EMAIL = "admin@example.com"


def _should_run() -> bool:
    # Always attempt on app startup unless running during blocked commands.
    blocked_cmds = {"collectstatic", "makemigrations", "migrate", "test"}
    argv = {arg.lower() for arg in sys.argv}
    if argv & blocked_cmds:
        return False

    return True


def ensure_default_admin() -> None:
    if not _should_run():
        return

    username = DEFAULT_ADMIN_USERNAME
    password = DEFAULT_ADMIN_PASSWORD
    email = DEFAULT_ADMIN_EMAIL

    try:
        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError, ProgrammingError
    except Exception:
        return

    try:
        User = get_user_model()
        existing = User.objects.filter(username=username).first()
        if existing:
            changed = False
            if not existing.is_staff:
                existing.is_staff = True
                changed = True
            if not existing.is_superuser:
                existing.is_superuser = True
                changed = True
            if email and not existing.email:
                existing.email = email
                changed = True
            # For demo: always force the known password.
            existing.set_password(password)
            changed = True
            if changed:
                existing.save(update_fields=["is_staff", "is_superuser", "email", "password"])
            return

        User.objects.create_superuser(
            username=username,
            email=email or "",
            password=password,
        )
    except (OperationalError, ProgrammingError):
        return
