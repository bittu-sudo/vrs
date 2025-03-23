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
@app.route("/")
def ho():
    try:
        # Check if movies already exist before adding
        if Movie.query.first() is None:
            df = pd.read_csv('/home/sathwik/first_proj/movies_metadata.csv', low_memory=False)
            df['poster_path'] = df['poster_path'].fillna("")  # Replace NaN with empty string
            df.loc[df['poster_path'].str.startswith("/"), 'poster_path'] = "https://img.lovepik.com/background/20211029/medium/lovepik-film-festival-simple-shooting-videotape-poster-background-image_605811936.jpg"

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

    return render_template("login_user.html")

@app.route("/join", methods=['POST','GET'])
def join():
  if request.method=='POST':
    Username=request.form['username']
    user=User.query.filter_by(name=Username).first()
    if user is not None:
      flash('Username already taken!Try with another one','error')
      return render_template("join.html")
    global uni
    uni=Username
    Role=request.form['role']
    email=request.form['email']
    if Role=='User':
     user=User.query.filter_by(email=email).first()
     if user:
        flash('Email already taken!Try with another one','error')
        return render_template("join.html")
    elif Role=='Staff':
     staff=Staff.query.filter_by(email=email).first()
     if staff:
        flash('Email already taken!Try with another one','error')
        return render_template("join.html")
    Password=request.form['password']
    rePassword=request.form['repassword']
    if Password!=rePassword:
      flash('Passwords do not match!','error')
      return render_template("join.html")
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
  return render_template("join.html") 


@app.route("/login_user", methods=['POST','GET'])
def login_user():
    global uni
    if request.method=='POST':
        username=request.form['username'].strip()
        email=request.form['email']
        uni=username
        session['username']=username
        password=request.form['password']
        user=User.query.filter_by(name=username).first()
        remember = request.form.get('remember') 
        if user is None or user.email!=email or user.password!=password:
            return render_template("login_user.html", warn="y")
        else:
            flash('Successfully logged in!','success')
            return redirect(url_for('home'))
    return render_template("login_user.html")
  
@app.route("/home", methods=['POST','GET'])
def home():
    user = User.query.filter_by(name=session.get('username')).first()
    if user is None:
      return render_template("login_user.html")
    
    movies = recommendations[user.lastmovie]
    movies = [Movie.query.filter_by(title=movie).first() for movie in movies]
    movies = [movie for movie in movies if movie is not None]  # Filter out None values
    
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
            movies = sorted(movies, key=lambda x: x.rating)
        elif sort == "release":
            movies = sorted(movies, key=lambda x: x.year)
    
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
        rec_titles = recommendations.get(inpu, [])  # List of recommended movie titles
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
            
        # Apply sorting to recommendations only
        if sort == "price":
            rec_objs = sorted(rec_objs, key=lambda x: x.price)
        elif sort == "rating":
            rec_objs = sorted(rec_objs, key=lambda x: x.rating)
        elif sort == "release":
            rec_objs = sorted(rec_objs, key=lambda x: x.year)
        else:
            # Default sorting by price
            rec_objs = sorted(rec_objs, key=lambda x: x.price)
        
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



@app.route('/view_movie/<title>', methods=['POST', 'GET'])
def view_movie(title):
  
  # if request.method=='POST':
  #   return redirect(url_for("rent", title=title, warn="n"))
  price=(Movie.query.filter_by(title=title).first()).price
  genre=format_genre((Movie.query.filter_by(title=title).first()).genre)
  overview=(Movie.query.filter_by(title=title).first()).overview
  posterpath=(Movie.query.filter_by(title=title).first()).posterpath
  rating=(Movie.query.filter_by(title=title).first()).rating
  stock=(Movie.query.filter_by(title=title).first()).stock
  release_date=(Movie.query.filter_by(title=title).first()).year
  movies = [movie for movie in recommendations[title] if movie != title]
  links=[]
  prices=[]
  genres=[]
  if movies:
   links=[(Movie.query.filter_by(title=movie).first()).posterpath for movie in movies]
   prices=[(Movie.query.filter_by(title=movie).first()).price for movie in movies]
   genres=[format_genre((Movie.query.filter_by(title=movie).first()).genre) for movie in movies]
  return render_template("view_movie.html", title=title, price=str(price), genre=str(genre), release_date=str(release_date),overview=overview, posterpath=str(posterpath), rating=str(rating), stock=str(stock),movie_links=links, movie_titles=movies,movie_prices=prices,movie_genres=genres,length=len(links))

