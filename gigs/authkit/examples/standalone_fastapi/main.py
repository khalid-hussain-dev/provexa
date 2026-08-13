from fastapi import FastAPI

from authkit import AuthService, InMemorySessionStore
from authkit.fastapi import create_auth_router, register_authkit_error_handler

from repository import ExampleUserRepository
from settings import example_config

config = example_config()
repository = ExampleUserRepository()
session_store = InMemorySessionStore(config)

app = FastAPI(title="AuthKit standalone example")
register_authkit_error_handler(app)
app.include_router(
    create_auth_router(
        repository_provider=lambda request: repository,
        config_provider=lambda request: config,
        session_store_provider=lambda request: session_store,
        service_provider=lambda request: AuthService(repository, config),
        prefix="/auth",
    )
)
