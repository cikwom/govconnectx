import unittest

import jwt

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


class PasswordSecurityTests(unittest.TestCase):
    def test_password_hash_is_not_plain_text_and_verifies(self):
        password = "Correct-Horse-Battery-42"
        encoded = hash_password(password)
        self.assertNotEqual(encoded, password)
        self.assertTrue(verify_password(password, encoded))

    def test_password_hash_uses_a_unique_salt(self):
        password = "Correct-Horse-Battery-42"
        self.assertNotEqual(hash_password(password), hash_password(password))

    def test_wrong_password_is_rejected(self):
        encoded = hash_password("Correct-Horse-Battery-42")
        self.assertFalse(verify_password("incorrect-password", encoded))

    def test_malformed_hash_is_rejected(self):
        self.assertFalse(verify_password("anything", "not-a-valid-hash"))

    def test_hash_with_excessive_work_factor_is_rejected_without_deriving(self):
        salt = "00" * 16
        digest = "00" * 32
        encoded = "pbkdf2_sha256$999999999999999999999$" + salt + "$" + digest
        self.assertFalse(verify_password("anything", encoded))

    def test_hash_with_too_few_iterations_is_rejected(self):
        salt = "00" * 16
        digest = "00" * 32
        encoded = "pbkdf2_sha256$1$" + salt + "$" + digest
        self.assertFalse(verify_password("anything", encoded))

    def test_hash_with_invalid_salt_or_digest_length_is_rejected(self):
        self.assertFalse(verify_password("anything", "pbkdf2_sha256$600000$00$" + "00" * 32))
        self.assertFalse(verify_password("anything", "pbkdf2_sha256$600000$" + "00" * 16 + "$00"))

    def test_non_string_hash_input_is_rejected(self):
        self.assertFalse(verify_password("anything", None))
        self.assertFalse(verify_password(None, hash_password("anything")))


class TokenSecurityTests(unittest.TestCase):
    def test_access_token_contains_expected_claims(self):
        token = create_access_token(42, "citizen")
        claims = decode_access_token(token)
        self.assertEqual(claims["sub"], "42")
        self.assertEqual(claims["role"], "citizen")
        self.assertEqual(claims["type"], "access")

    def test_invalid_token_is_rejected(self):
        with self.assertRaises(jwt.InvalidTokenError):
            decode_access_token("not.a.valid.token")


if __name__ == "__main__":
    unittest.main()
