from functools import wraps

from flask import redirect, session


def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if "user" not in session:
            return redirect("/login")
        return f(*a, **k)

    return wrap
