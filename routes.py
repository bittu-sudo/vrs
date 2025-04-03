from flask import Flask, render_template, request,session
from models import app, db , User, Staff, Movie, Rent
import bcrypt
from models import User, Staff, Movie, Rent
from functions import rentmovie, add_movie ,search_movies, return_movie, send_mail, format_genre
from flask import flash, redirect, url_for 
import pandas as pd
import pickle
from flask_login import login_user

# from recommenders import recommendations
recommendations = {}
uni=""

with open('rec_model', 'rb') as file:
    recommendations = pickle.load(file)

@app.route("/")
def ho():
    try:
        # Check if movies already exist before adding
        if Movie.query.first() is None:
            df = pd.read_csv('/home/sathwik/first_proj/movies_metadata.csv', low_memory=False)
            df['poster_path'] = df['poster_path'].fillna("")  # Replace NaN with empty string
            df.loc[df['poster_path'].str.startswith("/"), 'poster_path'] = "poster.jpeg"

            # Instead of bulk saving, add movies one by one
            for index, row in df.iterrows():
                movie = Movie(
                    title=row['title'],
                    year=row['release_date'],
                    genre=row['genres'],
                    posterpath=row['poster_path'],
                    overview=row['overview'],
                    stock=10,
                    price=100
                )
                db.session.add(movie)
                
                # Commit in batches to avoid memory issues
                if index % 100 == 0:
                    db.session.commit()
            
            # Final commit for any remaining movies
            db.session.commit()
    except Exception as e:
        print(f"Error loading movies: {e}")
        db.session.rollback()  # Roll back the session on error
        # Continue even if movies can't be loaded

    return render_template("welcome.html")

@app.route("/welcome", methods=['POST','GET'])
def welcome():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method=='POST':
        email=request.form['email']
        user=User.query.filter_by(email=email).first()
        if user is None:
            return render_template("join.html", email=email)
        else:
            return redirect(url_for('login_user'))
    return render_template("welcome.html")

@app.route("/join", methods=['POST','GET'])
def join():
  if 'username' in session:
    return redirect(url_for('home'))
  if request.method=='POST':
    Username=request.form['username']
    email=request.form['email']
    user=User.query.filter_by(name=Username).first()
    if user is not None:
      flash('Username already taken!Try with another one','error')
      return render_template("join.html", email=email)
    global uni
    uni=Username
    Role=request.form['role']
    if Role=='User':
     user=User.query.filter_by(email=email).first()
     if user:
        flash('Email already taken!Try with another one','error')
        return render_template("join.html", email=email)
    elif Role=='Staff':
     staff=Staff.query.filter_by(email=email).first()
     if staff:
        flash('Email already taken!Try with another one','error')
        return render_template("join.html", email="")
    Password=request.form['password']
    rePassword=request.form['repassword']
    if Password!=rePassword:
      flash('Passwords do not match!','error')
      return render_template("join.html", email=email)
    else:
      
      if Role=='User':
        user = User(name=Username, email=email, password=Password)
        db.session.add(user)
        db.session.commit()
        flash('Successfully registered! Please log in.','success')
        return redirect(url_for('login_user'))
      elif Role=='Staff':
        staff = Staff(name=Username, email=email, password=Password)
        db.session.add(staff)
        db.session.commit()
        flash('Successfully registered! Please log in.','success')
        return redirect(url_for('login_staff'))
  return render_template("join.html", email="")


@app.route("/login_user", methods=['POST','GET'])
def login_user():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username'].strip()
        email=request.form['email']
        uni=username
        password=request.form['password']
        user=User.query.filter_by(name=username).first()
        remember = request.form.get('remember') 
        if user is None or user.email!=email or user.password!=password:
            return render_template("login_user.html", warn="y")
        else:
            session['username']=username
            session.permanent = False
            if request.form.get('remember'):
                session.permanent=True
            flash('Successfully logged in!','success')
            return redirect(url_for('home'))
    return render_template("login_user.html")

