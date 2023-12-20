from flask import request, jsonify
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination
from flask import abort


app = Flask(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

posts = []

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:12345@localhost/blogPosts'
app.secret_key = '123456789'

db = SQLAlchemy(app)

# -------------------------------------- Tables --------------------------------------


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    comments = db.relationship('Comments', backref='post', lazy=True)


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    commenter_name = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)


class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)
    successful = db.Column(db.Boolean, nullable=False)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, search_query, successful):
        self.search_query = search_query
        self.successful = successful

class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String, nullable=False)
    event_description = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, event_type, event_description):
        self.event_type = event_type
        self.event_description = event_description


with app.app_context():
    db.create_all()

# -------------------------------------- routes --------------------------------------


@app.route('/search')
def search():
    search_query = request.args.get("query", "").lower()

    if not search_query:
        return jsonify({"error": "Invalid search query"}), 400

    page = request.args.get("page", 1, type=int)
    per_page = 3

    posts = Post.query.filter(Post.title.ilike(f"%{search_query}%")).paginate(
        page=page, per_page=per_page, error_out=False)

    if not posts.items:
        log_search = SearchLog(search_query=search_query, successful=False)
        db.session.add(log_search)
        db.session.commit()

        return jsonify({"message": "No results found"}), 404

    log_search = SearchLog(search_query=search_query, successful=True)
    db.session.add(log_search)
    db.session.commit()

    history_entry = History(event_type='search_performed', event_description=f'Search for "{search_query}"')
    db.session.add(history_entry)
    db.session.commit()

    results = [
        {"title": post.title, "url": url_for('displayPost', post_title=post.title, _external=True), "timestamp": post.timestamp} for post in posts.items
    ]

    return jsonify(results)


@app.route('/displayPost/<string:post_title>')
def displayPost(post_title):
    post = Post.query.filter_by(title=post_title).first_or_404()
    return render_template('displayPost.html', post=post)


@app.route('/delete_post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    history_entry = History(event_type='post_deleted', event_description=f'Post "{post.title}" deleted')
    db.session.add(history_entry)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    commenter_name = request.form.get('commenter_name')
    comment_content = request.form.get('comment')

    new_comment = Comments(
        post=post, commenter_name=commenter_name, content=comment_content)
    db.session.add(new_comment)
    db.session.commit()

    history_entry = History(event_type='comment_created', event_description=f'Comment on post "{post.title}" created')
    db.session.add(history_entry)
    db.session.commit()

    return redirect(url_for('otherUser', page=request.args.get('page', 1, type=int)))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower()
        username = request.form['username'].lower()
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template('register.html')

        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # Password is correct
            if user.username == "admin":
                return redirect(url_for('add_post'))
            else:
                return redirect(url_for('otherUser'))

    return render_template('login.html')


@app.route('/blogPosts', methods=['GET'])
def otherUser():
    page = request.args.get('page', 1, type=int)
    per_page = 3
    posts = Post.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('userBlogs.html', posts=posts)


@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    page = request.args.get('page', 1, type=int)
    per_page = 3
    posts = Post.query.paginate(page=page, per_page=per_page, error_out=False)

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        timestamp = datetime.now().strftime("%A, %B %d %Y at %I:%M %p")
        photo = request.files['photo']

        photo_filename = None

        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if photo and allowed_file(photo.filename):
            photo_filename = f"static/{secure_filename(photo.filename)}"
            photo.save(photo_filename)

            with app.app_context():
                save_post = Post(title=title, author=author, content=content,
                                 timestamp=timestamp, image=photo_filename)
                db.session.add(save_post)
                db.session.commit()

            history_entry = History(event_type='post_created', event_description=f'Post "{title}" created')
            db.session.add(history_entry)
            db.session.commit()

        posts = Post.query.all()

        posts = Post.query.paginate(
            page=page, per_page=per_page, error_out=False)

        return redirect(url_for('add_post') + f'?page={posts.page}' + '#blogPosts')

    return render_template('adminBlog.html', posts=posts)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(port=8000, debug=True)