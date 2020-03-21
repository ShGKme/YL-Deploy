import os
import time
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from mars.data import db_session
from mars.data.models import User, News
from mars.forms import LoginForm, RegisterForm, NewsForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db = db_session.create_session()
    return db.query(User).get(user_id)


@app.route('/')
def index():
    db = db_session.create_session()
    news = db.query(News).filter(News.is_private != True)
    return render_template("public_news.html", news=news)


@app.route('/fib')
def fib():
  def calc(n):
    if n <= 1:
      return 1
    return calc(n - 1) + calc(n - 2)
  start_time = time.time()
  numbers = [calc(i) for i in range(34)]
  waiting = f"--- {time.time() - start_time} seconds ---"
  return render_template('fib.html', numbers=numbers, waiting=waiting)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        db = db_session.create_session()
        user = db.query(User).filter(User.email == login_form.email.data).first()
        if not user:
            return render_template('login.html', form=login_form, message="Такого пользователя не существует")
        if user.check_password(login_form.password.data):
            login_user(user, remember=login_form.remember_me.data)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', form=login_form, message="Неверный пароль")
    else:
        return render_template('login.html', form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db = db_session.create_session()
        if db.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.add(user)
        db.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости', form=form)

from os import path
db_session.global_init(path.join(path.dirname(__file__), './db/mars_explorer.db'))


def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)