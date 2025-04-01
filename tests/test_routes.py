import unittest
from flask import Flask
from routes import app

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_route(self):
        """Test the home route."""
        response = self.app.get('/home')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MOVIE MART', response.data)

    def test_login_route(self):
        """Test a  login route. Adjust based on actual routes."""
        response = self.app.get('/login_user')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User Login', response.data)
        response = self.app.get('/login_staff')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff Login', response.data)

    def test_search_route(self):
        """Test a POST request."""
        response = self.app.post('/search', data={"query": "Jumanji"})  # Adjust endpoint
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search results', response.data)
        self.assertIn(b'Jumanji', response.data)  # Adjust expected response

if __name__ == '__main__':
    unittest.main()
