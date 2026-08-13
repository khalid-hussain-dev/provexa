# FastAPI integration

Install the optional FastAPI extra and use `create_auth_router` with injected
repository, configuration, and session-store providers. Register
`register_authkit_error_handler` on the application to produce AuthKit's
structured error envelope.

The example uses memory sessions for demonstration only. Production deployments
must inject `RedisSessionStore`.