@app.route("/logout", methods=['POST','GET'])
def logout():
    session.pop('username', None)
    session.pop('cart', None)
    session.pop('st', None)
    session.pop('manager', None)
    session.clear()
    session.permanent = False
    return redirect(url_for('welcome'))
  
@app.route("/home", methods=['POST','GET'])
def home():
    user = User.query.filter_by(name=session.get('username')).first()
    
    # Get the last movie with fallback to "Titanic"
    try:
        lm = user.lastmovie if user and user.lastmovie else "Titanic"
    except:
        lm = "Titanic"
    
    # Safely get recommendations with error handling
    try:
        movie_key = lm.lower()
        if movie_key in recommendations:
            movie_list = recommendations[movie_key]
        else:
            # Fallback to a known existing key or a list of default movies
            default_key = "titanic"  # Make sure this key exists in your recommendations
            movie_list = recommendations.get(default_key, ["Titanic", "Avatar", "The Godfather", "Pulp Fiction", "The Dark Knight"])
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        # Fallback to a list of default movies
        movie_list = ["Titanic", "Avatar", "The Godfather", "Pulp Fiction", "The Dark Knight"]
    
    # Get movie objects from database
    movies = []
    for movie_title in movie_list:
        movie = Movie.query.filter_by(title=movie_title).first()
        if movie is not None:
            movies.append(movie)
    
    # Default sorting
    movies = sorted(movies, key=lambda x: x.price)
    
    if request.method == 'POST':
        genre = request.form.get('genre')
        sort = request.form.get('sort')
        
        # Apply genre filter if not "All"
        if genre and genre != "all":
            # Convert genre to lowercase for case-insensitive comparison
            lower_genre = genre.lower()
            movies = [movie for movie in movies if lower_genre in movie.genre.lower()]
            
        # Apply sorting regardless of genre filter
        if sort == "price":
            movies = sorted(movies, key=lambda x: x.price)
        elif sort == "rating":
            movies = sorted(movies, key=lambda x: x.rating, reverse=True)  # Higher ratings first
        elif sort == "release":
            movies = sorted(movies, key=lambda x: x.year, reverse=True)  # Newest first
    
    # Prepare data for template
    titles = [movie.title for movie in movies]
    links = [movie.posterpath for movie in movies]
    prices = [movie.price for movie in movies]
    genres = [format_genre(movie.genre) for movie in movies]
    
    return render_template("home.html", movie_titles=titles, movie_links=links,
                          length=len(links), movie_prices=prices, movie_genres=genres)
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        inpu = request.form.get('query', '')
        
        # Get search results
        movie_objs = search_movies(inpu)
        
        # Handle both list and single result from search_movies
        if isinstance(movie_objs, list):
            matches = movie_objs  # These are already movie objects
        elif movie_objs:
            matches = [movie_objs]  # Single movie object
        else:
            matches = []  # No matches
            
        # Get recommendations based on the query
        rec_titles = recommendations.get(inpu.lower(), [])  # List of recommended movie titles
        rec_objs = []
        
        for title in rec_titles:
            movie = Movie.query.filter_by(title=title).first()
            if movie:
                rec_objs.append(movie)

        # Default sort by price
        rec_objs = sorted(rec_objs, key=lambda x: x.price)
        
        # Combine search results and recommendations - matches first, then sorted recommendations
        all_movies = matches + rec_objs
        
        if not all_movies:
            flash('No movies found!', 'error')
            return render_template("search.html", inpu=inpu, movie_links=[], movie_titles=[], length=0, movie_prices=[], movie_genres=[])
            
        # Prepare data for template
        titles = [movie.title for movie in all_movies]
        links = [movie.posterpath for movie in all_movies]
        prices = [movie.price for movie in all_movies]
        genres = [format_genre(movie.genre) for movie in all_movies]
        
        return render_template("search.html",
                               inpu=inpu,
                               movie_titles=titles,
                               movie_links=links,
                               length=len(links),
                               movie_prices=prices,
                               movie_genres=genres)
    
    # Handle GET request
    return render_template("search.html", 
                           inpu="",
                           movie_titles=[], 
                           movie_links=[],
                           length=0, 
                           movie_prices=[], 
                           movie_genres=[])

