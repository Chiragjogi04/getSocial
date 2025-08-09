import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import case, and_, or_, func
from flask_socketio import SocketIO, emit, join_room, leave_room
import re
from sqlalchemy.sql.expression import func

# === Flask App ===
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///getSocial.db'
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['PROFILE_PIC_FOLDER'] = 'static/images/profile_pics'

db = SQLAlchemy(app)
socketio = SocketIO(app)
online_users = set()

# === Login Manager ===
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# === Followers Table ===
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# === Models ===
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(300), default='default.jpg')
    bio = db.Column(db.Text, default='')
    is_online = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    # ✅ Notifications RECEIVED
    notifications_received = db.relationship(
        'Notification',
        backref='recipient',
        lazy='dynamic',
        foreign_keys='Notification.user_id'
    )

    # ✅ Notifications SENT (actor who triggered)
    notifications_sent = db.relationship(
        'Notification',
        backref='actor',
        lazy='dynamic',
        foreign_keys='Notification.from_user_id'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_file = db.Column(db.String(300))
    media_type = db.Column(db.String(20))
    caption = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    likes = db.relationship('Like', backref='post', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy='dynamic')


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    seen = db.Column(db.Boolean, default=False)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # recipient
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # actor
    type = db.Column(db.String(50))
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


# === User Loader ===
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === Routes ===

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('feed'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/hashtag/<tag>')
@login_required
def hashtag(tag):
    posts = Post.query.filter(Post.caption.like(f"%#{tag}%")).order_by(Post.timestamp.desc()).all()
    return render_template('hashtag.html', tag=tag, posts=posts)


@app.route('/feed')
@login_required
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()

    follow_suggestions = User.query.filter(
        User.id != current_user.id,
        ~User.followers.any(id=current_user.id)
    ).order_by(func.random()).limit(10).all()

    return render_template(
        'feed.html',
        posts=posts,
        follow_suggestions=follow_suggestions,
        Comment=Comment
    )

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['media']
        caption = request.form['caption']

        if file:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                media_type = 'image'
                upload_folder = app.config['UPLOAD_FOLDER']
            elif ext in ['.mp4', '.avi', '.mov', '.webm']:
                media_type = 'video'
                upload_folder = 'static/videos/uploads'
                os.makedirs(upload_folder, exist_ok=True)
            else:
                flash('Unsupported file type.')
                return redirect(url_for('upload'))

            file.save(os.path.join(upload_folder, filename))

            post = Post(media_file=filename, media_type=media_type,
                        caption=caption, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Media uploaded!')

        return redirect(url_for('feed'))
    return render_template('upload.html')


@app.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like:
        db.session.delete(like)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    text = request.form['text']
    if text:
        db.session.add(Comment(text=text, user_id=current_user.id, post_id=post_id))
        db.session.commit()
    return redirect(url_for('feed'))

@app.route('/reply/<int:comment_id>', methods=['POST'])
@login_required
def reply_comment(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    text = request.form['text']
    if text:
        reply = Comment(text=text, user_id=current_user.id, post_id=parent.post_id, parent_id=parent.id)
        db.session.add(reply)
        db.session.commit()
    return redirect(url_for('feed'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        current_user.follow(user)
        notif = Notification(
            user_id=user.id,
            from_user_id=current_user.id,
            type='follow',
            message=f"{current_user.username} started following you."
        )
        db.session.add(notif)
        db.session.commit()
    return redirect(url_for('profile', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        current_user.unfollow(user)
        db.session.commit()
    return redirect(url_for('profile', username=username))

@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    bio = request.form.get('bio')
    file = request.files.get('profile_pic')

    if bio is not None:
        current_user.bio = bio

    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['PROFILE_PIC_FOLDER'], filename))
        current_user.profile_pic = filename

    db.session.commit()
    flash('Profile updated.')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    users = []
    if query:
        users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    return render_template('search.html', users=users, query=query)

@app.route('/autocomplete')
@login_required
def autocomplete():
    q = request.args.get('q', '').strip()
    usernames = []
    if q:
        usernames = User.query.filter(User.username.ilike(f'{q}%')).with_entities(User.username).limit(5).all()
        usernames = [u[0] for u in usernames]
    return jsonify(usernames)

@app.route('/messages/<username>')
@login_required
def messages(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        abort(403)

    sent = Message.query.filter_by(sender_id=current_user.id, recipient_id=user.id)
    received = Message.query.filter_by(sender_id=user.id, recipient_id=current_user.id)

    received.update({Message.seen: True})
    db.session.commit()

    all_messages = sent.union(received).order_by(Message.timestamp.asc()).all()
    room = f"chat_{min(current_user.id, user.id)}_{max(current_user.id, user.id)}"
    return render_template('messages.html', user=user, messages=all_messages, room=room)


@app.route('/inbox')
@login_required
def inbox():
    all_messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).subquery()

    user1 = case(
        (all_messages.c.sender_id < all_messages.c.recipient_id, all_messages.c.sender_id),
        else_=all_messages.c.recipient_id
    )
    user2 = case(
        (all_messages.c.sender_id < all_messages.c.recipient_id, all_messages.c.recipient_id),
        else_=all_messages.c.sender_id
    )

    latest_messages = db.session.query(
        func.max(all_messages.c.id).label('id')
    ).group_by(user1, user2).subquery()

    messages = Message.query.filter(Message.id.in_(db.session.query(latest_messages.c.id))).order_by(Message.timestamp.desc()).all()

    return render_template('inbox.html', messages=messages)



@app.route('/api/<username>/followers')
@login_required
def api_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page=page, per_page=10, error_out=False)
    followers = [{
        'username': u.username,
        'profile_pic': u.profile_pic
    } for u in pagination.items]
    return jsonify(followers)

@app.route('/api/<username>/following')
@login_required
def api_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page=page, per_page=10, error_out=False)
    following = [{
        'username': u.username,
        'profile_pic': u.profile_pic
    } for u in pagination.items]
    return jsonify(following)

@app.route('/notifications/clear')
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(request.referrer or url_for('feed'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    if request.method == 'POST':
        post.caption = request.form['caption'].strip()
        db.session.commit()
        flash('Post updated.')
        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_post.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.')
    return redirect(url_for('profile', username=current_user.username))

@app.template_filter('linkify')
def linkify(text):
    text = re.sub(r'(?<!\w)@(\w+)', r'<a href="/profile/\1" class="text-info fw-bold">@\1</a>', text)
    text = re.sub(r'(?<!\w)#(\w+)', r'<a href="/hashtag/\1" class="text-warning fw-bold">#\1</a>', text)
    return text

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id

    # Delete comments, likes
    Comment.query.filter_by(user_id=user_id).delete()
    Like.query.filter_by(user_id=user_id).delete()

    # Remove follower/followed relationships
    for u in current_user.followers.all():
        current_user.followers.remove(u)

    for u in current_user.followed.all():
        current_user.followed.remove(u)

    # Delete messages
    Message.query.filter(
        (Message.sender_id == user_id) | (Message.recipient_id == user_id)
    ).delete()

    # Delete notifications
    Notification.query.filter(
        (Notification.user_id == user_id) | (Notification.from_user_id == user_id)
    ).delete()

    # Delete posts
    posts = Post.query.filter_by(user_id=user_id).all()
    for post in posts:
        db.session.delete(post)

    # Delete the user
    logout_user()
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('Your account and all associated data have been deleted.')
    return redirect(url_for('login'))


@app.context_processor
def inject_notifications():
    if not current_user.is_authenticated:
        return dict(new_notifications=[])
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).order_by(Notification.timestamp.desc()).all()
    return dict(new_notifications=notifications)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    print(f"{current_user.username} joined {room}")


@socketio.on('send_message')
@login_required
def handle_send_message(data):
    room = data['room']
    body = data['body']
    recipient_username = data['recipient']

    recipient = User.query.filter_by(username=recipient_username).first_or_404()

    # Save message to DB
    msg = Message(sender_id=current_user.id, recipient_id=recipient.id, body=body)
    db.session.add(msg)

    # Add notification
    notif = Notification(
        user_id=recipient.id,
        from_user_id=current_user.id,
        type='message',
        message=f"New message from {current_user.username}."
    )
    db.session.add(notif)

    db.session.commit()

    emit('receive_message', {
        'sender': current_user.username,
        'sender_pic': url_for('static', filename=f'images/profile_pics/{current_user.profile_pic}'),
        'body': body,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    }, to=room)

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        online_users.add(current_user.id)
        emit('user_online', {'user_id': current_user.id}, broadcast=True)
        print(f"{current_user.username} connected 🟢")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated and current_user.id in online_users:
        online_users.remove(current_user.id)
        emit('user_offline', {'user_id': current_user.id}, broadcast=True)
        print(f"{current_user.username} disconnected 🔴")

@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    emit('typing', {'username': current_user.username}, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {'username': current_user.username}, room=room, include_self=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