@app.route('/rent_movie/<title>', methods=['POST', 'GET'])
def rent_movie(title):
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
  active_deadline = [order.deadline for order in active_rentals]
  active_length = len(active_titles)
    
    # Process returned rentals
  returned_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in returned_rentals]
  returned_borrow_date = [order.rented_date for order in returned_rentals]
  returned_deadline = [order.deadline for order in returned_rentals]
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


@app.route("/myrentals", methods=['POST', 'GET'])
def myrentals():
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
    active_deadline = [order.deadline for order in active_rentals]
    active_length = len(active_titles)
    
    # Process returned rentals
    returned_titles = [(Movie.query.filter_by(id=movie.movie_id).first()).title for movie in returned_rentals]
    returned_borrow_date = [order.rented_date for order in returned_rentals]
    returned_deadline = [order.deadline for order in returned_rentals]
    returned_length = len(returned_titles)
    
    balance = user.balance
    
    if request.method == "POST":
        rating = request.form.get('rating')  # Use .get() to avoid KeyError
        title_sel = request.form.get('title')  # Get selected movie title
        if not rating or not title_sel:  # Ensure both fields exist
            flash("Please select a rating and movie.")
            return redirect(url_for("myrentals"))
        movie = Movie.query.filter_by(title=title_sel).first()
        if movie:
            movie.rating = (float(movie.rating) + float(rating)) / 2
            db.session.commit()
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
    return_movie(rent_id)
    return redirect(url_for('myrentals'))
    

@app.route("/add_credit", methods=['POST','GET'])
def add_credit():
    user = User.query.filter_by(name=session['username']).first()
    amount = request.form.get('amount', type=int)
    if amount and amount > 0:
        user.balance += amount
        db.session.commit()
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
           
            return redirect(url_for('staff'))
            
    return render_template("login_staff.html")

@app.route("/staff", methods=['POST', 'GET'])
def staff():
    # Check if staff is logged in
  
        
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
    order_data = []

    if orders:
                 id=[order.id for order in orders]
                 titles=[(Movie.query.filter_by(id=order.movie_id).first()).title for order in orders]
                 deadline=[order.deadline for order in orders]
                 user_name=[(User.query.filter_by(id=order.user_id).first()).name for order in orders]
                 user_email=[(User.query.filter_by(id=order.user_id).first()).email for order in orders]
                 stock_movies = [movie.title for movie in Movie.query.filter_by(stock=0).all()]
                 length=len(user_name)
    

    
    # Get out of stock movies
    stock_movies = [movie.title for movie in Movie.query.filter_by(stock=0).all()]
    
    return render_template("staff.html", titles=titles, deadline=deadline, user_name=user_name, user_email=user_email, length=length,out_of_stock_movies=stock_movies,order_id=id,warn='n')



@app.route("/sendmail/<order_id>", methods=['POST','GET'])
def sendmail(order_id):
    order = Rent.query.get(order_id)
    user = User.query.get(order.user_id)
    movie = Movie.query.get(order.movie_id)
    Message = f"Dear {user.name},\n\nThis is to remind you that the movie {movie.title} is due for return by {order.deadline}. Please return the movie at the earliest to avoid late fees.\n\nRegards,\nMovie Rental Team"
    send_mail(user.email, "Movie Rental Reminder", Message)
    flash(f'Mail sent to {user.email} for {movie.title}', 'success')
    return redirect(url_for('staff'))


@app.route("/login_manager", methods =['POST','GET'])
def login_manager():
  if request.method=='POST':
    if request.form['password']!="admin":
        return render_template("login_manager.html", warn="y")
    else:
        return redirect(url_for('manager'))
  return render_template("login_manager.html")

@app.route("/manager", methods=['POST','GET'])
def manager():
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
    rentals=Rent.query.filter_by(returned=False).all()
    id=[order.id for order in rentals]
    titles=[(Movie.query.filter_by(id=order.movie_id).first()).title for order in rentals]
    deadline=[order.deadline for order in rentals]
    user_name=[(User.query.filter_by(id=order.user_id).first()).name for order in rentals]
    borrowed_date=[order.rented_date for order in rentals]
    length=len(user_name)
    return render_template("total_rentals.html", id=id,titles=titles, deadline=deadline, user_name=user_name, borrowed_date=borrowed_date, length=length) 

@app.route("/delete_user", methods=['POST','GET'])
def delete_user():
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

if __name__ == '__main__':
    with open('rec_model', 'rb') as file:
        recommendations = pickle.load(file)
    app.run(debug=True)