from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bus_tracking_secret_2026"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT,
        route_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        password TEXT,
        bus_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        register_number TEXT,
        password TEXT,
        bus_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER,
        latitude TEXT,
        longitude TEXT,
        time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template("home.html")

# ---------------- ADMIN LOGIN ----------------

@app.route('/admin-login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username']=="admin" and request.form['password']=="admin123":
            session['admin']=True
            return redirect('/admin')
        else:
            return "Invalid Login"
    return render_template("admin_login.html")

# ---------------- ADMIN ----------------

@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':

        if 'route_name' in request.form:
            cursor.execute("INSERT INTO routes(route_name) VALUES(?)",
                           (request.form['route_name'],))

        if 'bus_number' in request.form:
            cursor.execute("INSERT INTO buses(bus_number,route_id) VALUES(?,?)",
                           (request.form['bus_number'],request.form['route_id']))

        if 'student_name' in request.form:
            cursor.execute("""
            INSERT INTO students(name,register_number,password,bus_id)
            VALUES(?,?,?,?)
            """,(
                request.form['student_name'],
                request.form['register_number'],
                generate_password_hash(request.form['password']),
                request.form['bus_id']
            ))

        if 'driver_name' in request.form:
            cursor.execute("""
            INSERT INTO drivers(name,password,bus_id)
            VALUES(?,?,?)
            """,(
                request.form['driver_name'],
                generate_password_hash(request.form['password']),
                request.form['bus_id']
            ))

        conn.commit()
        return redirect('/admin')

    cursor.execute("SELECT * FROM routes")
    routes = cursor.fetchall()

    cursor.execute("SELECT * FROM buses")
    buses = cursor.fetchall()

    conn.close()

    return render_template("index.html",routes=routes,buses=buses)

# ---------------- STUDENT LOGIN ----------------

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT name,password,bus_id FROM students WHERE register_number=?
        """,(request.form['register_number'],))

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1],request.form['password']):
            session['student']=user[0]
            session['bus_id']=user[2]
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():
    if 'student' not in session:
        return redirect('/login')
    return render_template("dashboard.html",name=session['student'])

# ---------------- DRIVER LOGIN ----------------

@app.route('/driver-login', methods=['GET','POST'])
def driver_login():
    if request.method == 'POST':
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id,password,bus_id FROM drivers WHERE name=?",
                       (request.form['name'],))

        d = cursor.fetchone()
        conn.close()

        if d and check_password_hash(d[1],request.form['password']):
            session['driver']=d[0]
            session['bus_id']=d[2]
            return redirect('/driver')
        else:
            return "Invalid"

    return render_template("driver_login.html")

# ---------------- DRIVER PAGE ----------------

@app.route('/driver')
def driver():
    if 'driver' not in session:
        return redirect('/driver-login')
    return render_template("driver.html")

# ---------------- LOCATION UPDATE ----------------

@app.route('/update_location', methods=['POST'])
def update_location():
    if 'driver' not in session:
        return "Unauthorized"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO locations(bus_id,latitude,longitude)
    VALUES(?,?,?)
    """,(session['bus_id'],
         request.form['latitude'],
         request.form['longitude']))

    conn.commit()
    conn.close()
    return "OK"

# ---------------- GET LOCATION ----------------

@app.route('/get_location')
def get_location():
    if 'bus_id' not in session:
        return jsonify({"error":"no"})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT latitude,longitude FROM locations
    WHERE bus_id=?
    ORDER BY id DESC LIMIT 1
    """,(session['bus_id'],))

    data = cursor.fetchone()
    conn.close()

    if data:
        return jsonify({"lat":float(data[0]),"lng":float(data[1])})

    return jsonify({"error":"no data"})

# ---------------- MAP ----------------

@app.route('/map')
def map():
    return render_template("map.html")

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
