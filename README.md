getSocial

getSocial is a social media web application built with Python, Flask, SQLAlchemy, and Flask-SocketIO. It offers essential features you'd expect from a modern social platform: user authentication, posting media, real-time messaging, following/unfollowing, search, notifications, comments, likes, profiles, and more.
Features
User Authentication
Registration and login with password hashing
Profile management (edit bio, upload profile picture)
Account deletion
Posts & Media
Create posts with image/video uploads
Edit or delete your posts
Like and comment on posts (including threaded replies)
Hashtag support in captions
Social Graph
Follow/unfollow other users
Suggestions for new users to follow
Dedicated follower/following APIs
Messaging
Real-time private messaging via WebSockets
Typing indicators and online status
Inbox for conversations
Notifications
Instantly see likes, follows, and message notifications
Mark notifications as read
Search
User search with auto-complete
Security
Uses Flask-Login for session management
Passwords stored as hashes
Access control for protected routes
Tech Stack
Backend: Python, Flask, SQLAlchemy, Flask-Login, Flask-SocketIO
Database: SQLite (development-ready)
Realtime: Flask-SocketIO (using Eventlet)
Templating: Jinja2
Frontend: HTML/CSS/Jinja (templates in /templates)
File Uploads: Support for image/video uploads, profile pictures
Installation
Clone the repository:
bash
git clone https://github.com/yourusername/getSocial.git
cd getSocial
(Optional) Create & activate a virtual environment:
bash
python -m venv venv
source venv/bin/activate           # On Windows: venv\Scripts\activate
Install dependencies:
bash
pip install -r requirements.txt
Make sure you're using Python 3.8+.
Usage
Set up the database (runs automatically on first launch):
No manual steps required for the included SQLite database.
Run the app:
bash
python app.py
Or, if your main file is named differently (e.g., getSocial.py):
bash
python getSocial.py
Open your browser:
Go to http://localhost:5000
