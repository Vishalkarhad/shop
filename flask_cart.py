from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["shopping_cart"]
cart_collection = db["cart"]
users_collection = db["users"]

@app.route('/')
def home():
    cart_items = list(cart_collection.find())
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('index.html', cart=cart_items, total_price=total_price)

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.json
    product_id = data.get('id')
    action = data.get('action')

    # Update the product quantity in the database
    item = cart_collection.find_one({"id": product_id})
    if item:
        new_quantity = item['quantity'] + 1 if action == 'increase' else max(0, item['quantity'] - 1)
        cart_collection.update_one({"id": product_id}, {"$set": {"quantity": new_quantity}})
    return jsonify({"success": True})

@app.route('/remove-item', methods=['POST'])
def remove_item():
    data = request.json
    product_id = data.get('id')

    # Remove the item from the database
    cart_collection.delete_one({"id": product_id})
    return jsonify({"success": True})

@app.route('/remove-all', methods=['POST'])
def remove_all():
    cart_collection.delete_many({})
    return jsonify({"success": True})

@app.route('/pay-now', methods=['POST'])
def pay_now():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Proceed with payment logic
    cart_collection.delete_many({})
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('home'))
        return "Invalid username or password", 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if users_collection.find_one({"username": username}):
            return "Username already exists", 400

        users_collection.insert_one({"username": username, "password": password})
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
