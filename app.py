
from flask import (
    Flask, render_template_string, redirect,
    url_for, session, flash
)
import sqlite3

from patterns import FoodFactory, ComboDiscount, CheckoutFacade


app = Flask(__name__)
app.secret_key = "unicafe-demo-secret"

DB = "unicafe.db"


# ==================================================
# DATABASE MANAGEMENT
# ==================================================

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            category TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL,
            discount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS campus_card (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            balance REAL NOT NULL
        )
    """)

    # Factory Pattern: Create food objects
    foods = [
        FoodFactory.create_food(
            1, "Chicken Burger", 150, 20, "Fast Food"
        ),
        FoodFactory.create_food(
            2, "Pizza Slice", 120, 15, "Fast Food"
        ),
        FoodFactory.create_food(
            3, "Sandwich", 80, 25, "Snacks"
        ),
        FoodFactory.create_food(
            4, "Coffee", 50, 30, "Drinks"
        ),
        FoodFactory.create_food(
            5, "Fresh Juice", 70, 20, "Drinks"
        ),
        FoodFactory.create_food(
            6, "French Fries", 60, 18, "Snacks"
        )
    ]

    conn.executemany(
        "INSERT OR IGNORE INTO foods VALUES (?, ?, ?, ?, ?)",
        [food.to_tuple() for food in foods]
    )

    conn.execute("""
        INSERT OR IGNORE INTO campus_card (id, balance)
        VALUES (1, 1000)
    """)

    conn.commit()
    conn.close()


# ==================================================
# MENU MANAGEMENT
# ==================================================

def get_menu():
    conn = get_db()
    foods = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()
    return foods


# ==================================================
# SHOPPING CART AND DISCOUNT
# ==================================================

def calculate_bill(cart):
    menu = {
        food["id"]: food
        for food in get_menu()
    }

    subtotal = sum(
        menu[int(item_id)]["price"] * quantity
        for item_id, quantity in cart.items()
        if int(item_id) in menu
    )

    item_count = sum(cart.values())

    # Strategy Pattern: Combo discount strategy
    discount_strategy = ComboDiscount()
    discount = discount_strategy.calculate(
        subtotal, item_count
    )

    return subtotal, discount, subtotal - discount


def add_to_cart(food_id):
    menu = {
        food["id"]: food
        for food in get_menu()
    }

    food = menu.get(food_id)

    if not food or food["stock"] <= 0:
        return False

    cart = session.get("cart", {})
    key = str(food_id)

    current_quantity = cart.get(key, 0)

    if current_quantity >= food["stock"]:
        return False

    cart[key] = current_quantity + 1
    session["cart"] = cart

    return True


# ==================================================
# CHECKOUT AND PAYMENT
# ==================================================

def checkout_order():
    cart = session.get("cart", {})

    if not cart:
        return False, "Your cart is empty."

    conn = get_db()

    try:
        conn.execute("BEGIN IMMEDIATE")

        subtotal, discount, total = calculate_bill(cart)

        # Check inventory
        for item_id, quantity in cart.items():

            food = conn.execute(
                "SELECT stock FROM foods WHERE id = ?",
                (int(item_id),)
            ).fetchone()

            if not food or food["stock"] < quantity:
                raise ValueError(
                    "Insufficient stock for an item."
                )

        # Check campus card balance
        card = conn.execute(
            "SELECT balance FROM campus_card WHERE id = 1"
        ).fetchone()

        if not card or card["balance"] < total:
            raise ValueError(
                "Insufficient campus card balance."
            )

        # Process payment
        conn.execute(
            """
            UPDATE campus_card
            SET balance = balance - ?
            WHERE id = 1
            """,
            (total,)
        )

        # Update inventory
        for item_id, quantity in cart.items():

            conn.execute(
                """
                UPDATE foods
                SET stock = stock - ?
                WHERE id = ?
                """,
                (quantity, int(item_id))
            )

        # Save order
        cursor = conn.execute(
            """
            INSERT INTO orders (total, discount)
            VALUES (?, ?)
            """,
            (total, discount)
        )

        order_id = cursor.lastrowid

        conn.commit()

        session["cart"] = {}

        return True, (
            f"Order #{order_id} completed! "
            f"Paid Tk. {total:.2f}"
        )

    except ValueError as error:
        conn.rollback()
        return False, str(error)

    finally:
        conn.close()


# ==================================================
# WEBSITE DESIGN
# ==================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>UniCafe - Campus Food Ordering</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f5f9;
            color: #263238;
        }

        header {
            background: #263b50;
            color: white;
            padding: 22px 8%;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        main {
            max-width: 1100px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
        }

        .menu {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }

        .card, .cart {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px #ddd;
        }

        .card h3 {
            margin-top: 0;
        }

        button {
            background: #16866b;
            color: white;
            border: 0;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #11644f;
        }

        button:disabled {
            background: #999;
            cursor: not-allowed;
        }

        .remove {
            background: #d9534f;
            padding: 5px 10px;
        }

        .price {
            color: #16866b;
            font-weight: bold;
        }

        .muted {
            color: #777;
            font-size: 13px;
        }

        .message {
            background: #dff5e9;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .total {
            border-top: 1px solid #ddd;
            padding-top: 12px;
        }

        @media(max-width: 700px) {
            .layout {
                grid-template-columns: 1fr;
            }

            .menu {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>

<header>
    <div>
        <h2>🍔 UniCafé</h2>
        Campus Food Ordering System
    </div>

    <div>
        Campus Card: Tk. {{ "%.2f"|format(balance) }}
    </div>
</header>

<main>

    {% with messages = get_flashed_messages() %}
        {% for message in messages %}
            <div class="message">{{ message }}</div>
        {% endfor %}
    {% endwith %}

    <h2>Today's Menu</h2>

    <p class="muted">
        Fresh food, easy ordering, cashless payment.
    </p>

    <div class="layout">

        <section class="menu">

            {% for food in foods %}

            <div class="card">

                <h3>{{ food.name }}</h3>

                <p>{{ food.category }}</p>

                <p class="price">
                    Tk. {{ "%.2f"|format(food.price) }}
                </p>

                <p class="muted">
                    Available: {{ food.stock }}
                </p>

                <form action="/add/{{ food.id }}" method="POST">

                    <button
                        {% if food.stock == 0 %}disabled{% endif %}
                    >
                        Add to Cart +
                    </button>

                </form>

            </div>

            {% endfor %}

        </section>


        <aside class="cart">

            <h2>🛒 Your Cart</h2>

            {% if cart_items %}

                {% for item in cart_items %}

                <p>
                    {{ item.name }} × {{ item.quantity }}

                    <br>

                    <span class="price">
                        Tk. {{
                            "%.2f"|format(
                                item.price * item.quantity
                            )
                        }}
                    </span>

                    <form
                        action="/remove/{{ item.id }}"
                        method="POST"
                    >
                        <button class="remove">
                            Remove one
                        </button>
                    </form>
                </p>

                {% endfor %}

                <div class="total">

                    <p>
                        Subtotal:
                        Tk. {{ "%.2f"|format(subtotal) }}
                    </p>

                    <p>
                        Discount:
                        Tk. {{ "%.2f"|format(discount) }}
                    </p>

                    <h3>
                        Total:
                        Tk. {{ "%.2f"|format(total) }}
                    </h3>

                    {% if item_count >= 3 %}
                        <p class="muted">
                            10% combo discount applied!
                        </p>
                    {% endif %}

                    <form action="/checkout" method="POST">

                        <button>
                            Checkout & Pay
                        </button>

                    </form>

                </div>

            {% else %}

                <p class="muted">
                    Your cart is empty.
                </p>

            {% endif %}

        </aside>

    </div>

</main>

</body>
</html>
"""


