from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

bp = Blueprint("auth", __name__)


@bp.route('/login', methods=['GET', 'POST'])  # route() decorator to bind a function to a URL.
def login():
    if request.method == 'POST':
        email = request.form['email']  # .get('email')  get方法也行，方括号也行
        password = request.form['password1']  # .get('password1')

        user = User.query.filter_by(email=email).first()
        if user:  # user exists
            if check_password_hash(user.password, password):
                flash("logged in successfully", category='success')
                login_user(user, remember=True)  # 浏览器会记住user，不用每次都登录
                return redirect(url_for('views.home'))  # 返回的是function。用的是绝对路径，好处是能避免相对路径可能出错。
            else:
                flash("incorrect password", category='error')
        else:
            flash("email does not exit", category='error')
    return render_template("login.html", user=current_user)


@bp.route('/logout')
@login_required  # 只有在登陆的状态下才额能访问logout界面
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        # check form valid or not
        user = User.query.filter_by(email=email).first()
        if user:
            flash('email already exists', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')  # category的名字是用来区别popup信息颜色的
        elif len(firstName) < 2:
            flash('first name must be greater than 1 characters.', category='error')  # category的名字是用来区别popup信息颜色的
        elif password2 != password1:
            flash('passwords don\'t match', category='error')  # category的名字是用来区别popup信息颜色的
        elif len(password1) < 7:
            flash('passwords must be greater than 6 characters.', category='error')  # category的名字是用来区别popup信息颜色的
        else:
            new_user = User(email=email, first_name=firstName,
                            password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)  # 注册完后自动登录.“Remember Me” prevents the user from accidentally being logged out when they close their browser.
            flash('account created', category='success')  # category的名字是用来区别popup信息颜色的
            return redirect(url_for('views.home'))  # views是blueprint的名字，home是里面的function的名字

    return render_template("sign_up.html", user=current_user)
