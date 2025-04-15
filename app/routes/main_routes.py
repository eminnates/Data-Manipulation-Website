from flask import Blueprint, render_template

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    return render_template("index.html")

@main_blueprint.route("/hakkimizda")
def hakkimizda_page():
    return render_template("hakkımızda.html")

@main_blueprint.route("/iletisim")
def iletisim_page():
    return render_template("iletisim.html")
