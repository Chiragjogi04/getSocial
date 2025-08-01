# 🌐 getSocial

A modern, feature-rich **social media web application** built with **Python**, **Flask**, **SQLAlchemy**, and **Flask-SocketIO**.  
It offers real-time messaging, media posting, likes, comments, notifications, hashtags, and much more—designed to provide an experience you'd expect from top social platforms.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-%20%20v2.x%20-black?logo=flask)
![SocketIO](https://img.shields.io/badge/Realtime-Flask--SocketIO-red?logo=websocket)

---

## ✨ Features

### 👤 User Authentication
- Secure registration and login (passwords hashed)
- Profile management (bio, profile picture upload)
- Account deletion

### 📸 Posts & Media
- Create posts with image/video uploads
- Edit or delete your own posts
- Like and comment on posts (with threaded replies)
- Hashtag support in captions

### 🔗 Social Graph
- Follow/unfollow users
- User suggestions
- API access for follower/following lists

### 💬 Messaging
- Real-time private chat (WebSocket-based)
- Typing indicators and online/offline presence
- Inbox for conversations

### 🔔 Notifications
- Instant alerts for likes, follows, messages
- Mark notifications as read

### 🔍 Search
- User search with auto-complete suggestions

### 🔐 Security
- Session management with Flask-Login
- Hashed password storage
- Access control for protected routes

---

## 🛠️ Tech Stack

| Layer         | Technology                                   |
|---------------|----------------------------------------------|
| **Backend**   | Python, Flask, SQLAlchemy, Flask-Login       |
| **Database**  | SQLite                                       |
| **Realtime**  | Flask-SocketIO (Eventlet)                    |
| **Frontend**  | HTML, CSS, Jinja2 (templating)               |
| **Media**     | Support for image/video uploads              |

---

## 🚀 Getting Started

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/Chiragjogi04/getSocial.git
cd getSocial
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Running the App
### Launch the application

```bash
python app.py
```
OR
```bash
python3 getSocial.py
```

### Finally open your browser and go to:
👉 http://127.0.0.1:5000 and getSocial....
