import unittest
from unittest.mock import patch, MagicMock, call
from datetime import timedelta
import datetime
from models import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, Movie, Rent
from functions import rentmovie, return_movie, search_movies, add_movie, generate_receipt, send_mail



class TestFunctions(unittest.TestCase):

    def setUp(self):
        """Set up mock data before each test."""
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.init_app(self.app)

        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()  # Create all tables

        # Create and commit user and movie first
        self.user = User(name="testuser", email="test@example.com", password="pass", balance=1000)
        self.movie = Movie(title="Inception", genre="Sci-Fi", stock=5, price=100)
        self.rented_movie = Movie(title="Inception2", genre="Sci-Fi", stock=5 , price=100)
        db.session.add(self.user)
        db.session.add(self.movie)
        db.session.add(self.rented_movie)
        db.session.commit()

        self.rent = Rent(
            user_id=self.user.id,
            movie_id=self.rented_movie.id,
            rented_date=datetime.datetime.now(datetime.UTC),
            deadline=datetime.datetime.now(datetime.UTC) + timedelta(days=7)
        )
        db.session.add(self.rent)
        db.session.commit()


    def tearDown(self):
        """Clean up after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Fixed tests
    @patch("functions.flash")
    @patch("functions.db.session.commit")
    @patch("functions.db.session.add")
    @patch("functions.Movie.query.get")
    @patch("functions.User.query.get")
    @patch("functions.Rent.query.filter_by")
    def test_rent_movie(self, mock_rent_filter_by, mock_user_get, mock_movie_get, mock_add, mock_commit, mock_flash):
        """Test renting a movie successfully."""
        # Configure mocks
        mock_user_get.return_value = self.user
        mock_movie_get.return_value = self.movie
        mock_rent_filter_by.return_value.first.return_value = None  # No existing rental

        result = rentmovie(self.user.id, self.movie.id)

        # Verify results
        self.assertIsNotNone(result)
        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        self.assertEqual(self.movie.stock, 4)
    
    @patch("functions.flash")
    @patch("functions.db.session.commit")
    @patch("functions.Movie.query.get")
    @patch("functions.User.query.get")
    @patch("functions.Rent.query.filter_by")
    def test_rent_movie_insufficient_stock(self, mock_rent_filter_by, mock_user_get, mock_movie_get, mock_commit, mock_flash):
        """Test renting with no stock available."""
        # Configure mocks
        mock_user_get.return_value = self.user
        mock_movie_get.return_value = self.movie
        self.movie.stock = 0
        mock_rent_filter_by.return_value.first.return_value = None

        result = rentmovie(self.user.id, self.movie.id)

        # Verify results
        self.assertIsNone(result)
        mock_commit.assert_not_called()
        
    @patch("functions.flash")
    @patch("functions.db.session.commit")
    @patch("functions.Movie.query.get")
    @patch("functions.User.query.get")
    @patch("functions.Rent.query.filter_by")
    def test_rent_movie_insufficient_balance(self, mock_rent_filter_by, mock_user_get, mock_movie_get, mock_commit, mock_flash):
        """Test renting with no stock available."""
        # Configure mocks
        mock_user_get.return_value = self.user
        mock_movie_get.return_value = self.movie
        self.user.balance = 0
        mock_rent_filter_by.return_value.first.return_value = None

        result = rentmovie(self.user.id, self.movie.id)

        # Verify results
        self.assertIsNone(result)
        mock_commit.assert_not_called()
        
    @patch("functions.flash")
    @patch("functions.db.session.commit")
    @patch("functions.db.session.delete")
    @patch("functions.Rent.query")
    def test_return_movie(self, mock_rent_query, mock_delete, mock_commit, mock_flash):
        """Test returning a rented movie."""
        # Configure rent query mock
        mock_filter = MagicMock()
        mock_filter.first.return_value = self.rent
        mock_rent_query.filter_by.return_value = mock_filter

        result = return_movie(self.rent.id)

        # Verify results
        self.assertTrue(result)
        self.assertEqual(self.rented_movie.stock, 6)
        mock_commit.assert_called()

    @patch("functions.flash")
    @patch("functions.Movie.query")
    def test_search_movies(self, mock_movie_query, flash):
        """Test movie search functionality."""
        # Configure filter mock
        mock_filter = MagicMock()
        mock_filter.all.return_value = [self.movie, self.rented_movie]
        mock_movie_query.filter.return_value = mock_filter

        results = search_movies("Inception")
        
        # Verify results
        self.assertIsNotNone(results)
        mock_movie_query.filter.assert_called()

    @patch("functions.flash")
    @patch("functions.db.session.commit")
    @patch("functions.db.session.add")
    @patch("functions.Movie.query.filter_by")
    def test_add_movie(self, mock_filter_by, mock_add, mock_commit, mock_flash):
        """Test adding a new movie."""
        # Configure filter mock
        mock_filter_by.return_value.first.return_value = None

        result = add_movie("Interstellar", 3, "Sci-Fi")
        
        # Verify results
        self.assertTrue(result)
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

    @patch("functions.flash")
    @patch("functions.User.query.get")
    @patch("functions.Movie.query.get")
    @patch("functions.Rent.query.get")
    def test_generate_receipt(self, mock_rent_get, mock_movie_get, mock_user_get, mock_flash):
        """Test receipt generation."""
        # Configure mocks
        mock_rent_get.return_value = self.rent
        mock_movie_get.return_value = self.movie
        mock_user_get.return_value = self.user

        pdf_path = generate_receipt(self.rent.id)
        
        # Verify results
        self.assertTrue(pdf_path.endswith(".pdf"))

    @patch("functions.flash")
    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp, mock_flash):
        """Test email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = send_mail("test@example.com", "Subject", "Body")
        
        self.assertTrue(result)
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

        sent_msg = mock_server.send_message.call_args[0][0]
        self.assertEqual(sent_msg['To'], "test@example.com")
        self.assertEqual(sent_msg['Subject'], "Subject")
        self.assertIn("Body", sent_msg.as_string())

if __name__ == "__main__":
    unittest.main()
