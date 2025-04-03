# Video Rental System (VRS)

## Overview
Video Rental System (VRS) is an online portal that allows customers to rent  movies while enabling staff to manage inventory efficiently. The system provides a seamless experience for users to browse movies by genre and many features, add them to their cart, and proceed with rental. It also includes features for staff and managers to handle inventory, monitor due returns, and generate invoices.

## Features
### Customers:
- **User Authentication:** Login via  email.
- **Browse Movies:** View movies categorized by genre,price,rating and search by keywords.
- **Movie Details:** Access cast, crew, plot summaries, and similar movie recommendations.
- **Cart System:** Add movies to the cart and proceed to rent .
- **Billing & Invoicing:** Generate an invoice after transaction completion.
- **Crediting Money:** Increase balance by adding money into vrs account.
- **Customer Profiles:** View past orders , due dates for returns and remaining balance in this account.

### Staff:
- **Inventory Management:** Keep track of rented movies and ensure availability.
- **Due Monitoring:** Ensure customers return movies on time and notify them of dues.
- **Notifications:** Get alerts for low-stock movies.

### Managers:
- **Full Inventory Control:** Remove movies, change genres, and audit rented items.
- **:** Use data science to predict demand and manage stock.

## Technologies Used
- **Backend:** Flask-SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript 
- **Database:** SQLite
- **Authentication:** Flask-Login
- **PDF Invoices:** FPDF
- **Recommendation System (Future Scope):** TF-IDF & Cosine Similarity for personalized movie suggestions

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/bittu-sudo/vrs
   ```
2. Navigate to the project folder:
   ```sh
   cd vrs
   ```
3. Set up a virtual environment (optional but recommended):
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Run the application:
   ```sh
   python run.py
   ```

Thank you for choosing the   !