# ==================================================
# FLASK ROUTES
# ==================================================

@app.route("/")
def home():

    foods = get_menu()

    cart = session.get("cart", {})

    menu = {
        food["id"]: food
        for food in foods
    }

    cart_items = []

    for item_id, quantity in cart.items():

        food = menu.get(int(item_id))

        if food:

            cart_items.append({
                "id": food["id"],
                "name": food["name"],
                "price": food["price"],
                "quantity": quantity
            })

    subtotal, discount, total = calculate_bill(cart)

    conn = get_db()

    balance = conn.execute(
        "SELECT balance FROM campus_card WHERE id = 1"
    ).fetchone()["balance"]

    conn.close()

    return render_template_string(
        HTML,
        foods=foods,
        cart_items=cart_items,
        subtotal=subtotal,
        discount=discount,
        total=total,
        balance=balance,
        item_count=sum(cart.values())
    )


@app.route("/add/<int:food_id>", methods=["POST"])
def add(food_id):

    if add_to_cart(food_id):
        flash("Item added to cart!")
    else:
        flash("Item unavailable or stock limit reached.")

    return redirect(url_for("home"))


@app.route("/remove/<int:food_id>", methods=["POST"])
def remove(food_id):

    cart = session.get("cart", {})
    key = str(food_id)

    if key in cart:

        cart[key] -= 1

        if cart[key] <= 0:
            del cart[key]

    session["cart"] = cart

    return redirect(url_for("home"))


@app.route("/checkout", methods=["POST"])
def checkout():

    # Facade Pattern: Single checkout interface
    checkout_facade = CheckoutFacade(checkout_order)

    success, message = checkout_facade.checkout()

    flash(message)

    return redirect(url_for("home"))


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
