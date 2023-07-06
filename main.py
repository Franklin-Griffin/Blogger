# Thanks past me for code examples!
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from markdown import markdown
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, login_blocked, error, success

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


@app.after_request
def after_request(response):
		"""Ensure responses aren't cached"""
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Expires"] = 0
		response.headers["Pragma"] = "no-cache"
		return response

@app.route("/")
@login_blocked
def index():
		return render_template("index.html")
	
@app.route("/home")
@login_required
def home():
		posts = db.execute("SELECT post_id, user_id AS user, title, subtitle, txt FROM posts ORDER BY post_id DESC LIMIT 3")
		for i in range(len(posts)):
			posts[i]["user"] = db.execute("SELECT username FROM users WHERE id = ?", posts[i]["user"])[0]["username"] # Change the user ID to the username
		return render_template("home.html", posts=posts)

@app.route("/login", methods=["GET", "POST"])
@login_blocked
def login():
		if request.method == "GET":
				return render_template("login.html")

		# POST
		if not request.form.get("username"):
				return error("You must provide a username")

		if not request.form.get("password"):
				return error("You must provide a password")
		rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
		if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
				return error("Invalid username and/or password")
		session["user_id"] = rows[0]["id"]
		session["user_name"] = db.execute("SELECT username FROM users WHERE id = ?", rows[0]["id"])[0]["username"]
		return success("You are now logged in!")

@app.route("/register", methods=["GET", "POST"])
@login_blocked
def register():
		if request.method == "GET":
				return render_template("register.html")

		username = request.form.get("username")
		password = request.form.get("password")
		confirm = request.form.get("confirmation")

		if not username or username == "":
				return error("Please enter a name")

		if len(db.execute("SELECT * FROM users WHERE username = ?", username)) != 0:
				return error("Username already exists. Are you trying to <a href='/login'>log in?</a>")
		if not password or password == "":
				return error("Please enter a password")
		if not confirm or confirm == "":
				return error("Please enter a confirmation password")
		if not password == confirm:
				return error("Passwords do not match")
		# Passwords must have 8 characters, a number, a letter, and a special character
		if len(password) < 8:
				return error("Your password is not long enough")
		number = False
		letter = False
		special = False
		for i in password:
				if i.isnumeric():
						number = True
				elif i.isalpha():
						letter = True
				else:
						# Special character
						special = True
		if not number:
				return error("Your password must contain a number")
		if not letter:
				return error("Your password must contain a letter")
		if not special:
				return error("Your password must contain a special character")
		# Register user and log in
		db.execute("INSERT INTO users (username, hash, tasks) VALUES (?, ?, 0)", username, generate_password_hash(password))
		session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["id"]
		session["user_name"] = username
		return success("You have successfully registered!")

@app.route("/logout")
def logout():
		session.clear()
		flash("You have successfully been logged out!", "success")
		return redirect("/")

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
		if request.method == "GET":
				return render_template("post.html")

		title = request.form.get("title")
		subtitle = request.form.get("subtitle")
		txt = request.form.get("text") # txt to avoid SQL keyword text 
		if not title:
			return error("Your post must have a title")
		if not txt:
			return error("Your post must have body text")
		db.execute("INSERT INTO posts (user_id, title, subtitle, txt) VALUES (?, ?, ?, ?)", session["user_id"], title, subtitle, markdown(txt))
		return success("Posted!")
	
@app.route("/read", methods=["POST"])
def read():
		if "del" in request.form:
			db.execute("DELETE FROM posts WHERE post_id = ?", request.form.get("del"))
			return success("Post deleted!")
		post = db.execute("SELECT title, subtitle, txt, user_id FROM posts WHERE post_id = ?", request.form.get("id"))[0]
		user = db.execute("SELECT username FROM users WHERE id = ?", post["user_id"])[0]["username"]
		return render_template("read.html", title=post["title"], subtitle=post["subtitle"], txt=post["txt"], user=user)

@app.route("/posts")
def posts():
		posts = db.execute("SELECT post_id, user_id AS user, title, subtitle, txt FROM posts ORDER BY post_id DESC") # no "LIMIT 3"
		for i in range(len(posts)):
			posts[i]["user"] = db.execute("SELECT username FROM users WHERE id = ?", posts[i]["user"])[0]["username"] # Change the user ID to the username
		return render_template("posts.html", posts=posts)

@app.route("/about")
def about():
		return render_template("about.html")
	
@app.route("/contact")
def contact():
		return render_template("contact.html")

app.run(host='0.0.0.0', port=81)