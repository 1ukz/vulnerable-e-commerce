from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    make_response,
    session,
)
import base64, json
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "insecure-secret-key"

# In-memory carts and discounts, keyed by user_id
carts = defaultdict(list)
discounts = defaultdict(int)

products = [
    {
        "id": 1,
        "name": "Widget Pro",
        "price": 99.99,
        "desc": "High-end widget",
        "img": "https://via.placeholder.com/150",
    },
    {
        "id": 2,
        "name": "Gadget Plus",
        "price": 49.50,
        "desc": "Advanced gadget",
        "img": "https://via.placeholder.com/150",
    },
    {
        "id": 3,
        "name": "Doohickey XL",
        "price": 19.95,
        "desc": "Oversized doohickey",
        "img": "https://via.placeholder.com/150",
    },
    {
        "id": 4,
        "name": "Thingamajig Go",
        "price": 5.00,
        "desc": "Portable thingamajig",
        "img": "https://via.placeholder.com/150",
    },
]
user_names = {"1": "Lucas", "2": "Maria"}


@app.context_processor
def inject_globals():
    # Get user_id from URL path if available
    user_id_val = request.view_args.get("user_id", 1) if request.view_args else 1
    user_id_str = str(user_id_val)
    name = user_names.get(user_id_str, "Guest")
    cart_count = sum(i["quantity"] for i in carts[user_id_str])
    return {
        "current_user": name,
        "cart_count": cart_count,
        "current_user_id": user_id_val,
    }


@app.route("/")
def index():
    return redirect(url_for("shop", user_id=1))


@app.route("/set_user/<int:uid>")
def set_user(uid):
    return redirect(url_for("shop", user_id=uid))


@app.route("/user/<int:user_id>/shop")
def shop(user_id):
    # Clear cart and discount for this user on landing
    user_id_str = str(user_id)
    carts.pop(user_id_str, None)
    discounts.pop(user_id_str, None)
    return render_template("shop.html", products=products)


@app.route("/user/<int:user_id>/cart/add", methods=["POST"])
def add_to_cart(user_id):
    user_id_str = str(user_id)
    pid = int(request.form["product_id"])
    qty = int(request.form["quantity"])
    price = float(request.form["price"])
    carts[user_id_str].append({"product_id": pid, "quantity": qty, "price": price})
    return redirect(url_for("view_cart", user_id=user_id))


@app.route("/user/<int:user_id>/cart")
def view_cart(user_id):
    user_id_str = str(user_id)
    items = carts[user_id_str]
    total = sum(i["price"] * i["quantity"] for i in items)
    discount = discounts.get(user_id_str, 0)
    discounted_total = round(total * (1 - discount / 100), 2)
    return render_template(
        "cart.html",
        items=items,
        total=total,
        discounted_total=discounted_total,
        discount=discount,
        products=products,
    )


@app.route("/user/<int:user_id>/cart/remove/<int:index>")
def remove_item(user_id, index):
    user_id_str = str(user_id)
    if 0 <= index < len(carts[user_id_str]):
        carts[user_id_str].pop(index)
    return redirect(url_for("view_cart", user_id=user_id))


@app.route("/user/<int:user_id>/cart/clear")
def clear_cart(user_id):
    user_id_str = str(user_id)
    carts[user_id_str].clear()
    discounts.pop(user_id_str, None)
    return redirect(url_for("view_cart", user_id=user_id))


@app.route("/user/<int:user_id>/cart/apply", methods=["POST"])
def apply_discount(user_id):
    user_id_str = str(user_id)
    code = request.form.get("discount_code", "")
    try:
        disc = json.loads(base64.b64decode(code))["discount"]
    except:
        disc = 0
    discounts[user_id_str] = disc
    return redirect(url_for("view_cart", user_id=user_id))


@app.route("/user/<int:user_id>/checkout")
def checkout(user_id):
    user_id_str = str(user_id)
    total = sum(i["price"] * i["quantity"] for i in carts[user_id_str])
    discount = discounts.get(user_id_str, 0)
    final = round(total * (1 - discount / 100), 2)
    return render_template("payment.html", amount=final)


@app.route("/user/<int:user_id>/payment/submit", methods=["POST"])
def payment_submit(user_id):
    user_id_str = str(user_id)
    items = carts.get(user_id_str, [])
    total = sum(i["price"] * i["quantity"] for i in items)
    discount = discounts.get(user_id_str, 0)
    final_total = round(total * (1 - discount / 100), 2)
    return render_template("thanks.html", amount=final_total)


if __name__ == "__main__":
    app.run(host="0.0.0.0", ssl_context="adhoc", debug=True)
