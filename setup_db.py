import sqlite3

conn = sqlite3.connect("grocery.db")
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)
""")

# Products table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    stock INTEGER
)
""")

# Orders table (with payment details added)
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    total REAL,
    payment_mode TEXT,
    payment_status TEXT
)''')


# Admin table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# Default admin
cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))

# Sample products
products = [
    ("Apple", 50.0, 20),
    ("Banana", 10.0, 50),
    ("Milk", 40.0, 30),
    ("Bread", 30.0, 25)
]
for name, price, stock in products:
    cursor.execute("INSERT OR IGNORE INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))

conn.commit()
conn.close()
print("✅ Database setup complete with default admin and sample products")
