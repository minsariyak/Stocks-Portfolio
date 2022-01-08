# export API_KEY=pk_4efb7d8036a24e90b01eefefe612818b
import os
import sys

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")
os.environ["API_KEY"] = "pk_4efb7d8036a24e90b01eefefe612818b"


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # get all fields from stocks table for current user
    stocks = db.execute("SELECT * FROM stocks WHERE user_id = :current_user", current_user=session["user_id"])
    # get sum of total field
    total_stocks = db.execute("SELECT SUM(total) AS total FROM stocks WHERE user_id = :current_user",
                              current_user=session["user_id"])
    # get amount of cash for the current user
    cash = db.execute("SELECT cash FROM users WHERE id = :current_user", current_user=session["user_id"])

    # calculate grand total of cash
    if total_stocks[0]["total"] is None:
        all_total = cash[0]["cash"] + 0
    else:
        all_total = cash[0]["cash"] + total_stocks[0]["total"]
    cash_total = cash[0]["cash"]
    # get number of rows in stocks table
    stocks_length = len(stocks)

    return render_template("index.html", stocks=stocks, stocks_length=stocks_length, cash_total="{:.2f}".format(cash_total), all_total="{:.2f}".format(all_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    # if it is a GET request, render a form to enable the user to specify what to buy
    if request.method == 'GET':
        return render_template("buy.html")
    # otherwise do the following on a POST request
    else:
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Can't leave symbol blank")

        shares = request.form.get("shares")
        if not shares:
            return apology("Can't leave shares blank")
        try:
            if int(shares) <= 0:
                return apology("Shares must be greater than 0")
        except:
            return apology("Shares must be an integer")

        stock = lookup(symbol)
        if stock == None:
            return apology("Symbol not found")

        # getting the current user's cash from database, Row returned is a dict in a list [{cash: 10000}])
        cash = db.execute("SELECT cash FROM users WHERE id = :current_user", current_user=session["user_id"])
        # converting return value to a float
        float_cash = float(cash[0]["cash"])

        # updating cash for the current user if he can afford it
        cost = int(shares) * stock["price"]
        if float_cash >= cost:
            db.execute("UPDATE users SET cash = :new_cash WHERE id = :current_user",
                       new_cash=float_cash-cost, current_user=session["user_id"])
            db.execute("INSERT INTO stocks (user_id, symbol, name, shares, price, total) VALUES (:user_id, :symbol, :name, :shares, :price, :total)",
                       user_id=session["user_id"], symbol=symbol, name=stock["name"], shares=shares, price=stock["price"], total=cost)
            db.execute("INSERT INTO history (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares, :price, CURRENT_TIMESTAMP)",
                       user_id=session["user_id"], symbol=symbol, shares=shares, price=stock["price"])
            return redirect("/")
        else:
            return apology("You donot have enough cash")

        # stocks = db.execute("SELECT symbol FROM stocks WHERE id = :current_user", current_user=session["user_id"])


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # get all fields from history table
    history = db.execute("SELECT * FROM history WHERE user_id = :id", id=session["user_id"])

    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    # show form to get stock details
    if request.method == 'GET':
        return render_template("quote.html")
    # show quote after searching
    else:
        symbol = request.form.get("symbol")
        stocks = lookup(symbol)
        if stocks == None:
            return apology("No stocks found")
        else:
            return render_template("quoted.html", stocks=stocks)


@app.route("/register", methods=["GET", "POST"])
def register():
    # show form to gather user details
    if request.method == 'GET':
        return render_template("register.html")
    # gather user details and save to database
    else:
        existing_users = db.execute("SELECT username FROM users")
        username = request.form.get("username")
        if not username:
            return apology("Username can't be empty")

        # check if username exists already
        for i in range(len(existing_users)):
            if username == existing_users[i]["username"]:
                return apology("Username taken, choose another one please")

        # confirm passwords match
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password:
            return apology("Password cant be empty")
        if not confirmation:
            return apology("Please confirm your password")
        if password != confirmation:
            return apology("Passwords donot match")

        # convert password to hash and save to database
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)

        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # show form to get details of stock to be sold
    if request.method == 'GET':
        stocks = db.execute("SELECT symbol FROM stocks WHERE user_id = :id", id=session["user_id"])
        return render_template("sell.html", stocks=stocks)
    # get details from the form and update user details in database (hence representing a sale)
    else:
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Please select a symbol")

        # error checking
        shares = request.form.get("shares")
        if not shares:
            return apology("Please enter number of shares to sell")
        if int(shares) < 0:
            return apology("Share amount cannot be negative")
        current_shares = db.execute("SELECT shares FROM stocks WHERE user_id = :id AND symbol = :symbol",
                                    id=session["user_id"], symbol=symbol)
        if int(shares) > current_shares[0]["shares"]:
            return apology("You donot own the requested amount of shares")
        if current_shares[0]["shares"] == 0:
            return apology("You donot own any shares for the selected stock")

        # lookup stock price and calculate sale amount
        stocks = lookup(symbol)
        stock_price = stocks["price"]
        sell_value = stock_price * int(shares)

        # update necessary tables in the database and record the transaction
        db.execute("UPDATE stocks SET shares = :shares, price = :price WHERE user_id = :id AND symbol = :symbol",
                   shares=current_shares[0]["shares"]-int(shares), price=stock_price, id=session["user_id"], symbol=symbol)
        current = db.execute("SELECT * FROM stocks WHERE user_id = :id AND symbol = :symbol", id=session["user_id"], symbol=symbol)
        total = current[0]["price"] * current[0]["shares"]
        db.execute("UPDATE stocks SET total = :total WHERE user_id = :id AND symbol = :symbol",
                   total=total, id=session["user_id"], symbol=symbol)
        current_cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=current_cash[0]["cash"]+sell_value, id=session["user_id"])
        db.execute("INSERT INTO history (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares, :price, CURRENT_TIMESTAMP)",
                   user_id=session["user_id"], symbol=symbol, shares=int(shares)*-1, price=stock_price)

        return redirect("/")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Increase user's cash"""
    # show form to input cash amount
    if request.method == "GET":
        return render_template("cash.html")
    # add cash and update user table
    else:
        cash = int(request.form.get("cash"))
        # get current cash
        current_cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        # add amount from form to current cash
        updated_cash = current_cash[0]["cash"] + cash
        # update database table
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=updated_cash, id=session["user_id"])

        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
