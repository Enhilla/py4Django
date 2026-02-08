from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from .bootstrap import ensure_default_admin

        ensure_default_admin()
