import unittest

from authkit import AuthKitConfig, create_access_token, decode_access_token, hash_password, verify_password


class ContractTests(unittest.TestCase):
    def test_password_contract(self):
        value = hash_password("contract-password")
        self.assertTrue(value.startswith("pbkdf2_sha256$260000$"))
        self.assertTrue(verify_password("contract-password", value))

    def test_jwt_contract(self):
        config = AuthKitConfig(jwt_secret_key="contract-secret", environment="test")
        payload = decode_access_token(create_access_token("user-id", config), config)
        self.assertEqual(set(("sub", "jti", "iat", "exp")), set(payload))
