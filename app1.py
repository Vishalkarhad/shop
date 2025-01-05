from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, ReturnDocument
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime


class admin:
    def __init(self):
        self.url = "mongodb+srv://vishal:12345@sharemart.qwglm.mongodb.net/?retryWrites=true&w=majority&appName=sharemart"
        self.client = MongoClient(url)
        self.db = client["clikkart"]
        
    def admin_login(self,userid,password):
        login=db.adminlogin.find_one()
        if login['userid']==userid and login['password']==password:
            return True
        else:
            return False
        
    

app = Flask(__name__)
app.secret_key = "your_secret_key"
# MongoDB connection
url = "mongodb+srv://vishal:12345@sharemart.qwglm.mongodb.net/?retryWrites=true&w=majority&appName=sharemart"
client = MongoClient(url)
db = client["clikkart"]
v=admin()

# Counters collection for user IDs
if not db.counters.find_one({"_id": "user_id"}):
    db.counters.insert_one({"_id": "user_id", "seq": 0})

if not db.counters.find_one({"_id": "p_id"}):
    db.counters.insert_one({"_id": "p_id", "seq": 0})

def get_next_sequence(name):
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        return_document=ReturnDocument.AFTER
    )
    return counter["seq"]


@app.route("/")
def home():
    products=db.product_list.find()
    return render_template("index.html",products=products)

@app.route('/adminlogin')
def adminpage():
    return render_template('adminlogin.html')

@app.route('/adminpanel',methods=['POST'])
def adminvsk():
    userid1= request.form["userid"]
    password1= request.form["password"]
    if v.admin_login(userid1,password1)==True:
        return render_template('/adminpanel.html')
    else:
        return False
@app.route('/product_add',methods=['POST'])
def product_add():
    p_name=request.form['product_name']
    p_url=request.form['image_url']
    p_price=request.form['price']
    p_cat=request.form['category']
    p_id = get_next_sequence("p_id")
    db.product_list.insert_one({'product_id':p_id,
                                'product_name':p_name,
                                'product_url':p_url,
                                'product_price':p_price,
                                'product_cat':p_cat})
    flash("product add succefully",'danger')
    return render_template('adminpanel.html')

@app.route("/signup")
def signup_form():
    return render_template("signup.html")


@app.route("/si", methods=["POST"])
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
        "password": password,
    }
    db.users.insert_one(user)
    return jsonify({"status": "success", "message": "User registered successfully!", "user_id": user_id})


@app.route("/login")
def login_form():
    return render_template("login.html")


@app.route("/login1", methods=["POST"])
def login():
    mobile = request.form.get("mobile")
    password = request.form.get("password")

    user = db.users.find_one({"mobile_no": mobile})
    if user and user["password"]== password:
        session["user_id"] = user["user_id"]
        flash("Login successful!", "success")
        return redirect(url_for("home"))
    else:
        flash("Invalid mobile number or password.", "danger")
        return redirect(url_for("login_form"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Please log in to add items to the cart."}), 401

    data = request.get_json()
    producturl = data.get("producturl")
    product_name = data.get("productName")
    price = data.get("price")

    if product_name and price:
        db.cart.update_one(
            {"user_id": session["user_id"]},
            {"$push": {"items": {"producturl":producturl, "product_name": product_name, "price": price}}},
            upsert=True
        )
            
        
        
        return jsonify({"status": "success", "message": f"{product_name} added to cart successfully!"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid product details."}), 400


@app.route("/cart", methods=["GET"])
def view_cart():
    if "user_id" not in session:
        flash("Please log in to view your cart.", "warning")
        return redirect(url_for("login_form"))

    cart_list = db.cart.find({"user_id": session["user_id"]})
    
    cart1=[]
    total_price=0
    for i in cart_list:
        for n in range(0,len(i['items'])):
            cart1.append([i['items'][n]['producturl'],i['items'][n]['product_name'],i['items'][n]['price']])
            total_price +=i['items'][n]['price']
            # , cart=cart1,total_price=total_price
    return render_template("cart1.html", cart=cart1,total_price=total_price)

@app.route("/remove-item", methods=["POST"])
def remove_item():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Please log in."}), 401

    data = request.get_json()
    product_name = data.get("product_name")
    user_id = session["user_id"]

    # Remove the item from the user's cart
    db.cart.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_name": product_name}}}
    )

    return jsonify({"status": "success", "message": "Item removed successfully."}), 200


@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Please log in to complete the payment."}), 401

    # Mock payment verification logic (replace with actual payment gateway integration)
    payment_data = request.get_json()
    payment_status = payment_data.get("status", "failed")

    if payment_status == "success":
        # Retrieve the cart items for the user
        user_id = session["user_id"]
        user_cart = db.cart.find_one({"user_id": user_id})

        if not user_cart or not user_cart.get("items"):
            return jsonify({"status": "error", "message": "Cart is empty. Add items to checkout."}), 400

        # Move cart items to the completed_orders collection
        completed_order = {
            "user_id": user_id,
            "items": user_cart["items"],
            "payment_status": "success",
            "payment_details": payment_data,  # Store additional payment details if available
            "order_date": datetime.utcnow()
        }
        db.completed_orders.insert_one(completed_order)

        # Empty the user's cart
        db.cart.update_one({"user_id": user_id}, {"$set": {"items": []}})

        return jsonify({"status": "success", "message": "Payment successful. Order placed!"}), 200
    else:
        return jsonify({"status": "error", "message": "Payment failed. Please try again."}), 400


@app.route("/check-referral", methods=["POST"])
def check_referral():
    data = request.json
    referral_code = data.get("referral_code")

    if not referral_code:
        return jsonify({"valid": False, "message": "Referral code cannot be empty"}), 400

    referral = db.referal_code_table.find_one({"code": referral_code})
    if referral and referral.get("is_valid", False):
        
        return jsonify({
            "valid": True,
            "message": f"Referral code {referral_code} is valid!",
            "message2": f" your minimun buying price is :{referral['sharing_price']}",
        })
    else:
        return jsonify({"valid": False, "message": "Invalid referral code."}), 400


@app.route("/pay-now", methods=["POST"])
def pay_now():
    if "user_id" not in session:
        flash("Please log in to proceed with payment.", "warning")
        return redirect(url_for("login_form"))

    # Clear the cart after payment
    db.cart.delete_many({"user_id": session["user_id"]})
    flash("Payment successful! Your cart has been cleared.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
