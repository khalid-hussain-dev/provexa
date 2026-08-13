# Testing

Run the package tests from `gigs/authkit` after installing the development
extra. Unit tests use fake repositories and session stores. Redis tests may use
a fake Redis client or a dedicated test Redis instance. Do not enable memory
sessions in a production-like process.
