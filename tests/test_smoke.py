import unittest

from app import app


class ChittyScoreSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("status"), "healthy")
        self.assertEqual(payload.get("service"), "chittyscore")


if __name__ == "__main__":
    unittest.main()
