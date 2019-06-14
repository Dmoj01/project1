from flask import Flask, session, render_template, redirect, request
from flask_session import Session
from functools import wraps
from flask import g, request, redirect, url_for
import requests

# Login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Return render_template of error.html with a given message
def apology(message):
    return render_template("error.html", error=message)

# Until s[i] is equal to c, add i to "text", if i is equal to c then break and return text
def until(c, s):
    text = ""
    for i in s:
        if i == c:
            break
        text += i

    return text
