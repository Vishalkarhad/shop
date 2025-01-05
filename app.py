from flask import Flask,render_template,request,url_for,session,redirect,url_for,flash,jsonify
from pymongo import MongoClient, ReturnDocument
from werkzeug.security import check_password_hash
import base64
import random
import string
import secrets

#this is a flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"
url="mongodb+srv://vishal:12345@sharemart.qwglm.mongodb.net/?retryWrites=true&w=majority&appName=sharemart"
client=MongoClient(url)
db=client['clikkart']
cart_data = []
code=[None,0]

if not db.counters.find_one({"_id": "user_id"}):
    db.counters.insert_one({"_id": "user_id", "seq": 0})

def get_next_sequence(name):
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        return_document=ReturnDocument.AFTER
    )
    return counter["seq"]

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/signup")
def signup_form():
    return render_template("signup.html")

@app.route('/si',methods=['POST'])
def signup():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    mobile_no = request.form["mobile_no"]
    password = request.form["password"]
    if db.users.find_one({"mobile_no": mobile_no}):
        return jsonify({"status": "error", "message": "Mobile number already registered."})
    user_id = get_next_sequence("user_id")
    user = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "mobile_no": mobile_no,
        "password": password
    }

    # Insert the new user into the users collection
    db.users.insert_one(user)
    return jsonify({"status": "success", "message": "User registered successfully!", "user_id": user_id})

@app.route("/login")    
def login():
    return render_template('login.html')

@app.route("/login1", methods=["GET", "POST"])
def login1():
    if request.method == "POST":
        mobile = request.form.get("mobile")
        password = request.form.get("password")

        # Check if user exists
        user = db.users.find_one({"mobile_no": mobile})
        if user:
            # Verify password
            if user["password"]== password:
                session['user_id'] = str(user['_id'])
                flash("Login successful!", "success")
                return redirect(url_for("login"))
            else:
                flash("Invalid password.", "danger")
        else:
            flash("User not found.", "danger")

        return redirect(url_for("login"))

    return render_template("login.html")


    

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    global cart
    data = request.get_json()
    product_name = data.get('productName')
    price = data.get('price')

    if product_name and price:
        # Add product to the cart
        cart_data.append({'productName': product_name, 'price': price})
        return jsonify({'message': f'{product_name} added to cart successfully!'}), 200
    else:
        return jsonify({'message': 'Invalid product details.'}), 400

@app.route('/cart', methods=['GET'])
def view_cart():
    return render_template("cart.html",cart=cart_data,code=code ),200


@app.route('/check-referral', methods=['POST'])
def check_referral():
    data = request.json
    referral_code = data.get('referral_code')

    if not referral_code:
        return jsonify({'valid': False, 'message': 'Referral code cannot be empty'}), 400

    referral = db.referal_code_table.find_one({'code': referral_code,
                                               
                                               })
    if referral and referral.get('is_valid', False):
        code[0]=referral_code
        code[1]=referral['sharing_price']
        return jsonify({'valid': True, 'message': f'Your referral code is {referral_code} valid!','message2':f"your minimun buying price is {referral['sharing_price']}"})
    else:
        return jsonify({'valid': False, 'message': 'Invalid referral code.'})
# Define another route


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
