from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import pandas as pd
import joblib
from datetime import datetime
model = joblib.load("model.pkl")

app = Flask(__name__)

app.secret_key = "AI_PREDICTIVE_MAINTENANCE_2026"


# =========================
# Load AI Model
# =========================

model = joblib.load("model.pkl")


# =========================
# Database
# =========================

DATABASE = "database.db"


def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn



# =========================
# Create Tables
# =========================

def create_tables():

    conn = get_db()

    cur = conn.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT UNIQUE,

        password TEXT

    )
    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT,

        temperature REAL,

        vibration REAL,

        pressure REAL,

        runtime REAL,

        result TEXT,

        date TEXT

    )
    """)



    conn.commit()

    conn.close()



create_tables()



# =========================
# Login
# =========================

@app.route("/")
def login():

    return render_template("login.html")



# =========================
# Register
# =========================

@app.route("/register", methods=["GET","POST"])
def register():


    if request.method == "POST":


        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]



        conn = get_db()

        cur = conn.cursor()



        try:

            cur.execute(
                """
                INSERT INTO users(name,email,password)
                VALUES(?,?,?)
                """,
                (name,email,password)
            )


            conn.commit()


            flash("Registration Successful")

            return redirect(url_for("login"))


        except sqlite3.IntegrityError:


            flash("Email already exists")



        finally:

            conn.close()



    return render_template("register.html")




# =========================
# Login Process
# =========================

@app.route("/login", methods=["POST"])
def login_process():


    email = request.form["email"]

    password = request.form["password"]



    conn = get_db()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT * FROM users
        WHERE email=? AND password=?

        """,
        (email,password)
    )


    user = cur.fetchone()


    conn.close()



    if user:


        session["name"] = user["name"]

        session["email"] = user["email"]


        return redirect(url_for("dashboard"))



    flash("Invalid Email or Password")


    return redirect(url_for("login"))




# =========================
# Dashboard
# =========================

@app.route("/dashboard")
def dashboard():

    if "email" not in session:
        return redirect(url_for("login"))


    conn = get_db()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT result, temperature, vibration, pressure, runtime, date
        FROM predictions
        WHERE email=?
        ORDER BY id DESC
        """,
        (session["email"],)
    )


    rows = cur.fetchall()

    conn.close()



    total = len(rows)

    healthy = 0
    warning = 0
    critical = 0


    temperature = []
    vibration = []
    health = []
    risk = []



    for row in rows:


        # Status Count

        if row["result"] == "Healthy":
            healthy += 1

        elif row["result"] == "Warning":
            warning += 1

        elif row["result"] == "Critical":
            critical += 1



        # Graph Data

        temperature.append(row["temperature"])
        vibration.append(row["vibration"])



        # Health Score Calculation

        score = 100 - (
            (row["temperature"]/120)*30 +
            (row["vibration"]/100)*30 +
            (row["pressure"]/100)*20 +
            (row["runtime"]/1200)*20
        )


        score = round(max(0,score),2)

        health.append(score)



        risk.append(round(100-score,2))



    data = {

        "total": total,

        "healthy": healthy,

        "warning": warning,

        "critical": critical,


        "temperature": temperature,

        "vibration": vibration,

        "health": health,

        "risk": risk

    }



    return render_template(
        "dashboard.html",
        user=session["name"],
        data=data
    )



# =========================
# Manual Prediction
# =========================

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    result = None
    confidence = None


    if request.method == "POST":

        temperature = float(request.form["temperature"])
        vibration = float(request.form["vibration"])
        pressure = float(request.form["pressure"])
        runtime = float(request.form["runtime"])


        sample = pd.DataFrame(
            [[temperature, vibration, pressure, runtime]],
            columns=[
                "Temperature",
                "Vibration",
                "Pressure",
                "Runtime"
            ]
        )


        result = model.predict(sample)[0]


        if hasattr(model, "predict_proba"):

            probability = model.predict_proba(sample)[0]

            confidence = round(
                max(probability)*100,2
            )


        conn = get_db()

        cur = conn.cursor()


        cur.execute(
            """
            INSERT INTO predictions
            (email,temperature,vibration,pressure,runtime,result,date)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                session["email"],
                temperature,
                vibration,
                pressure,
                runtime,
                result,
                datetime.now().strftime("%d-%m-%Y %H:%M")
            )
        )


        conn.commit()
        conn.close()



    return render_template(
        "prediction.html",
        result=result,
        confidence=confidence
    )



# =========================
# CSV Prediction
# =========================

@app.route("/csv_prediction", methods=["POST"])
def csv_prediction():

    predictions = []


    file = request.files.get("file")


    if file:

        df = pd.read_csv(file)


        features = df[
            [
                "Temperature",
                "Vibration",
                "Pressure",
                "Runtime"
            ]
        ]


        result = model.predict(features)


        df["Result"] = result


        predictions = df.to_dict(
            orient="records"
        )


    return render_template(
        "prediction.html",
        predictions=predictions
    )

# =========================
# Reports
# =========================

@app.route("/reports")
def reports():


    if "email" not in session:

        return redirect(url_for("login"))



    conn = get_db()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT * FROM predictions
        WHERE email=?
        ORDER BY id DESC

        """,

        (session["email"],)

    )



    reports = cur.fetchall()



    conn.close()



    return render_template(

        "reports.html",

        reports=reports

    )




# =========================
# Profile
# =========================

@app.route("/profile")
def profile():


    if "email" not in session:

        return redirect(url_for("login"))



    return render_template(

        "profile.html",

        name=session["name"],

        email=session["email"]

    )





# =========================
# Logout
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))




# =========================
# Run
# =========================

if __name__ == "__main__":

    app.run(debug=True)