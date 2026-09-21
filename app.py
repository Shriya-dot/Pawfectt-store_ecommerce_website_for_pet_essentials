from flask import (
    Flask, render_template, request, redirect,
    session, url_for, jsonify, flash, send_from_directory
)
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime
import os
import razorpay

app = Flask(__name__)
app.secret_key = "my_flask_secret_key_123"
bcrypt = Bcrypt(app)

# ------------------ FILE UPLOAD CONFIG ------------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------ DATABASE CONNECTION ------------------
client = MongoClient("mongodb://localhost:27017")
db = client.Ecommerce
users_collection = db.users
admins_collection = db.admins
products_collection = db.products
cart_collection = db.cart
payments_collection = db.payments

# ------------------ RAZORPAY CONFIG ------------------
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_RZg4oKKQesYGY9")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "oHz1rMLIg5k7z72hQvLMomTu")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template('user_dashboard.html')

# ------------------ LOGIN SELECTOR ------------------
@app.route('/login1')
def login1():
    return render_template('login1.html')

# ------------------ USER REGISTRATION ------------------
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return "Passwords do not match!"
        if users_collection.find_one({'email': email}):
            return "Email already exists!"

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })
        return redirect('/login_user')

    return render_template('register_user.html')

# ------------------ USER LOGIN ------------------
@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_email'] = user['email']
            session['user_name'] = user['username']
            return redirect(url_for('user_dashboard'))
        else:
            return "Invalid email or password!"

    return render_template('login_user.html')

# ------------------ USER DASHBOARD ------------------
@app.route('/user_dashboard')
def user_dashboard():
    username = session.get('user_name')
    return render_template('user_dashboard.html', username=username)

# ------------------ STORE CATEGORY ROUTES ------------------

@app.route('/toys')
def toys():
    products = db.products.find({"category": "toys"})
    return render_template('toys.html', products=products)

@app.route('/medicines')
def medicines():
    products = db.products.find({"category": "medicines"})
    return render_template('medicines.html', products=products)

@app.route('/groom')
def groom():
    products = db.products.find({"category": "groom"})
    return render_template('groom.html', products=products)

@app.route('/food')
def food():
    products = db.products.find({"category": "food"})
    return render_template('food.html', products=products)


# ------------------ CART ROUTES ------------------
@app.route('/cart')
def cart():
    username = session.get('user_name')
    user_email = session.get('user_email')
    items = []
    total = 0

    if user_email:
        items = list(cart_collection.find({'user_email': user_email}))
        total = sum(item['price'] * item['quantity'] for item in items)

    return render_template(
        'cart.html',
        username=username,
        cart_items=items,
        total=total,
        razorpay_key_id=RAZORPAY_KEY_ID
    )

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_email' not in session:
        return redirect('/login_user')

    user_email = session['user_email']
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    product = products_collection.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    existing = cart_collection.find_one({'user_email': user_email, 'product_id': product_id})
    if existing:
        cart_collection.update_one({'_id': existing['_id']}, {'$inc': {'quantity': quantity}})
    else:
        cart_collection.insert_one({
            'user_email': user_email,
            'product_id': product_id,
            'product_name': product['name'],
            'price': product['price'],
            'img': product.get('img', ''),
            'quantity': quantity
        })

    return jsonify({'success': True, 'message': 'Added to cart successfully!'})

