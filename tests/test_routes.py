import unittest
from flask import Flask
from routes import app

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True

    def test_welcome_route(self):
        """Test the welcome route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Unlimited movies', response.data)
        response = self.app.get('/welcome')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Unlimited movies', response.data)

    def test_home_route(self):
        """Test the home route."""
        response = self.app.get('/home')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MOVIE MART', response.data)
    
    def test_cart_route(self):
        """Test the cart route."""
        response = self.app.get('/cart')
        self.assertNotIn(b'My Cart', response.data)
    
    def test_staff_route(self):
        """Test the staff route."""
        response = self.app.get('/staff')
        self.assertNotIn(b'Staff Dashboard', response.data)
    
    def test_manager_route(self):
        """Test the manager route."""
        response = self.app.get('/manager')
        self.assertNotIn(b'Manager Dashboard', response.data)
    
    def test_myrentals_route(self):
        """Test the myrentals route."""
        response = self.app.get('/myrentals')
        self.assertNotIn(b'My Rentals', response.data)
    
    def test_view_movie_route(self):
        """Test the view_movie route."""
        response = self.app.get('view_movie/Jumanji')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jumanji', response.data)

    def test_auth_route(self):
        """Test a auth routes."""
        response = self.app.get('/login_user')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User Login', response.data)
        response = self.app.get('/login_staff')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff Login', response.data)
        response = self.app.get('/login_manager')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manager Login', response.data)
        response = self.app.get('/join')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Join MovieMart', response.data)

    def test_search_route(self):
        """Test a POST request."""
        response = self.app.post('/search', data={"query": "Jumanji"})  # Adjust endpoint
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search results', response.data)
        self.assertIn(b'Jumanji', response.data)  # Adjust expected response
    
if __name__ == '__main__':
    unittest.main()
