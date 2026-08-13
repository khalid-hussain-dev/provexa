import unittest

from authkit import AuthKitConfig, hash_password, verify_password


class PasswordTests(unittest.TestCase):
    def test_provexa_compatible_format_and_round_trip(self) -> None:
        password_hash = hash_password("strong-password")
        parts = password_hash.split("$")
        self.assertEqual(parts[0], "pbkdf2_sha256")
        self.assertEqual(parts[1], "260000")
        self.assertTrue(verify_password("strong-password", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_malformed_hashes_fail_closed(self) -> None:
        for value in ["", "not-a-hash", "bcrypt$1$salt$digest", "pbkdf2_sha256$bad$salt$digest"]:
            self.assertFalse(verify_password("password", value))

    def test_custom_config_keeps_stored_iteration_compatibility(self) -> None:
        config = AuthKitConfig(jwt_secret_key="test", password_iterations=1000)
        password_hash = hash_password("password", config)
        default_config = AuthKitConfig(jwt_secret_key="test")
        self.assertTrue(verify_password("password", password_hash, default_config))