@app.route('/searchsort', methods=['GET', 'POST'])
def searchsort():
    if request.method == 'POST':
        inpu = request.form.get('searchcontent', '')
        
        # Get search results
        movie_objs = search_movies(inpu)
        
        # Handle both list and single result from search_movies
        if isinstance(movie_objs, list):
            matches = movie_objs  # These are already movie objects
        elif movie_objs:
            matches = [movie_objs]  # Single movie object
        else:
            matches = []  # No matches
            
        # Get recommendations based on the query
        rec_titles = recommendations.get(inpu, [])  # List of recommended movie titles
        rec_objs = []
        
        for title in rec_titles:
            movie = Movie.query.filter_by(title=title).first()
            if movie:
                rec_objs.append(movie)
        
        # Apply filtering and sorting ONLY to recommendations
        genre = request.form.get('genre')
        sort = request.form.get('sort')
        
        # Apply genre filter if not "all"
        if genre and genre != "all":
            lower_genre = genre.lower()
            rec_objs = [movie for movie in rec_objs if lower_genre in movie.genre.lower()]
            matches = [movie for movie in matches if lower_genre in movie.genre.lower()]
            
        # Apply sorting to recommendations only
        if sort == "price":
            rec_objs = sorted(rec_objs, key=lambda x: x.price)
            matches = sorted(matches, key=lambda x: x.price)
        elif sort == "rating":
            rec_objs = sorted(rec_objs, key=lambda x: x.rating)
            matches = sorted(matches, key=lambda x: x.rating)
        elif sort == "release":
            rec_objs = sorted(rec_objs, key=lambda x: x.year)
            matches = sorted(matches, key=lambda x: x.year)
        else:
            # Default sorting by price
            rec_objs = sorted(rec_objs, key=lambda x: x.price)
            matches = sorted(matches, key=lambda x: x.price)
        
        # Combine search results and recommendations - matches first, then sorted recommendations
        all_movies = matches + rec_objs
        
        if not all_movies:
            return render_template("no_search.html", inpu=inpu)
            
        # Prepare data for template
        titles = [movie.title for movie in all_movies]
        links = [movie.posterpath for movie in all_movies]
        prices = [movie.price for movie in all_movies]
        genres = [format_genre(movie.genre) for movie in all_movies]
        
        return render_template("search.html", 
                               inpu=inpu,
                               movie_titles=titles, 
                               movie_links=links,
                               length=len(links), 
                               movie_prices=prices, 
                               movie_genres=genres)
    
    # Handle GET request
    return render_template("search.html", 
                           input="",
                           movie_titles=[], 
                           movie_links=[],
                           length=0, 
                           movie_prices=[], 
                           movie_genres=[])



@app.route('/view_movie/<title>', methods=['GET'])
def view_movie(title):
  
  # if request.method=='POST':
  #   return redirect(url_for("rent", title=title, warn="n"))
  if Movie.query.filter_by(title=title).first() is None:
    return render_template("404.html", inpu=title), 404
  price=(Movie.query.filter_by(title=title).first()).price
  genre=format_genre((Movie.query.filter_by(title=title).first()).genre)
  overview=(Movie.query.filter_by(title=title).first()).overview
  posterpath=(Movie.query.filter_by(title=title).first()).posterpath
  rating=(Movie.query.filter_by(title=title).first()).rating
  stock=(Movie.query.filter_by(title=title).first()).stock
  release_date=(Movie.query.filter_by(title=title).first()).year
  movies = [movie for movie in recommendations[title.lower()] if movie != title]
  links=[]
  prices=[]
  genres=[]
  if movies:
   links=[(Movie.query.filter_by(title=movie).first()).posterpath for movie in movies]
   prices=[(Movie.query.filter_by(title=movie).first()).price for movie in movies]
   genres=[format_genre((Movie.query.filter_by(title=movie).first()).genre) for movie in movies]
  return render_template("view_movie.html", title=title, price=str(price), genre=str(genre), release_date=str(release_date),overview=overview, posterpath=str(posterpath), rating=str(rating), stock=str(stock),movie_links=links, movie_titles=movies,movie_prices=prices,movie_genres=genres,length=len(movies))

