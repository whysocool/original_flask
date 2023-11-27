from flask import Blueprint, render_template, request, flash, session
from . import db

bp = Blueprint("views", __name__)


@bp.route('/', methods=['GET'])
def home():
    return render_template("home.html")
