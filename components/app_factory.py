from flask import Flask
from jinja2 import DictLoader

from .db import init_db, register_db_handlers
from .routes import bp
from .templates import (
    BASE,
    DASH,
    FORM,
    LOGIN,
    MEDS,
    SALES,
    SELL,
    TABLE,
)


def create_app():
    app = Flask(__name__)
    app.secret_key = "change-this-secret"

    register_db_handlers(app)
    app.register_blueprint(bp)
    app.jinja_loader = DictLoader({
        "base.html": BASE,
        "login.html": LOGIN,
        "table.html": TABLE,
        "dashboard.html": DASH,
        "medicines.html": MEDS,
        "form.html": FORM,
        "sell.html": SELL,
        "sales.html": SALES,
    })
    return app


app = create_app()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