@app.route('/rent_movie/<title>', methods=['POST', 'GET'])
def rent_movie(title):
  if 'username' not in session:
    return redirect(url_for('login_user'))
  uni=session.get('username','')
  user = User.query.filter_by(name=uni).first()
  price=(Movie.query.filter_by(title=title).first()).price
  rating=(Movie.query.filter_by(title=title).first()).rating
  stock=(Movie.query.filter_by(title=title).first()).stock
  if stock==0:
      return render_template("rent_movie.html", title=title, price=str(price),rating=str(rating), stock=str(stock),warn="stock")
  if price > User.query.filter_by(name=session.get('username')).first().balance:
      return render_template("rent_movie.html", title=title, price=str(price),rating=str(rating), stock=str(stock),warn="balance")
  rentmovie((User.query.filter_by(name=session.get('username')).first()).id, (Movie.query.filter_by(title=title).first()).id)
  rentals=Rent.query.filter_by(user_id=(User.query.filter_by(name=uni).first()).id).all()
  # Separate active and returned rentals
  active_rentals = [rental for rental in rentals if rental is not None and not rental.returned]
  returned_rentals = [rental for rental in rentals if rental is not None and rental.returned]
    
    # Process active rentals
  active_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in active_rentals]
  active_order = [order for order in active_rentals]
  active_borrow_date = [order.rented_date for order in active_rentals]
  active_borrow_date=[i.strftime('%Y-%m-%d') for i in active_borrow_date]
  active_deadline = [order.deadline for order in active_rentals]
  active_deadline=[i.strftime('%Y-%m-%d') for i in active_deadline]
  active_length = len(active_titles)
    
    # Process returned rentals
  returned_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in returned_rentals]
  returned_borrow_date = [order.rented_date for order in returned_rentals]
  returned_borrow_date=[i.strftime('%Y-%m-%d') for i in returned_borrow_date]
  returned_deadline = [order.deadline for order in returned_rentals]
  returned_deadline=[i.strftime('%Y-%m-%d') for i in returned_deadline]
  returned_length = len(returned_titles)
  balance = user.balance
 
  return render_template(
        "myrentals.html", 
        balance=balance,
        active_titles=active_titles, 
        active_rented_date=active_borrow_date, 
        active_deadline=active_deadline, 
        active_length=active_length,
        active_order=active_order,
        returned_titles=returned_titles, 
        returned_rented_date=returned_borrow_date, 
        returned_deadline=returned_deadline, 
        returned_length=returned_length,
        user=uni
    )   

@app.route('/addcart/<title>', methods=['POST', 'GET'])
def addcart(title):
    if 'username' not in session:
        return redirect(url_for('login_user'))
    uni = session.get('username','')
    user = User.query.filter_by(name=uni).first()
    movie = Movie.query.filter_by(title=title).first()
    price = movie.price
    rating = movie.rating
    stock = movie.stock
    if stock==0:
        return render_template("view_movie.html", title=title, price=str(price),rating=str(rating), stock=str(stock),warn="stock")
    
    if 'cart' not in session:
        session['cart'] = []
    if title in session['cart']:
        flash(f'{title} already in cart!', 'error')
        return redirect(url_for('cart'))
    session['cart'].append(title)
    flash(f'{title} added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/removecart/<title>', methods=['POST', 'GET'])
