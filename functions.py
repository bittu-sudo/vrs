from fpdf import FPDF
import os
from datetime import datetime, timedelta, UTC
from flask import flash,current_app
from models import db
from models import User, Movie, Rent
from sqlalchemy import func
from fuzzywuzzy import fuzz
import ast
import re
def rentmovie(user_id, movie_id):
    # Fetch user and movie 
    user = db.session.get(User, user_id)
    movie = db.session.get(Movie, movie_id)

    if not user:
        flash("User not found.")
        return
    if not movie:
        flash("Movie not found.")
        return

    # Check balance and stock
    if user.balance < movie.price:
        flash("Insufficient balance.",'error')
        return
    if movie.stock < 1:
        flash("Movie out of stock.",'error')
        return

    temp=Rent.query.filter_by(user_id=user_id,returned=False).all()
    
  
    if temp is not None:
        temp=[temp1.movie_id for temp1 in temp]
    if temp is not None and movie_id in temp:
        flash("Movie already rented! Please return the movie before renting again.",'error')
        return
    
    # Create rent record
    rent = Rent(
        user_id=user.id,
        movie_id=movie.id,
        rented_date=datetime.now(UTC),
        deadline=datetime.now(UTC) + timedelta(days=15)
    )
    # Update stock and balance
    movie.stock -= 1
    user.balance -= movie.price
    user.lastmovie = movie.title
    db.session.add(rent)
    db.session.commit()

    flash("Movie rented successfully!",'success')
    generate_receipt(rent.id)
    return True


def search_movies(title):
    try:
        if  len(title.strip()) == 0:
            return None
            
        # First try exact match (case-insensitive)
        exact_match = Movie.query.filter(func.lower(Movie.title) == func.lower(title)).first()
        if exact_match:
            return exact_match

        # If no exact match, try substring match (case-insensitive)
        substring_matches = Movie.query.filter(func.lower(Movie.title).contains(func.lower(title))).all()
        if substring_matches:
            return substring_matches

        # If still no matches, try fuzzy matching
        all_movies = Movie.query.all()
        fuzzy_matches = []

        for movie in all_movies:
            if movie is not None:  # Filter out None values
                # Calculate similarity ratio
                ratio = fuzz.ratio(title.lower(), movie.title.lower())
                if ratio > 70:  # Threshold for similarity
                    fuzzy_matches.append(movie)

        if fuzzy_matches:
            return fuzzy_matches

        return None
    except Exception as e:
        flash(f"Search error: {str(e)}")
        return None
    
def return_movie(order_id):        
        order_obj = Rent.query.filter_by(id=order_id).first()
        if order_obj:
            movie_obj = Movie.query.filter_by(id=order_obj.movie_id).first()
            movie_obj.stock += 1
            order_obj.returned = True
            db.session.commit()
            flash("Movie returned successfully.",'success')
            return True
        else:
            flash("Order Not Found!",'error')

 
def view_rented_orders(user_id):
    user_obj = User.query.get(user_id)
    if not user_obj:
        flash("User not found.",'error')
        return []
    
    return Rent.query.filter_by(user_id=user_obj.id).all()

def send_mail(user_email, subject, body, pdf_path=None):
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    # Email configuration
    sender_server = "smtp.gmail.com"
    sender_port = 587
    sender_email = "moviemartvrs@gmail.com"
    sender_password = "virs dpsj luau xcyt"

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    if pdf_path:
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {pdf_path}",
        )
        message.attach(part)
    
    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(sender_server, sender_port)
        server.starttls(context=context)
        server.login(sender_email, sender_password)

        # Send email
        server.send_message(message)
        flash("Email sent successfully.",'success')
        return True
        
    except Exception:
        flash("Email sending failed.",'error')
        return False
    finally:
        server.quit()

def add_movie(title, stock, genre="", rating=5, year=0, img_path="", price=0, overview=""):
    movie_obj = Movie.query.filter_by(title=title).first()
    if movie_obj is not None:
        movie_obj.stock += stock
        if price!=0:
            movie_obj.price = price
        db.session.commit()
    else:
        movie_obj = Movie(title=title, genre=genre, rating=rating, price=price, stock=stock, year=year, posterpath=img_path, overview=overview)
        db.session.add(movie_obj)
        db.session.commit()
        flash("Movie Added Successfully!",'success')
    return True
    
def format_genre(genre_string):
    try:
        genre_data = ast.literal_eval(genre_string)
        
        if type(genre_data) == list:
            genre_names = [item.get('name', '') for item in genre_data if type(item) == dict]
            return genre_names
        
        elif type(genre_data) == dict:
            return [genre_data.get('name', '')]
            
    except (SyntaxError, ValueError):
        pattern = r"'name':\s*'([^']*)'"
        matches = re.findall(pattern, genre_string)
        if matches:
            return ', '.join(matches)
    return genre_string

