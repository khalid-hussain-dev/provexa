# PROVEXA adapter

`authkit.adapters.provexa` is an explicit compatibility layer. It maps the
existing PROVEXA user model and repository to AuthKit's protocols and delegates
session operations to the existing integration session store.

The adapter is never imported by the AuthKit core and does not mount or replace
the existing `/api/v1/auth` routes. Use it only after testing the host-specific
composition in the integration workspace.
