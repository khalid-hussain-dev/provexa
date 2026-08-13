# Architecture

The core package depends on the standard library and its own contracts only.
Application persistence is provided through `UserRepository`; transient
authentication state is provided through `SessionStore`.

Redis is authoritative for production sessions. The memory implementation is a
deliberately guarded local/test seam. FastAPI and PROVEXA integrations are
optional layers and are not imported by `import authkit`.
