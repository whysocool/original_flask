from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

bp = Blueprint("auth", __name__)


@bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():  # view function
    if request.method == 'POST':
        email = request.form.get('email')
        fullName = request.form.get('fullName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        # check form valid or not
        user_found = db.users.find_one({'email': email})  # each user has distinct email
        if user_found:
            flash('email already exists', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.',
                  category='error')  # category is used assign colour to flashed messages
        elif len(fullName) < 2:
            flash('full name must be greater than 1 characters.', category='error')
        elif password2 != password1:
            flash('passwords don\'t match', category='error')
        elif len(password1) < 7:
            flash('passwords must be greater than 6 characters.', category='error')
        else:
            new_user = {
                'email': email,
                'fullName': fullName,
                'password': generate_password_hash(password1),
            }
            db.users.insert_one(new_user)
            flash('account created', category='success')
            return redirect(url_for('auth.login'))
    return render_template("sign_up.html")


@bp.route('/login', methods=['GET', 'POST'])  # route() decorator to bind a function to a URL.
def login():
    if request.method == 'POST':
        email = request.form['email']  # .get('email')  get方法也行，方括号也行
        password = request.form['password1']  # .get('password1')

        user_found = db.users.find_one({'email': email})  # each user has distinct email
        if user_found:  # user exists
            if check_password_hash(user_found['password'], password):
                flash("logged in successfully", category='success')
                session['email'] = email
                return redirect(url_for('views.home'))  # 返回的是function。用的是绝对路径，好处是能避免相对路径可能出错。
            else:
                flash("incorrect password", category='error')
        else:
            flash("email does not exit", category='error')
    return render_template("login.html")





@bp.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('auth.login'))