def removecart(title):
    if 'cart' in session:
        if title in session.get('cart'):
            session['cart'].remove(title)
            flash(f'{title} removed from cart!', 'success')
        else:
            flash(f'{title} not in cart!', 'error')
    return redirect(url_for('cart'))

@app.route('/cart', methods=['POST', 'GET'])
def cart():
    if 'username' not in session:
        return redirect(url_for('login_user'))
    if request.method == 'POST':
        if 'cart' not in session:
            flash('Cart is empty!', 'error')
            return redirect(url_for('cart'))
        titles = session['cart']
        movies = [Movie.query.filter_by(title=title).first() for title in titles]
        prices = [movie.price for movie in movies]
        tot_price = sum(prices)
        user = User.query.filter_by(name=session.get('username')).first()
        if tot_price > user.balance:
            flash('Insufficient balance!', 'error')
            return redirect(url_for('cart'))
        if 'cart' in session:
            for movie in movies:
                rentmovie(user.id, movie.id)
            user.balance -= tot_price
            db.session.commit()
            flash('Movies rented successfully!', 'success')
            session.pop('cart', None)
            return redirect(url_for('cart'))
    user = User.query.filter_by(name=session.get('username')).first()
    if 'cart' in session:
        titles = session['cart']
        movies = [Movie.query.filter_by(title=title).first() for title in titles]
        links = [movie.posterpath for movie in movies]
        prices = [movie.price for movie in movies]
        tot_price = sum(prices)
        genres = [format_genre(movie.genre) for movie in movies]
        return render_template("cart.html", movie_titles=titles, movie_prices=prices, movie_genres=genres, movie_links=links, length=len(titles), total=tot_price, balance=user.balance)
    return render_template("cart.html", movie_titles=[], movie_prices=[], movie_genres=[], movie_links=[], length=0, total=0, balance=user.balance)

@app.route("/myrentals", methods=['POST', 'GET'])
def myrentals():
    if 'username' not in session:
        return redirect(url_for('login_user'))
    uni = session.get('username', '')
    user = User.query.filter_by(name=uni).first()
    rentals = Rent.query.filter_by(user_id=user.id).all()
    
    # Separate active and returned rentals
    active_rentals = [rental for rental in rentals if rental is not None and not rental.returned]
    returned_rentals = [rental for rental in rentals if rental is not None and rental.returned]
    
      
    # Process active rentals
    active_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in active_rentals]
    active_order = [order for order in active_rentals]
    active_borrow_date = [order.rented_date for order in active_rentals]
    active_borrow_date=[i.strftime('%Y-%m-%d') for i in active_borrow_date]
    active_deadline = [order.deadline for order in active_rentals]
    active_deadline=[i.strftime('%Y-%m-%d') for i in active_deadline]
    active_length = len(active_titles)
    
    # Process returned rentals
    returned_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in returned_rentals]
    returned_borrow_date = [order.rented_date for order in returned_rentals]
    returned_borrow_date=[i.strftime('%Y-%m-%d') for i in returned_borrow_date]
    returned_deadline = [order.deadline for order in returned_rentals]
    returned_deadline=[i.strftime('%Y-%m-%d') for i in returned_deadline]
    returned_length = len(returned_titles)
    balance = user.balance
    
    if request.method == "POST":
        rating = request.form.get('rating')  # Use .get() to avoid KeyError
        title_sel = request.form.get('title')  # Get selected movie title
        if not rating or not title_sel:  # Ensure both fields exist
            flash("Please select a rating and movie.","error")
            return redirect(url_for("myrentals"))
        movie = Movie.query.filter_by(title=title_sel).first()
        if movie:
            movie.rating = (float(movie.rating) + float(rating)) / 2
            db.session.commit()
            flash("rating submitted sucessfully!","success")
            return redirect(url_for("myrentals"))
    
    return render_template(
        "myrentals.html", 
        balance=balance,
        active_titles=active_titles, 
        active_rented_date=active_borrow_date, 
        active_deadline=active_deadline, 
        active_length=active_length,
        active_order=active_order,
        returned_titles=returned_titles, 
        returned_rented_date=returned_borrow_date, 
        returned_deadline=returned_deadline, 
        returned_length=returned_length,
        user=uni
    )
