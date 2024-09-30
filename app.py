from flask import Flask, render_template, redirect, url_for, request, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tweetr.db'
app.config['SECRET_KEY'] = 'ilovecode' 


# Set the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

#database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True) 

    tweets = db.relationship('Tweet', backref='author', lazy=True)

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.before_request
def load_user():
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
    else:
        g.user = None

@app.route('/')
def index():
    if not g.user:
        return render_template('landing.html')
    tweets = Tweet.query.order_by(Tweet.timestamp.desc()).all()
    return render_template('timeline.html', tweets=tweets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))

    return render_template('login.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        gender = request.form['gender']

        hashed_pw = generate_password_hash(password)

        # Handle profile picture upload
        file = request.files['profile_picture']
        profile_picture = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            profile_picture = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(profile_picture)

        new_user = User(username=username, password=hashed_pw, gender=gender, profile_picture=profile_picture)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/tweet', methods=['POST'])
def tweet():
    if not g.user:
        return redirect(url_for('login'))

    content = request.form['content']
    new_tweet = Tweet(content=content, user_id=g.user.id)
    db.session.add(new_tweet)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    tweets = Tweet.query.filter_by(user_id=user_id).order_by(Tweet.timestamp.desc()).all()

    return render_template('profile.html', user=user, tweets=tweets)


if __name__ == '__main__':
    app.run(debug=True)
