# set FLASK_APP=application.py
# set DATABASE_URL=postgres://rdtrqesvolkwti:876f3e658f83c936d8244ebbbb2ec271102bec9b6ab9c8ed7218f3fbf5e715aa@ec2-54-228-252-67.eu-west-1.compute.amazonaws.com:5432/ddmr1vdubddpvi

import os

from flask import Flask, session, render_template, redirect, request, jsonify
import requests
from flask_session import Session
from werkzeug.security import generate_password_hash, \
     check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, apology, until

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def index():
    """ INDEX """
    return render_template("index.html")


@app.route("/search", methods=["POST"])
@login_required
def search():
    """ SEARCH """

    search = request.form.get("search") + "%"
    if search is "%":
        return redirect("/")
    searchtext = until("%", search)
    li = db.execute("SELECT * FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search", {"search": search}).fetchall()

    add = "s"
    if len(li) == 1:
        add = ""

    return render_template("index.html", li=li, search="{} search result{} for '{}'".format(len(li), add,searchtext))


@app.route("/bookpage/<int:book_id>")
@login_required
def bookpage(book_id):
    """ BOOK PAGE """

    if book_id is None or db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).rowcount == 0:
        return apology("No such book.")

    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wy4PE1FcYzpSQ4HrApPcvA", "isbns": book["isbn"]}).json()

    if db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND username = :username", {"book_id": book_id, "username": session["username"]}).rowcount == 1:
        return render_template("book.html", book=book, reviews=reviews, reviewed=False, goodreads=goodreads["books"][0])
    else:
        return render_template("book.html", book=book, reviews=reviews, reviewed=True, goodreads=goodreads["books"][0])


@app.route("/review/<int:book_id>", methods=["POST"])
@login_required
def review(book_id):
    """ REVIEW """

    userinput = [request.form.get("review"), request.form.get("rating")]
    for i in userinput:
        if i is None:
                return apology("You must fill in all fields.")

    if db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND username = :username",
                    {"book_id": book_id, "username": session["username"]}).rowcount == 1:
        return apology("You've already written a review for this book.")

    else:
        db.execute("INSERT INTO reviews (book_id, review, rating, username) VALUES (:book_id, :review, :rating, :username)",
                    {"book_id": book_id, "review": userinput[0], "rating": userinput[1], "username": session["username"]})
        db.commit()

        return redirect("/bookpage/{}".format(book_id))


@app.route("/api/<string:isbn>")
def api(isbn):
    """ API ACCESS """

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wy4PE1FcYzpSQ4HrApPcvA", "isbns": book["isbn"]}).json()

    res = {"title": book["title"],
            "author": book["author"],
            "year": book["year"],
            "isbn": book["isbn"],
            "review_count": goodreads["books"][0]["work_reviews_count"],
            "average_score": goodreads["books"][0]["average_rating"]}
    return jsonify(res)


@app.route("/login", methods=["GET", "POST"])
def login():
    """ LOGIN """

    session.clear()

    if request.method == "POST":
        userinput = [request.form.get("username"), request.form.get("password")]
        for i in userinput:
            if i is None:
                return apology("You must fill in all fields.")

        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": userinput[0]}).fetchall()
        if len(user) == 0:
            return apology("Account does not exist.")
        elif not check_password_hash(user[0]["hash"], userinput[1]):
            return apology("Invalid username and/or password.")
        else:
            session["user_id"] = user[0]["id"]
            session["username"] = user[0]["username"]
            return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ REGISTER """

    session.clear()

    if request.method == "POST":

        userinput = [request.form.get("username"), request.form.get("password"), request.form.get("cpassword")]
        for i in userinput:
            if i is None:
                return apology("You must fill in all fields.")

        if db.execute("SELECT * FROM users WHERE username = :username", {"username": userinput[0]}).rowcount == 1:
            return apology("Username already taken.")
        elif userinput[1] != userinput[2]:
            return apology("Password confirmation does not match password.")
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": userinput[0], "hash": generate_password_hash(userinput[1])})
            db.commit()
            return redirect("/login")

    else:
        return render_template("register.html")
