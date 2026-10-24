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
