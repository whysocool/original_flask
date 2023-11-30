from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from werkzeug.security import generate_password_hash
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
    if request.method == 'POST':
        fullName = request.form.get('fullName')
        nationality = request.form.get('nationality')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        budget_accommodation = request.form.get('budget_accommodation')
        budget_transportation = request.form.get('budget_transportation')
        if len(fullName) < 2:
            flash('full name must be greater than 1 characters.', category='error')
        elif len(nationality) < 3:
            flash('nationality must be greater than 2 characters.', category='error')
        elif len(password) < 7:
            flash('passwords must be greater than 6 characters.', category='error')
        elif int(age) < 0:
            flash('age must be great than 0.', category='error')
        elif not (gender in ('Male', 'Female')):
            flash('gender must be Male or Female.', category='error')
        elif int(budget_accommodation) < 0:
            flash('budget must be greater than 0.', category='error')
        elif int(budget_transportation) < 0:
            flash('budget must be greater than 0.', category='error')
        else:
            # update user document
            myquery = db.users.find_one({'email': session['email']})
            new_document = {
                "$set": {"fullName": fullName,
                         "nationality": nationality,
                         'password': generate_password_hash(password),
                         'age': age,
                         'gender': gender,
                         'budget_accommodation': budget_accommodation,
                         'budget_transportation': budget_transportation}
            }
            db.users.update_one(myquery, new_document)
            flash('Profile modified successfully.', category='success')
            return redirect(url_for('views.home'))
    return render_template('/modify_one_user_profile.html', user_found=db.users.find_one({'email': session['email']}))
