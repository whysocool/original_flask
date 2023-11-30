from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from . import db

bp = Blueprint("views", __name__)


@bp.route('/', methods=['GET'])
def home():
    return render_template("home.html")


@bp.route('/one_user_history', methods=['GET'])
def one_user_history():
    cursor = db.histories.find({'email': session['email']})
    return render_template('one_user_history.html', cursor=cursor)


@bp.route('/modify_one_user_profile', methods=['GET', 'POST'])
def modify_one_user_profile():
    if request.method=='POST':
        fullName = request.form.get('fullName')
        email = request.form.get('email')
        nationality = request.form.get('nationality')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        budget_accommodation = request.form.get('budget_accommodation')
        budget_transportation = request.form.get('budget_transportation')
        if len(email)<4:
            flash('Email must be greater than 3 characters.',
              category='error')  # category is used assign colour to flashed messages
    return


    return render_template('/modify_one_user_profile.html',user_found=db.find_one({'email': session['email']})
