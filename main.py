from sqlite3 import IntegrityError
import sqlalchemy
import werkzeug
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
#from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from functools import wraps
from wtforms.validators import DataRequired, URL
import dotenv
from dotenv import load_dotenv

import os

load_dotenv()

import requests
from pprint import PrettyPrinter
printer = PrettyPrinter()

BASE_URL = 'https://finnhub.io/api/v1'
JSON_FILE = '/news?category=general'
API_KEY = os.getenv('API_KEY')
headers = {
    'X-Finnhub-Token': API_KEY
}
response = requests.get(BASE_URL+JSON_FILE, headers=headers)
data = response.json()
print(response)
#printer.pprint(data)
try:
    news_headlines = []
    news_url = []
    news_images = []
    news_source = []
    for i in range(len(data)):
        if data[i]['source'] == 'Bloomberg':
            continue
        news = data[i]['headline']
        url = data[i]['url']
        images = data[i]['image']
        source = data[i]['source']
        news_headlines.append(news)
        news_url.append(url)
        news_images.append(images)
        news_source.append(source)
    news_dict = {}
    for i in range(6):
        news_dict[news_headlines[i]] = news_url[i], news_images[i], news_source[i]
except KeyError:
    news_dict = {0:0}
#for key,value in news_dict.items():
    #print(key, value[1])

def word_search(names: list[str], searchWord: str):
    lis = []
    names.sort()
    left = 0
    right = len(names) - 1
    for i in range(len(searchWord)):
        char = searchWord[i]
        while left <= right and (len(names[left]) <= i or names[left][i] != char):
            left += 1
        while left <= right and (len(names[right]) <= i or names[right][i] != char):
            right -= 1
    lis.append([])
    remain = right - left + 1
    for j in range(remain):
        lis[-1].append(names[left + j])
    if len(lis[0]) == 0:
        return 'player not found'
    print(lis[0])
    return lis[0]

# CREATE FLASK CONNECTION
app = Flask(__name__)
ckeditor = CKEditor(app)
bootstrap = Bootstrap(app)
# connect to SQlite DB
app.config['SECRET_KEY'] = os.getenv('secret_key')
og = 'sqlite:///social_network.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CONFIGURE TABLES
followers = db.Table('followers',
        db.Column('follower_id', db.Integer, db.ForeignKey('website_users.id')),
        db.Column('followed_id', db.Integer, db.ForeignKey('website_users.id'))
                     )

