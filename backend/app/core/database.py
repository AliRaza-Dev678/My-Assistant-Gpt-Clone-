from app.core.config import Settings, get_settings


MODEL_MODULES = ["app.models.entities", "aerich.models"]


def build_tortoise_config(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return {
        "connections": {"default": settings.database_url},
        "apps": {
            "models": {
                "models": MODEL_MODULES,
                "default_connection": "default",
            }
        },
        "use_tz": True,
        "timezone": "UTC",
    }


# Aerich imports this variable using app.core.database.TORTOISE_ORM.
TORTOISE_ORM = build_tortoise_config()
