# Pawfect

Pawfect is a pet-supplies e-commerce web application built for customers and store administrators. Customers can browse food, toys, medicines, and grooming products; manage a cart; and complete purchases through Razorpay. Administrators can manage products, stock, and orders from a dedicated dashboard.

## Features

- Customer and administrator registration and login
- Product categories for food, toys, medicines, and grooming
- Product browsing and shopping-cart management
- Razorpay payment order creation and signature verification
- Admin dashboard to add, delete, and update product stock
- Order history and inventory tracking
- Image uploads for products

## Tech stack

- **Backend:** Python, Flask
- **Database:** MongoDB with PyMongo
- **Authentication:** Flask sessions and Flask-Bcrypt
- **Payments:** Razorpay
- **Frontend:** HTML, CSS, JavaScript, and Jinja templates

## Prerequisites

- Python 3.10 or newer
- MongoDB running locally on port `27017`
- A Razorpay test account and API keys for checkout testing

## Installation

1. Clone the repository and open its folder:

   ```bash
   git clone <your-repository-url>
   cd pawfect
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt razorpay
   ```

4. Set Razorpay test credentials before starting the application:

   ```powershell
   $env:RAZORPAY_KEY_ID="your_test_key_id"
   $env:RAZORPAY_KEY_SECRET="your_test_key_secret"
   ```

5. Start MongoDB, then run the application:

   ```bash
   python app.py
   ```

6. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Usage

- Register a **user** account to browse products and use the cart.
- Register an **administrator** account to add products, update stock, and review orders.
- Use Razorpay **test mode** credentials and test payment methods during development.

## Security note

Do not commit real Razorpay keys, Flask secret keys, database passwords, or uploaded private files to GitHub. Store credentials in environment variables or a local `.env` file that is excluded through `.gitignore`.

