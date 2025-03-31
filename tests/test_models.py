import unittest
from datetime import datetime, UTC
from flask import Flask
from models import db, User, Staff, Movie, Rent

class ModelsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary test database."""
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        db.init_app(self.app)
        
        with self.app.app_context():
            db.create_all()
        
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up the test database."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_user(self):
        """Test creating a User model instance."""
        with self.app.app_context():
            user = User(name="JohnDoe", email="johndoe@example.com", password="hashedpass")
            db.session.add(user)
            db.session.commit()
            
            user_in_db = User.query.filter_by(email="johndoe@example.com").first()
            self.assertIsNotNone(user_in_db)
            self.assertEqual(user_in_db.name, "JohnDoe")

    def test_create_movie(self):
        """Test creating a Movie model instance."""
        with self.app.app_context():
            movie = Movie(title="Inception", genre="Sci-Fi", price=5, stock=10)
            db.session.add(movie)
            db.session.commit()
            
            movie_in_db = Movie.query.filter_by(title="Inception").first()
            self.assertIsNotNone(movie_in_db)
            self.assertEqual(movie_in_db.genre, "Sci-Fi")

    def test_rent_movie(self):
        """Test creating a Rent record."""
        with self.app.app_context():
            user = User(name="JaneDoe", email="janedoe@example.com", password="hashedpass")
            movie = Movie(title="The Matrix", genre="Action", price=4, stock=5)
            db.session.add_all([user, movie])
            db.session.commit()
            
            rent = Rent(user_id=user.id, movie_id=movie.id, rented_date=datetime.now(UTC), deadline=datetime.now(UTC))
            db.session.add(rent)
            db.session.commit()
            
            rent_in_db = Rent.query.filter_by(user_id=user.id, movie_id=movie.id).first()
            self.assertIsNotNone(rent_in_db)
            self.assertEqual(rent_in_db.returned, False)

if __name__ == '__main__':
    unittest.main()
