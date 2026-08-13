from authkit import AuthKitConfig


def example_config() -> AuthKitConfig:
    return AuthKitConfig(
        jwt_secret_key="replace-this-local-example-secret",
        environment="development",
        allow_in_memory_sessions=True,
        expose_password_reset_token=True,
        two_factor_issuer="AuthKit",
    )