@app.route('/remove_from_cart/<cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'user_email' not in session:
        return redirect('/login_user')

    cart_collection.delete_one({'_id': ObjectId(cart_id)})
    flash('Item removed from cart', 'info')
    return redirect('/cart')

# ------------------ ADMIN ROUTES ------------------
@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return "Passwords do not match!"
        if admins_collection.find_one({'email': email}):
            return "Admin already exists!"

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admins_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })
        return redirect('/login_admin')

    return render_template('register_admin.html')

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = admins_collection.find_one({'email': email})
        if admin and bcrypt.check_password_hash(admin['password'], password):
            session['admin_email'] = admin['email']
            session['admin_name'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials!"

    return render_template('login_admin.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_name' not in session:
        return redirect('/login_admin')
    return render_template('admin_dashboard.html', username=session['admin_name'])

@app.route('/admin_order')
def admin_order():
    if 'admin_name' not in session:
        return redirect('/login_admin')

    orders = list(payments_collection.find())
    return render_template('admin_order.html', username=session['admin_name'], orders=orders)

# ------------------ ADMIN PRODUCT MGMT ------------------
@app.route('/admin/add_product', methods=['POST'])
def admin_add_product():
    if 'admin_name' not in session:
        return redirect('/login_admin')

    name = request.form.get('name')
    category = request.form.get('category', '').lower()
    price = float(request.form.get('price', 0))
    stock = int(request.form.get('stock', 0))
    description = request.form.get('description', '')
    img_file = request.files.get('img')

    if img_file and img_file.filename:
        filename = img_file.filename
        save_dir = os.path.join(app.static_folder, 'images')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        img_file.save(save_path)
        img_path = filename  # ✅ Store full relative path
    else:
        img_path = "default.png"  # ✅ Default image fallback


    products_collection.insert_one({
        'name': name,
        'category': category,
        'price': price,
        'stock': stock,
        'description': description,
        'img': img_path
    })
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/get_products', methods=['GET'])
def admin_get_products():
    if 'admin_name' not in session:
        return redirect('/login_admin')

    docs = list(products_collection.find())
    for d in docs:
        d['_id'] = str(d['_id'])
    return jsonify(docs)

@app.route('/admin/get_orders', methods=['GET'])
def admin_get_orders():
    if 'admin_name' not in session:
        return redirect('/login_admin')

    orders = list(payments_collection.find())
    for o in orders:
        o['_id'] = str(o['_id'])
        o['order_date'] = o.get('order_date', '')
        o['payment_method'] = 'Razorpay'
        o['status'] = o.get('status', 'Pending').capitalize()
        o['total_amount'] = round(o.get('total_amount', 0), 2)

    return jsonify(orders)


@app.route('/get_products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    query = {}
    if category:
        query['category'] = category.lower()

    docs = list(products_collection.find(query))
    for d in docs:
        d['_id'] = str(d['_id'])
    return jsonify(docs)

@app.route('/admin/update_stock/<product_id>', methods=['POST'])
def admin_update_stock(product_id):
    if 'admin_name' not in session:
        return redirect('/login_admin')

    try:
        stock = int(request.form['stock'])
    except:
        return "Invalid stock value", 400

    products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': {'stock': stock}})
    flash('Stock updated successfully!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<product_id>', methods=['DELETE', 'POST'])
def admin_delete_product(product_id):
    if 'admin_name' not in session:
        return redirect('/login_admin')

    products_collection.delete_one({'_id': ObjectId(product_id)})

    if request.method == 'DELETE' or request.is_json:
        return jsonify({'status': 'ok', 'msg': 'Deleted'})

    flash('Product deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))

# ------------------ RAZORPAY PAYMENT ROUTES ------------------
@app.route("/create_order", methods=["POST"])
def create_order():
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 403

    data = request.get_json()
    try:
        amount_in_inr = float(data.get("amount", 0))
        if amount_in_inr <= 0:
            return jsonify({"error": "Invalid amount value"}), 400
    except Exception as e:
        print("⚠️ Invalid amount data:", e)
        return jsonify({"error": "Invalid amount"}), 400

    amount_in_paise = int(amount_in_inr * 100)
    print(f"🪙 Attempting Razorpay order creation for ₹{amount_in_inr} ({amount_in_paise} paise)")

    try:
        order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1"
        })
        print("✅ Razorpay Order Created:", order)
    except Exception as e:
        print("❌ Razorpay order creation failed:", str(e))
        return jsonify({
            "error": "Failed to create Razorpay order",
            "details": str(e)
        }), 500

    # ✅ Save payment info only if order created successfully
    try:
        payments_collection.insert_one({
            "order_id": order.get("id"),
            "user_email": session["user_email"],
            "amount": amount_in_paise,
            "status": "created",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print("⚠️ Failed to save payment record:", e)

    return jsonify(order)


# ------------------ ✅ UPDATED VERIFY PAYMENT ------------------
@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    payload = request.get_json()
    if not payload:
        return jsonify({"verified": False, "message": "Invalid data"}), 400

    try:
        # ✅ Verify Razorpay signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': payload.get("razorpay_order_id"),
            'razorpay_payment_id': payload.get("razorpay_payment_id"),
            'razorpay_signature': payload.get("razorpay_signature")
        })
    except razorpay.errors.SignatureVerificationError:
        payments_collection.update_one(
            {'order_id': payload.get("razorpay_order_id")},
            {'$set': {'status': 'failed'}}
        )
        return jsonify({
            'verified': False,
            'status': 'failed',
            'message': 'Signature verification failed'
        }), 400

    # ✅ Payment successful
    cart_items = payload.get("cart", [])
    user_email = session.get("user_email")
    user_name = session.get("user_name")

    if not user_email:
        return jsonify({"verified": False, "message": "User not logged in"}), 403

    if cart_items:
        # ✅ Create detailed list of purchased items
        item_list = []
        for item in cart_items:
            # Handle all possible key variations for product name
            product_name = (
                item.get('product_name') or
                item.get('name') or
                item.get('title') or
                item.get('product') or
                'Unnamed Product'
            )

            item_list.append({
                'product_name': product_name,
                'price': float(item.get('price', 0)),
                'quantity': int(item.get('quantity', 1))
            })

        total_price = sum(i['price'] * i['quantity'] for i in item_list)

        # ✅ Store order details in payments collection
        payments_collection.update_one(
            {'order_id': payload.get("razorpay_order_id")},
            {'$set': {
                'user_name': user_name,
                'user_email': user_email,
                'items': item_list,
                'total_amount': total_price,
                'payment_id': payload.get("razorpay_payment_id"),
                'status': 'paid',
                'order_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }},
            upsert=True  # ensures it creates if not found
        )

        # ✅ Reduce stock count in products collection
        for item in item_list:
            products_collection.update_one(
                {'name': item['product_name']},
                {'$inc': {'stock': -item['quantity']}}
            )

        # ✅ Clear user’s cart after payment
        cart_collection.delete_many({'user_email': user_email})

    else:
        print("⚠️ No cart data received from frontend!")

    return jsonify({
        'verified': True,
        'status': 'paid',
        'message': 'Payment verified successfully'
    })

# ------------------ CHECKOUT ------------------
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_name' not in session:
        return redirect('/login_user')

    user_email = session['user_email']
    username = session['user_name']
    cart_items = list(cart_collection.find({'user_email': user_email}))

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect('/cart')

    for item in cart_items:
        product = products_collection.find_one({'_id': ObjectId(item['product_id'])})
        if product and product['stock'] >= item['quantity']:
            total_price = item['quantity'] * product['price']
            payments_collection.insert_one({
                'user_email': user_email,
                'user_name': username,
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'quantity': item['quantity'],
                'total_price': total_price,
                'status': 'Completed'
            })
            products_collection.update_one(
                {'_id': ObjectId(item['product_id'])},
                {'$inc': {'stock': -item['quantity']}}
            )

    cart_collection.delete_many({'user_email': user_email})
    flash('Order placed successfully!', 'success')
    return redirect('/user_dashboard')

# ------------------ FILE SERVE ------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user_dashboard'))

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