def generate_receipt(order_id):
    try:
        order_obj = Rent.query.filter_by(id=order_id).first()
        if order_obj is None:
            flash("Order not found.", "error")
            return None
        movie_obj = Movie.query.filter_by(id=order_obj.movie_id).first()
        user_obj = User.query.filter_by(id=order_obj.user_id).first()
        
        if order_obj and movie_obj and user_obj:
            receipt = FPDF()
            receipt.add_page()
            
            # Modern minimalist header with brand accent
            receipt.set_fill_color(45, 52, 54)  # Dark slate for header
            receipt.rect(0, 0, 210, 40, 'F')
            
            # Logo placeholder (centered)
            # receipt.image('static/images/vrs_logo.png', x=85, y=8, w=40, h=20, type='', link='')
            
            # Main title with modern font
            receipt.set_font('Helvetica', 'B', 20)
            receipt.set_text_color(255, 255, 255)  # White text
            receipt.set_xy(0, 28)
            receipt.cell(210, 10, 'MOVIE MART', 0, 1, 'C')
            
            # Add receipt date in top corner
            current_date = datetime.now().strftime("%d/%m/%Y")
            receipt.set_font('Helvetica', '', 8)
            receipt.set_text_color(200, 200, 200)  # Light gray
            receipt.set_xy(160, 5)
            receipt.cell(45, 5, f'Date: {current_date}', 0, 0, 'R')
            
            # Receipt ID with subtle style
            receipt.set_xy(0, 45)
            receipt.set_font('Helvetica', 'B', 12)
            receipt.set_text_color(45, 52, 54)  # Dark slate
            receipt.cell(210, 10, f'Receipt #{order_obj.id}', 0, 1, 'C')
            
            # Stylish divider with gradient effect
            receipt.set_draw_color(231, 76, 60)  # Red accent
            receipt.set_line_width(0.5)
            receipt.line(30, 58, 180, 58)
            
            # Create two-column layout
            col_width = 90
            left_col_x = 15
            right_col_x = 115
            current_y = 65
            
            # CUSTOMER INFO SECTION - Left column
            receipt.set_font('Helvetica', 'B', 11)
            receipt.set_text_color(231, 76, 60)  # Red accent for section headers
            receipt.set_xy(left_col_x, current_y)
            receipt.cell(col_width, 8, 'CUSTOMER DETAILS', 0, 1, 'L')
            current_y += 10
            
            # Customer info with icons
            receipt.set_font('Helvetica', '', 9)
            receipt.set_text_color(70, 70, 70)  # Dark gray for text
            
            # Add circular bullet points
            receipt.set_xy(left_col_x, current_y)
            receipt.set_fill_color(231, 76, 60)  # Red accent
            # receipt.circle(left_col_x + 2, current_y + 2, 1.5, 'F')
            receipt.set_xy(left_col_x + 7, current_y)
            receipt.cell(25, 5, 'ID:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(60, 5, f'{user_obj.id}', 0, 1, 'L')
            current_y += 7
            
            receipt.set_font('Helvetica', '', 9)
            receipt.set_xy(left_col_x, current_y)
            receipt.set_fill_color(231, 76, 60)
            # receipt.circle(left_col_x + 2, current_y + 2, 1.5, 'F')
            receipt.set_xy(left_col_x + 7, current_y)
            receipt.cell(25, 5, 'Name:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(60, 5, f'{user_obj.name}', 0, 1, 'L')
            current_y += 7
            
            receipt.set_font('Helvetica', '', 9)
            receipt.set_xy(left_col_x, current_y)
            receipt.set_fill_color(231, 76, 60)
            # receipt.circle(left_col_x + 2, current_y + 2, 1.5, 'F')
            receipt.set_xy(left_col_x + 7, current_y)
            receipt.cell(25, 5, 'Email:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(60, 5, f'{user_obj.email}', 0, 1, 'L')
            
            # RENTAL DETAILS - Right column
            current_y = 65  # Reset Y position for right column
            receipt.set_font('Helvetica', 'B', 11)
            receipt.set_text_color(231, 76, 60)  # Red accent
            receipt.set_xy(right_col_x, current_y)
            receipt.cell(col_width, 8, 'RENTAL DETAILS', 0, 1, 'L')
            current_y += 10
            
           
           
            if isinstance(order_obj.rented_date, str):
                    formatted_date = datetime.strptime(order_obj.rented_date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
            else:
                    formatted_date = order_obj.rented_date.strftime("%d/%m/%Y")
            # except ValueError:
            #     formatted_date = str(order_obj.rented_date).split()[0]
            
            # Rental info with icons
            receipt.set_font('Helvetica', '', 9)
            receipt.set_text_color(70, 70, 70)
            
            receipt.set_xy(right_col_x, current_y)
            receipt.set_fill_color(231, 76, 60)
            # receipt.circle(right_col_x + 2, current_y + 2, 1.5, 'F')
            receipt.set_xy(right_col_x + 7, current_y)
            receipt.cell(25, 5, 'Order ID:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(60, 5, f'{order_obj.id}', 0, 1, 'L')
            current_y += 7
            
            receipt.set_font('Helvetica', '', 9)
            receipt.set_xy(right_col_x, current_y)
            receipt.set_fill_color(231, 76, 60)
            # receipt.circle(right_col_x + 2, current_y + 2, 1.5, 'F')
            receipt.set_xy(right_col_x + 7, current_y)
            receipt.cell(25, 5, 'Rental Date:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(60, 5, f'{formatted_date}', 0, 1, 'L')
            current_y += 7
            
            # Feature movie details in center panel
            movie_section_y = 100
            receipt.set_xy(0, movie_section_y)
            receipt.set_fill_color(240, 240, 240)  # Light gray background
            receipt.rect(15, movie_section_y, 180, 40, 'F')
            
            receipt.set_font('Helvetica', 'B', 11)
            receipt.set_text_color(45, 52, 54)  # Dark slate
            receipt.set_xy(25, movie_section_y + 5)
            receipt.cell(160, 8, 'MOVIE DETAILS', 0, 1, 'L')
            
            # Add movie poster placeholder (small thumbnail)
            receipt.set_fill_color(200, 200, 200)  # Gray for poster placeholder
            receipt.rect(25, movie_section_y + 15, 20, 15, 'F')
            
            # Movie info with stylish presentation
            receipt.set_font('Helvetica', 'B', 10)
            receipt.set_text_color(45, 52, 54)
            receipt.set_xy(55, movie_section_y + 15)
            receipt.cell(120, 6, f'{movie_obj.title}', 0, 1, 'L')
            
            receipt.set_font('Helvetica', '', 9)
            receipt.set_text_color(70, 70, 70)
            receipt.set_xy(55, movie_section_y + 22)
            receipt.cell(25, 5, 'Genre:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            if isinstance(format_genre(movie_obj.genre), list):
             genre_text = ", ".join(format_genre(movie_obj.genre))  # Convert list to comma-separated string
            else:
             genre_text = str(movie_obj.genre)  # Ensure it's a string
            receipt.cell(95, 5, genre_text, 0, 1, 'L')
            
            receipt.set_font('Helvetica', '', 9)
            receipt.set_xy(55, movie_section_y + 28)
            receipt.cell(25, 5, 'Movie ID:', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 9)
            receipt.cell(95, 5, f'{movie_obj.id}', 0, 1, 'L')
            
            # Modern pricing box with shadow effect
            try:
                price = float(movie_obj.price)
            except ValueError:
                price = 0.0
                
            # # Draw a light "shadow" rectangle slightly offset
            # receipt.set_fill_color(220, 220, 220)  # Light gray for shadow
            # receipt.rect(60, 155, 92, 25, 'F')
            
            # Draw the actual price box
            receipt.set_fill_color(231, 76, 60)  # Red accent
            receipt.rect(55, 150, 100, 25, 'F')
            
            receipt.set_font('Helvetica', 'B', 14)
            receipt.set_text_color(255, 255, 255)  # White text
            receipt.set_xy(55, 150)
            receipt.cell(70, 25, 'TOTAL AMOUNT', 0, 0, 'L')
            receipt.set_font('Helvetica', 'B', 16)
            receipt.cell(30, 25, f'${price:.2f}', 0, 1, 'R')
            
           
            
            # Thank you note with styled box
            receipt.set_fill_color(245, 245, 245)  # Very light gray
            receipt.rect(15, 190, 180, 30, 'F')
            receipt.set_font('Helvetica', 'B', 12)
            receipt.set_text_color(231, 76, 60)  # Red accent
            receipt.set_xy(15, 195)
            receipt.cell(180, 10, 'THANK YOU FOR CHOOSING MOVIE MART', 0, 1, 'C')
            
           
            
            # Save the receipt
            receipt_dir = os.path.join(current_app.root_path, 'Receipts')
            if not os.path.exists(receipt_dir):
                os.makedirs(receipt_dir, exist_ok=True)
            receipt_path = os.path.join(receipt_dir, f"receipt{order_obj.id}.pdf")
            receipt.output(receipt_path)
            
            # Send receipt by email
            try:
                send_mail(user_obj.email,"RECEIPT FOR MOVIE RENT","",receipt_path)
                flash("Receipt Generated Successfully and sent to your email.")
            except Exception as e:
                flash(f"Receipt generated but email sending failed: {str(e)}")
                
            return receipt_path
        else:
            flash("Missing order information for receipt generation", "error")
            return None
            
    except Exception as e:
        flash(f"Error generating receipt: {str(e)}", "error")
        print(f"Receipt generation error: {str(e)}")  # Log for debugging
        return None