class User(UserMixin, db.Model):
    __tablename__ = "website_users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    pic = db.Column(db.String(250), nullable=False)
    posts = db.relationship('Posts', back_populates='author')
    followed = db.relationship('User', secondary=followers,
                            primaryjoin=(followers.c.follower_id == id),
                            secondaryjoin=(followers.c.followed_id == id),
                            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f'{self.name}'

class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    text = db.Column(db.String(250), nullable=False)
    # foreign key
    author_id = db.Column(db.Integer, db.ForeignKey('website_users.id'))
    author = db.relationship('User', back_populates='posts')
    date = db.Column(db.String(250), nullable=False)

#db.create_all()

# CREATE FORMS
class registerForm(FlaskForm):
    email = StringField('Email: ', validators=[DataRequired()])
    password = PasswordField("Password: ", validators=[DataRequired()])
    name = StringField('Full name: ', validators=[DataRequired()])
    submit = SubmitField('Sign up ')

class loginForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('log in')

class PostForm(FlaskForm):
    title = StringField('Title:', validators = [DataRequired()])

    text = StringField('caption: ', validators=[DataRequired()])
    submit = SubmitField('Submit Post')

class ProfilePicture(FlaskForm):
    picture = StringField('upload profile picture')
    submit = SubmitField('submit')

class name_form(FlaskForm):
    player_name = StringField("Enter user name: ")
    submit = SubmitField('Submit')

#LOGIN MANAGER
login_manger=LoginManager()
login_manger.init_app(app)

# gets user_id from database
@login_manger.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#logs out user before app opens
@app.before_first_request
def init_app():
    logout_user()

@app.route('/')
def home_page():
    news = news_dict
    try:
        foll_post = []
        for item in current_user.followed:
            foll_post.append(item.posts)
        #all_post = list(itertools.chain(*foll_post))
        all_post = []
        for item in foll_post:
            all_post = all_post + item
        print(all_post)
        new_posts = all_post

    except AttributeError:
        post = Posts.query.all()
        all_post = post[::-1]
        new_posts = all_post
    return render_template('index.html', news=news, new_posts=new_posts)

@app.route('/register', methods=["GET" ,"POST"])
def register():
    form = registerForm()
    if form.validate_on_submit():
        new_user = User(
            email = request.form['email'],
            password=werkzeug.security.generate_password_hash(
                request.form['password'],
                method='sha256',
                salt_length=8),
            name = request.form['name'],
            pic = ''
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
        except sqlalchemy.exc.IntegrityError:
            flash('you already have an account with this email, please try again')
        else:
            return redirect(url_for('home_page'))
    return render_template('register.html', form=form)

@app.route('/login', methods=["POST", "GET"])
def login():
    form = loginForm()
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('invalid email')
            return redirect(url_for('login'))
        elif user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home_page'))
        else:
            flash('invalid password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/new-post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if request.method == 'POST':
        new_post = Posts(
            title=request.form['title'],
            img_url='',
            text=request.form['text'],
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('all_post'))
    return render_template('new_post.html', form=form)

@app.route('/edit/<int:post_id>', methods=['POST', 'GET'])
@login_required
def edit_post(post_id):

    post = Posts.query.get(post_id)
    edit_form = PostForm(
        title=post.title,
        img_url=post.img_url,
        text=post.text,
        author=post.author,
        date=post.date
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.img_url = ''
        post.text = edit_form.text.data
        post.author = current_user
        post.date = date.today().strftime("%B %d, %Y")
        db.session.commit()
        return redirect(url_for('all_post'))
    return render_template('new_post.html', form=edit_form)

@app.route('/delete/<int:post_id>', methods=["POST", 'GET'])
@login_required
def delete(post_id):
    #
    id = current_user.id
    post = Posts.query.get(post_id)
    if id == post.author_id:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('all_post'))

@app.route('/all-post', methods=["GET", 'POST'])
def all_post():
    post = Posts.query.all()
    all_post = post[::-1]
    return render_template('all_post.html', all_posts=all_post)

@app.route('/profile', methods=['GET', "POST"])
@login_required
def profile():
    form = ProfilePicture()
    update_user_id = current_user.id
    user = User.query.get(update_user_id)
    if request.method == 'POST':
        user.pic = request.form['picture']
        db.session.commit()
    user = User.query.filter_by(id = update_user_id).first()
    all_post = user.posts
    foll = []
    foll_post = []
    for item in current_user.followed:
        foll.append(item)
        foll_post.append(item.posts)
    num = len(foll)
    print(current_user.posts)
    return render_template('profile.html', form=form, posts=all_post, num=num)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/player_search', methods=["POST", "GET"])
@login_required
def player_search():
    form = name_form()
    names = None
    if form.validate_on_submit():
        search = request.form['player_name'].lower()
        name = User.query.all()
        lis_names = []
        for item in name:
            lis_names.append(item.name)
        print(lis_names)
        names = word_search(lis_names, search)
    return render_template('player_search.html', form=form, names=names)

@app.route('/other_profile/<search_name>', methods=["POST", "GET"])
@login_required
def other_profile(search_name):
    search_user = User.query.filter_by(name=search_name).first()
    users_post = search_user.posts
    foll = []
    for item in current_user.followed:
        foll.append(item)

    return render_template('other_user.html', posts=users_post, search_user=search_user, foll=foll)

@app.route('/follow/<user_name>', methods=["GET", "POST"])
@login_required
def follow(user_name):
    form = name_form()
    if form.validate_on_submit():
        user_name = request.form['player_name']
        user = User.query.filter_by(name=user_name).first()
        current_user.followed.append(user)
        db.session.commit()
    return render_template('follow.html', form=form)

@app.route('/follow_user/<user_name>', methods=["GET", "POST"])
@login_required
def follow_user(user_name):
    user = User.query.filter_by(name=user_name).first()
    current_user.followed.append(user)
    db.session.commit()
    return redirect(url_for('other_profile', search_name=user_name))

@app.route('/unfollow_user/<user_name>', methods=["GET", "POST"])
@login_required
def unfollow_user(user_name):
    user = User.query.filter_by(name=user_name).first()
    current_user.followed.remove(user)
    db.session.commit()
    return redirect(url_for('other_profile', search_name=user_name))

@app.route('/following_list', methods=["GET", "POST"])
@login_required
def following_list():
    foll = []
    for item in current_user.followed:
        foll.append(item)

    return render_template('follow.html', foll=foll)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
