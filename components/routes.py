from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash

from .auth import login_required
from .db import db

bp = Blueprint("pharmacy", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        if u and check_password_hash(u["password"], request.form["password"]):
            session["user"] = u["username"]
            return redirect("/")
        flash("Wrong username or password")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@bp.route("/")
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


@bp.route("/medicines")
@login_required
def medicines():
    q = "%" + request.args.get("q", "") + "%"
    rows = db().execute("SELECT * FROM medicines WHERE name LIKE ? OR category LIKE ?", (q, q)).fetchall()
    return render_template("medicines.html", rows=rows)


@bp.route("/medicines/add", methods=["GET", "POST"])
@bp.route("/medicines/<int:mid>/edit", methods=["GET", "POST"])
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


@bp.route("/medicines/<int:mid>/delete", methods=["POST"])
@login_required
def delete(mid):
    db().execute("DELETE FROM medicines WHERE id=?", (mid,))
    db().commit()
    return redirect("/medicines")


@bp.route("/sell", methods=["GET", "POST"])
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


@bp.route("/sales")
@login_required
def sales():
    return render_template("sales.html", rows=db().execute("SELECT * FROM sales ORDER BY id DESC").fetchall())
