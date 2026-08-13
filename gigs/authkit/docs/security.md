# Security

Use a high-entropy secret managed by the deployment environment. Use Redis in
production and keep the Redis namespace dedicated to the application. Password
reset tokens are stored as keyed hashes and should be delivered through a
separate email mechanism; direct response exposure is for local/test flows only.

OAuth and account recovery delivery are future extensions.
