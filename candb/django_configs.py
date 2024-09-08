from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES: dict[str: dict[str: str | dict[str: str]]] = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        "OPTIONS": {
            "service": "candb",
            "passfile": BASE_DIR / "secrets" / ".pgpass",
        },
    }
}


