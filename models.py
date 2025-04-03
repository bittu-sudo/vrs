from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

# Initialize Flask app
app = Flask(__name__)

# Set app configuration
app.config['SECRET_KEY'] = '229b845d2e364ca8a032e35c104f69b1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy()
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),unique=True, nullable=False)
    email=db.Column(db.String(120),unique=True, nullable= False)
    password=db.Column(db.String(50),nullable=False)
    balance=db.Column(db.Integer)
    rents = db.relationship('Rent', backref='user')
    lastmovie=db.Column(db.String(100))

    def __init__(self, name, email, password, balance=1000, lastmovie=""):
        self.name=name
        self.email=email
        self.password = generate_password_hash(password)
        self.balance=balance
        self.lastmovie=lastmovie

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price=db.Column(db.Integer)
    genre=db.Column(db.String(50))
    rating=db.Column(db.Float)
    stock=db.Column(db.Integer)
    rents = db.relationship('Rent', backref='movie')
    overview=db.Column(db.String(2000))
    posterpath=db.Column(db.String(500))
    year=db.Column(db.Integer)

    def __init__(self, title, genre, price=0, rating=5, stock=0, overview="", posterpath="", year=2000):
        self.title=title
        self.genre=genre
        self.price = price
        self.rating = rating
        self.stock =stock
        self.overview =overview
        self.posterpath = posterpath
        self.year=year


class Rent(db.Model):
    id = db.Column(db.Integer, primary_key=True,nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    rented_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)

    def __init__(self, user_id, movie_id, rented_date, deadline):
        self.user_id=user_id
        self.movie_id=movie_id
        self.rented_date=rented_date
        self.deadline=deadline
        self.returned=False

with app.app_context():
    db.create_all()





