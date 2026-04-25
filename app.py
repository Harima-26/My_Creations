import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------- Database Connection ----------------
def get_db():
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Home / Products ----------------
@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("index.html", products=products)

# ---------------- User Register ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                       (name, email, password))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# ---------------- User Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["cart"] = []  # initialize cart
            return redirect("/")
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- Add to Cart ----------------
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        return redirect("/")

    # check if already in cart
    for item in session["cart"]:
        if item["product_id"] == product_id:
            item["quantity"] += 1
            item["subtotal"] = item["quantity"] * item["price"]
            break
    else:
        session["cart"].append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": 1,
            "subtotal": product["price"]
        })

    session.modified = True
    return redirect("/cart")


# ---------------- Cart Page ----------------
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cart_items = []
    total = 0
    cart = session.get("cart", [])

    for item in cart:
        cursor.execute("SELECT * FROM products WHERE id=?", (item["product_id"],))
        product = cursor.fetchone()
        if product:
            subtotal = product["price"] * item["quantity"]
            total += subtotal
            cart_items.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": item["quantity"],
                "subtotal": subtotal
            })

    conn.close()
    return render_template("cart.html", cart_items=cart_items, total=total)

# ---------------- Place Order ----------------
@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    cart = session.get("cart", [])
    if not cart:
        return redirect("/cart")

    conn = get_db()
    cursor = conn.cursor()

    for item in cart:
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, quantity, price, total, payment_mode, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            item["product_id"],
            item["quantity"],
            item["price"],
            item["subtotal"],
            "COD",     # default
            "Pending"
        ))

        cursor.execute("UPDATE products SET stock = stock - ? WHERE id=?",
                       (item["quantity"], item["product_id"]))

    conn.commit()
    conn.close()
    session["cart"] = []  # clear cart

    return redirect("/orders")




# ---------------- User Orders ----------------
@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, p.name, o.quantity, p.price, (o.quantity * p.price) AS total
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id=?
    """, (session["user_id"],))
    orders = cursor.fetchall()
    conn.close()

    return render_template("orders.html", orders=orders)

# ---------------- Admin Login ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin_user = cursor.fetchone()
        conn.close()

        if admin_user:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return "Invalid Admin Credentials"
    return render_template("admin_login.html")

# ---------------- Admin Dashboard ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", products=products)

# ---------------- Admin Add Product ----------------
@app.route("/admin/add", methods=["GET", "POST"])
def add_product():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", 
                       (name, price, stock))
        conn.commit()
        conn.close()
        return redirect("/admin/dashboard")
    return render_template("add_product.html")

# ---------------- Admin Orders ----------------
@app.route("/admin/orders")
def admin_orders():
    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT o.id as order_id, u.name as user_name, 
                             p.name as product_name, o.quantity, o.price, o.total, 
                             o.payment_mode, o.payment_status
                      FROM orders o
                      JOIN users u ON o.user_id = u.id
                      JOIN products p ON o.product_id = p.id
                      ORDER BY o.id DESC""")
    orders = [dict(order_id=row[0], user_name=row[1], product_name=row[2],
                   quantity=row[3], price=row[4], total=row[5],
                   payment_mode=row[6], payment_status=row[7])
              for row in cursor.fetchall()]
    conn.close()

    return render_template("admin_orders.html", orders=orders)

@app.route('/admin/users')
def admin_users():
    conn = sqlite3.connect('grocery.db')
    conn.row_factory = sqlite3.Row  # so we can access columns by name
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email FROM users")  # your users table
    users = cursor.fetchall()

    conn.close()
    return render_template('admin_users.html', users=users)
    
@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    conn = sqlite3.connect('grocery.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form.get('password')  # optional

        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("UPDATE users SET name=?, email=?, password=? WHERE id=?", (name, email, password_hash, id))
        else:
            cursor.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, id))
        conn.commit()
        conn.close()
        return redirect('/admin/users')

    cursor.execute("SELECT id, name, email FROM users WHERE id=?", (id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    conn = sqlite3.connect('grocery.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/users')

   
if __name__ == "__main__":
    app.run(debug=True)