@app.route('/returnmovie/<rent_id>', methods=['POST', 'GET'])
def returnmovie(rent_id):
    if 'username' not in session:
        return redirect(url_for('login_user'))
    return_movie(rent_id)
    return redirect(url_for('myrentals'))
    

@app.route("/add_credit/", methods=['POST','GET'])
def add_credit():
    if 'username' not in session:
        return redirect(url_for('login_user'))
    user = User.query.filter_by(name=session['username']).first()
    amount = request.form.get('amount', type=int)
    ref = request.form.get('redirect', '')
    if amount and amount > 0:
        user.balance += amount
        db.session.commit()
        flash("Money credited successfully!",'success')
    if ref == 'cart':
        return redirect(url_for('cart'))
    return redirect(url_for('myrentals'))
@app.route("/login_staff", methods=['POST', 'GET'])
def login_staff():
    if request.method == 'POST':
        staffname = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        
        staff = Staff.query.filter_by(name=staffname).first()
        
        if (staff is None) or (staff.email != email) or (staff.password != password):
            flash('Invalid credentials!', 'error')
            return render_template("login_staff.html")
        else:
            session['st'] = "True"
            if request.form.get('remember'):
                session.permanent = True
            return redirect(url_for('staff'))
            
    return render_template("login_staff.html")

@app.route("/staff", methods=['POST', 'GET'])
def staff():
    # Check if staff is logged in
    if 'st' not in session:
        return redirect(url_for('login_staff'))
        
    # Handle POST request for updating movie stock
    if request.method == 'POST':
        moviename = request.form.get('moviename')
        stock = request.form.get('stock', 0)
        
        try:
            stock = int(stock)
        except ValueError:
            flash('Stock must be a number!', 'error')
            return redirect(url_for('staff'))
            
        # Check if movie already exists
        existing_movie = Movie.query.filter_by(title=moviename).first()
        if existing_movie:
            existing_movie.stock += stock
            db.session.commit()
            flash(f'Movie stock updated!', 'success')
        else:
            flash(f'Movie not found!', 'error')
        return redirect(url_for('staff'))
    
    # Get active rentals
    orders = Rent.query.filter_by(returned=False).all()
    
    # Prepare data for template
    
    if orders:
                 id=[order.id for order in orders]
                 titles=[(Movie.query.filter_by(id=order.movie_id).first()).title for order in orders]
                 deadline=[order.deadline for order in orders]
                 deadline=[i.strftime('%Y-%m-%d') for i in deadline]
                 user_name=[(User.query.filter_by(id=order.user_id).first()).name for order in orders]
                 user_email=[(User.query.filter_by(id=order.user_id).first()).email for order in orders]
                 stock_movies = [movie.title for movie in Movie.query.filter_by(stock=0).all()]
                 length=len(user_name)
    else:
        titles = []
        deadline = []
        user_name = []
        user_email = []
        length = 0
        id = []
    # Get out of stock movies
    stock_movies = [movie.title for movie in Movie.query.filter_by(stock=0).all()]
    warn = 'n'
    if len(stock_movies)==0:
        warn = 'y'
    
    return render_template("staff.html", titles=titles, deadline=deadline, user_name=user_name, user_email=user_email, length=length,out_of_stock_movies=stock_movies,order_id=id,warn=warn)
    

@app.route("/sendmail/<order_id>", methods=['POST','GET'])
def sendmail(order_id):
    if 'st' not in session:
        return redirect(url_for('login_staff'))
    order = Rent.query.get(order_id)
    user = User.query.get(order.user_id)
    movie = Movie.query.get(order.movie_id)
    Message = f"Dear {user.name},\n\nThis is to remind you that the movie {movie.title} is due for return by {order.deadline.strftime('%Y-%m-%d')}. Please return the movie at the earliest to avoid late fees.\n\nRegards,\nMovie Rental Team"
    send_mail(user.email, "Movie Rental Reminder", Message)
    flash(f'Mail sent to {user.email} for {movie.title}', 'success')
    return redirect(url_for('staff'))


