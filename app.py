
import sqlite3
from datetime import date, timedelta
from functools import wraps
from flask import Flask, g, request, redirect, session, render_template, flash
from jinja2 import DictLoader
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret"
DB = "pharmacy.db"


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT);
    CREATE TABLE IF NOT EXISTS medicines(id INTEGER PRIMARY KEY, name TEXT, category TEXT,
        price REAL, stock INTEGER, expiry TEXT);
    CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, customer TEXT, total REAL, date TEXT);
    CREATE TABLE IF NOT EXISTS sale_items(id INTEGER PRIMARY KEY, sale_id INTEGER,
        medicine_id INTEGER, qty INTEGER, price REAL);""")
    if not c.execute("SELECT 1 FROM users").fetchone():
        c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                  ("admin", generate_password_hash("admin123")))
    c.commit()
    c.close()


def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if "user" not in session:
            return redirect("/login")
        return f(*a, **k)
    return wrap


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        if u and check_password_hash(u["password"], request.form["password"]):
            session["user"] = u["username"]
            return redirect("/")
        flash("Wrong username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def dashboard():
    d, today = db(), date.today()
    soon = (today + timedelta(days=30)).isoformat()
    return render_template(
        "dashboard.html",
        total=d.execute("SELECT COUNT(*) FROM medicines").fetchone()[0],
        low=d.execute("SELECT * FROM medicines WHERE stock<10").fetchall(),
        soon=d.execute("SELECT * FROM medicines WHERE expiry BETWEEN ? AND ?",
                       (today.isoformat(), soon)).fetchall(),
        expired=d.execute("SELECT * FROM medicines WHERE expiry<?", (today.isoformat(),)).fetchall(),
        sales=d.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date=?",
                        (today.isoformat(),)).fetchone()[0])


@app.route("/medicines")
@login_required
def medicines():
    q = "%" + request.args.get("q", "") + "%"
    rows = db().execute("SELECT * FROM medicines WHERE name LIKE ? OR category LIKE ?", (q, q)).fetchall()
    return render_template("medicines.html", rows=rows)


@app.route("/medicines/add", methods=["GET", "POST"])
@app.route("/medicines/<int:mid>/edit", methods=["GET", "POST"])
@login_required
def medicine_form(mid=None):
    d = db()
    m = d.execute("SELECT * FROM medicines WHERE id=?", (mid,)).fetchone() if mid else None
    if request.method == "POST":
        f = request.form
        vals = (f["name"], f["category"], float(f["price"]), int(f["stock"]), f["expiry"])
        if mid:
            d.execute("UPDATE medicines SET name=?,category=?,price=?,stock=?,expiry=? WHERE id=?", vals + (mid,))
        else:
            d.execute("INSERT INTO medicines(name,category,price,stock,expiry) VALUES(?,?,?,?,?)", vals)
        d.commit()
        flash("Saved successfully")
        return redirect("/medicines")
    return render_template("form.html", m=m)


@app.route("/medicines/<int:mid>/delete", methods=["POST"])
@login_required
def delete(mid):
    db().execute("DELETE FROM medicines WHERE id=?", (mid,))
    db().commit()
    return redirect("/medicines")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    d = db()
    meds = d.execute("SELECT * FROM medicines WHERE stock>0 AND expiry>=?",
                     (date.today().isoformat(),)).fetchall()
    if request.method == "POST":
        items, total = [], 0
        for m in meds:
            qty = int(request.form.get(f"qty_{m['id']}") or 0)
            if qty > m["stock"]:
                flash(f"Not enough stock for {m['name']}")
                return redirect("/sell")
            if qty > 0:
                items.append((m, qty))
                total += qty * m["price"]
        if not items:
            flash("Select at least one medicine")
            return redirect("/sell")
        sid = d.execute("INSERT INTO sales(customer,total,date) VALUES(?,?,?)",
                        (request.form["customer"] or "Walk-in", total, date.today().isoformat())).lastrowid
        for m, qty in items:
            d.execute("INSERT INTO sale_items(sale_id,medicine_id,qty,price) VALUES(?,?,?,?)",
                      (sid, m["id"], qty, m["price"]))
            d.execute("UPDATE medicines SET stock=stock-? WHERE id=?", (qty, m["id"]))
        d.commit()
        flash(f"Sale completed. Total bill: {total:.2f} Tk")
        return redirect("/sales")
    return render_template("sell.html", meds=meds)


@app.route("/sales")
@login_required
def sales():
    return render_template("sales.html", rows=db().execute("SELECT * FROM sales ORDER BY id DESC").fetchall())


# ---------- HTML templates (kept inside this file to stay short) ----------
BASE = """<!doctype html><html><head><title>Pharmacy System</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body>
<nav class="navbar navbar-expand navbar-dark bg-success px-3"><span class="navbar-brand">Pharmacy</span>
{% if session.user %}<a class="nav-link text-white px-3" href="/">Dashboard</a>
<a class="nav-link text-white px-3" href="/medicines">Medicines</a>
<a class="nav-link text-white px-3" href="/sell">Sell</a>
<a class="nav-link text-white px-3" href="/sales">Sales</a>
<a class="nav-link text-white px-3 ms-auto" href="/logout">Logout</a>{% endif %}</nav>
<div class="container mt-4">{% for m in get_flashed_messages() %}<div class="alert alert-info">{{ m }}</div>{% endfor %}
{% block body %}{% endblock %}</div></body></html>"""

LOGIN = """{% extends "base.html" %}{% block body %}
<form method="post" class="col-md-4 mx-auto"><h3>Login</h3>
<input name="username" class="form-control mb-2" placeholder="Username" required>
<input name="password" type="password" class="form-control mb-2" placeholder="Password" required>
<button class="btn btn-success w-100">Login</button></form>{% endblock %}"""

TABLE = """{% macro tbl(rows) %}<table class="table table-sm"><tr><th>Name</th><th>Stock</th><th>Expiry</th></tr>
{% for r in rows %}<tr><td>{{ r.name }}</td><td>{{ r.stock }}</td><td>{{ r.expiry }}</td></tr>
{% else %}<tr><td colspan=3>None</td></tr>{% endfor %}</table>{% endmacro %}"""

DASH = """{% extends "base.html" %}{% from "table.html" import tbl %}{% block body %}
<div class="row text-center mb-3">
<div class="col"><div class="card p-3"><h6>Total Medicines</h6><h3>{{ total }}</h3></div></div>
<div class="col"><div class="card p-3"><h6>Low Stock</h6><h3>{{ low|length }}</h3></div></div>
<div class="col"><div class="card p-3"><h6>Today's Sales</h6><h3>{{ sales }} Tk</h3></div></div></div>
<h5>Low Stock (&lt;10)</h5>{{ tbl(low) }}
<h5>Expiring in 30 days</h5>{{ tbl(soon) }}
<h5 class="text-danger">Expired</h5>{{ tbl(expired) }}{% endblock %}"""

MEDS = """{% extends "base.html" %}{% block body %}
<form class="d-flex mb-3"><input name="q" class="form-control me-2" placeholder="Search name/category">
<button class="btn btn-outline-success me-2">Search</button><a class="btn btn-success" href="/medicines/add">+ Add</a></form>
<table class="table table-striped"><tr><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Expiry</th><th></th></tr>
{% for r in rows %}<tr><td>{{ r.name }}</td><td>{{ r.category }}</td><td>{{ r.price }}</td><td>{{ r.stock }}</td><td>{{ r.expiry }}</td>
<td><a class="btn btn-sm btn-warning" href="/medicines/{{ r.id }}/edit">Edit</a>
<form method="post" action="/medicines/{{ r.id }}/delete" class="d-inline" onsubmit="return confirm('Delete?')">
<button class="btn btn-sm btn-danger">Delete</button></form></td></tr>{% endfor %}</table>{% endblock %}"""

FORM = """{% extends "base.html" %}{% block body %}
<form method="post" class="col-md-5"><h4>{{ 'Edit' if m else 'Add' }} Medicine</h4>
<input name="name" class="form-control mb-2" placeholder="Name" value="{{ m.name if m }}" required>
<input name="category" class="form-control mb-2" placeholder="Category" value="{{ m.category if m }}">
<input name="price" type="number" step="0.01" class="form-control mb-2" placeholder="Price" value="{{ m.price if m }}" required>
<input name="stock" type="number" class="form-control mb-2" placeholder="Stock" value="{{ m.stock if m }}" required>
<input name="expiry" type="date" class="form-control mb-2" value="{{ m.expiry if m }}" required>
<button class="btn btn-success">Save</button></form>{% endblock %}"""

SELL = """{% extends "base.html" %}{% block body %}
<form method="post"><input name="customer" class="form-control mb-3 col-md-4" placeholder="Customer name (optional)">
<table class="table"><tr><th>Medicine</th><th>Price</th><th>In Stock</th><th>Qty</th></tr>
{% for m in meds %}<tr><td>{{ m.name }}</td><td>{{ m.price }}</td><td>{{ m.stock }}</td>
<td><input name="qty_{{ m.id }}" type="number" min="0" max="{{ m.stock }}" class="form-control w-50"></td></tr>{% endfor %}</table>
<button class="btn btn-success">Generate Bill</button></form>{% endblock %}"""

SALES = """{% extends "base.html" %}{% block body %}<h4>Sales History</h4>
<table class="table table-striped"><tr><th>#</th><th>Customer</th><th>Total (Tk)</th><th>Date</th></tr>
{% for r in rows %}<tr><td>{{ r.id }}</td><td>{{ r.customer }}</td><td>{{ r.total }}</td><td>{{ r.date }}</td></tr>{% endfor %}
</table>{% endblock %}"""

app.jinja_loader = DictLoader({
    "base.html": BASE, "login.html": LOGIN, "table.html": TABLE, "dashboard.html": DASH,
    "medicines.html": MEDS, "form.html": FORM, "sell.html": SELL, "sales.html": SALES})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)