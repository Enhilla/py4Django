from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from .bootstrap import ensure_default_admin
        from . import signals  # noqa: F401

        ensure_default_admin()