@app.route("/login_manager", methods =['POST','GET'])
def login_manager():
  if request.method=='POST':
    if request.form['password']!="admin":
        return render_template("login_manager.html", warn="y")
    else:
        session['manager'] = "True"
        return redirect(url_for('manager'))
  return render_template("login_manager.html")

@app.route("/manager", methods=['POST','GET'])
def manager():
    if 'manager' not in session:
        return redirect(url_for('login_manager'))
    if request.method == 'POST':
      moviename = request.form.get('movieName','')
      if moviename:
        stock = request.form.get('stock','')
        price = request.form.get('price','')
        genre = request.form.get('genre','')
        overview = request.form.get('overview','')
        posterpath = request.form.get('posterpath','')
        rating = request.form.get('rating','')
        year = request.form.get('year','')
        # Check if movie already exists
        existing_movie = Movie.query.filter_by(title=moviename).first()
        
        if existing_movie:
            existing_movie.stock = stock
            existing_movie.price = price
            existing_movie.genre = genre
            existing_movie.overview = overview
            existing_movie.posterpath = posterpath
            existing_movie.rating = rating
            existing_movie.year = year
            db.session.commit()
            flash(f'Movie updated!',
                  'success')
        else:
             add_movie(moviename, stock, genre, rating, year, posterpath, price, overview)
             flash(f'Movie added!', 'success')
      if 'movie_title' in request.form:
         movie_delete = request.form.get('movie_title')
         if movie_delete:
            movie = Movie.query.filter_by(title=movie_delete).first()
            if movie:
             db.session.delete(movie)
             db.session.commit()
             flash(f'Movie deleted!', 'success')
            else:
             flash(f'Movie not found!', 'error')
        
      return redirect(url_for('manager'))
    return render_template("manager.html")


@app.route("/total_rentals", methods=['POST','GET'])
def total_rentals():
    if 'manager' not in session:
        return redirect(url_for('login_manager'))
    rentals=Rent.query.filter_by(returned=False).all()
    id=[order.id for order in rentals]
    titles=[(Movie.query.filter_by(id=order.movie_id).first()).title for order in rentals]
    deadline=[order.deadline for order in rentals]
    deadline=[i.strftime('%Y-%m-%d') for i in deadline]
    user_name=[(User.query.filter_by(id=order.user_id).first()).name for order in rentals]
    borrowed_date=[order.rented_date for order in rentals]
    borrowed_date=[i.strftime('%Y-%m-%d') for i in borrowed_date]
    length=len(user_name)
    return render_template("total_rentals.html", id=id,titles=titles, deadline=deadline, user_name=user_name, borrowed_date=borrowed_date, length=length) 

@app.route("/delete_user", methods=['POST','GET'])
def delete_user():
    if 'manager' not in session:
        return redirect(url_for('login_manager'))
    if request.method == 'POST':
        role = request.form.get('role', '')
        username = request.form.get('username', '')

        if not username:
            flash('Username is required!', 'error')
            return redirect(url_for('delete_user'))
        
        if role == 'user':
            model = User
        elif role == 'staff':
            model = Staff
        else:
            flash('Invalid role specified!', 'error')
            return redirect(url_for('delete_user'))
        
        user = model.query.filter_by(name=username).first()
        if user:
            # Delete rentals first
            Rent.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            flash(f'{role.capitalize()} deleted successfully!', 'success')
        else:
            flash(f'{role.capitalize()} not found!', 'error')
        
        return redirect(url_for('delete_user'))
    
    return render_template("delete_user.html")


@app.errorhandler(404)
def not_found(e):
  return render_template("404.html"), 404

if __name__ == '__main__':
    app.run(debug=True)