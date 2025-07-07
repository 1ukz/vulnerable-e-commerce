from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    render_template,
    make_response,
    session,
)
import base64, json, zlib
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "insecure-secret-key"  # required for session

# In-memory carts, keyed by user_id cookie
carts = defaultdict(list)

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


def get_user_id():
    return request.cookies.get("user_id")


@app.route("/set_user/<int:uid>")
def set_user(uid):
    resp = make_response(redirect(url_for("shop")))
    resp.set_cookie("user_id", str(uid))  # session-cookie
    return resp


@app.context_processor
def inject_globals():
    uid = get_user_id() or "1"
    name = user_names.get(uid, "Guest")
    cart_count = sum(i["quantity"] for i in carts[uid])
    # return both current_user and cart_count
    return {"current_user": name, "cart_count": cart_count}


@app.route("/")
def shop():
    # reset everything on landing
    uid = get_user_id()
    if not uid:
        return redirect(url_for("set_user", uid=1))
    carts.pop(uid, None)
    session.pop("discount", None)
    return render_template("shop.html", products=products)


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    uid = get_user_id()
    pid = int(request.form["product_id"])
    qty = int(request.form["quantity"])
    price = float(request.form["price"])
    carts[uid].append({"product_id": pid, "quantity": qty, "price": price})
    return redirect(url_for("view_cart"))


@app.route("/cart")
def view_cart():
    uid = get_user_id()
    items = carts[uid]
    total = sum(i["price"] * i["quantity"] for i in items)
    discount = session.get("discount", 0)  # stored in session
    discounted_total = round(total * (1 - discount / 100), 2)
    return render_template(
        "cart.html",
        items=items,
        total=total,
        discounted_total=discounted_total,
        discount=discount,
        products=products,
    )


@app.route("/cart/remove/<int:index>")
def remove_item(index):
    uid = get_user_id()
    if 0 <= index < len(carts[uid]):
        carts[uid].pop(index)
    return redirect(url_for("view_cart"))


@app.route("/cart/clear")
def clear_cart():
    uid = get_user_id()
    carts[uid].clear()
    session.pop("discount", None)
    return redirect(url_for("view_cart"))


@app.route("/cart/apply", methods=["POST"])
def apply_discount():
    code = request.form.get("discount_code", "")
    try:
        disc = json.loads(base64.b64decode(code))["discount"]
    except:
        disc = 0
    session["discount"] = disc
    return redirect(url_for("view_cart"))


@app.route("/checkout")
def checkout():
    uid = get_user_id()
    total = sum(i["price"] * i["quantity"] for i in carts[uid])
    discount = session.get("discount", 0)
    final = round(total * (1 - discount / 100), 2)
    return render_template("payment.html", amount=final)


@app.route("/payment/submit", methods=["POST"])
def payment_submit():
    uid = get_user_id()
    # recompute the cart total & discount just like in checkout
    items = carts.get(uid, [])
    total = sum(i["price"] * i["quantity"] for i in items)
    discount = session.get("discount", 0)
    final_total = round(total * (1 - discount / 100), 2)

    # now render the template with the final_total
    return render_template("thanks.html", amount=final_total)


if __name__ == "__main__":
    app.run(host="0.0.0.0", ssl_context="adhoc", debug=True)
