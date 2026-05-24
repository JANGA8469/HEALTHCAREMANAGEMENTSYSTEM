from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "healthcare_secret_key"

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, age TEXT, gender TEXT, phone TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, specialty TEXT, phone TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT, doctor TEXT, date TEXT, time TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT, diagnosis TEXT, prescription TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS billing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT, amount TEXT, status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'patient'
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN CHECK ----------------
def login_required():
    return "user" in session


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("healthcare.db")
        c = conn.cursor()

        c.execute("SELECT password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            session["role"] = user[1]
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form.get("role", "patient")

        conn = sqlite3.connect("healthcare.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"

        conn.close()
        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- HOME ----------------
@app.route("/")
def home():
    if not login_required():
        return redirect("/login")
    return render_template("index.html")


# ---------------- DASHBOARD (WITH BOOKING) ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    # BOOK APPOINTMENT FROM DASHBOARD
    if request.method == "POST":
        c.execute("""
            INSERT INTO appointments (patient, doctor, date, time)
            VALUES (?, ?, ?, ?)
        """, (
            request.form["patient"],
            request.form["doctor"],
            request.form["date"],
            request.form["time"]
        ))
        conn.commit()

    # STATS
    c.execute("SELECT COUNT(*) FROM patients")
    patients = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM doctors")
    doctors = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM appointments")
    appointments_count = c.fetchone()[0]

    # APPOINTMENT LIST
    c.execute("SELECT * FROM appointments ORDER BY id DESC")
    appointments = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        patients=patients,
        doctors=doctors,
        appointments=appointments,
        appointments_count=appointments_count
    )


# ---------------- PATIENTS ----------------
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute("INSERT INTO patients (name, age, gender, phone) VALUES (?, ?, ?, ?)",
                  (request.form["name"], request.form["age"],
                   request.form["gender"], request.form["phone"]))
        conn.commit()
        return redirect("/patients")

    c.execute("SELECT * FROM patients ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("patients.html", patients=data)


# ---------------- DOCTORS ----------------
@app.route("/doctors", methods=["GET", "POST"])
def doctors():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute("INSERT INTO doctors (name, specialty, phone) VALUES (?, ?, ?)",
                  (request.form["name"], request.form["specialty"], request.form["phone"]))
        conn.commit()
        return redirect("/doctors")

    c.execute("SELECT * FROM doctors ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("doctors.html", doctors=data)


# ---------------- APPOINTMENTS ----------------
@app.route("/appointments")
def appointments():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    c.execute("SELECT * FROM appointments ORDER BY id DESC")
    data = c.fetchall()

    conn.close()
    return render_template("appointments.html", appointments=data)


# ---------------- RECORDS ----------------
@app.route("/records", methods=["GET", "POST"])
def records():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""INSERT INTO records (patient, diagnosis, prescription)
                     VALUES (?, ?, ?)""",
                  (request.form["patient"],
                   request.form["diagnosis"],
                   request.form["prescription"]))
        conn.commit()
        return redirect("/records")

    c.execute("SELECT * FROM records ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("records.html", records=data)


# ---------------- BILLING ----------------
@app.route("/billing", methods=["GET", "POST"])
def billing():
    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""INSERT INTO billing (patient, amount, status)
                     VALUES (?, ?, ?)""",
                  (request.form["patient"],
                   request.form["amount"],
                   request.form["status"]))
        conn.commit()
        return redirect("/billing")

    c.execute("SELECT * FROM billing ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("billing.html", bills=data)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)