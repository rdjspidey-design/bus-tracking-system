from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bus_tracking_secret_2026"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # DELETE OLD TABLES (IMPORTANT)
    cursor.execute("DROP TABLE IF EXISTS students")
    cursor.execute("DROP TABLE IF EXISTS drivers")
    cursor.execute("DROP TABLE IF EXISTS buses")
    cursor.execute("DROP TABLE IF EXISTS routes")
    cursor.execute("DROP TABLE IF EXISTS locations")

    # CREATE NEW TABLES
    cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        register_number TEXT,
        password TEXT,
        bus_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        password TEXT,
        bus_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT,
        route_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE locations (
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
            return "Invalid Login ❌"
    return render_template("admin_login.html")

# ---------------- ADMIN PANEL ----------------

@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':

        try:
            # ADD ROUTE
            if 'route_name' in request.form and request.form['route_name']:
                cursor.execute("INSERT INTO routes(route_name) VALUES(?)",
                               (request.form['route_name'],))

            # ADD BUS
            if 'bus_number' in request.form and request.form['bus_number']:
                cursor.execute("INSERT INTO buses(bus_number,route_id) VALUES(?,?)",
                               (request.form['bus_number'],request.form['route_id']))

            # ADD STUDENT
            if 'student_name' in request.form:
                name = request.form['student_name']
                reg = request.form['register_number']
                password = generate_password_hash(request.form['password'])
                bus_id = request.form.get('bus_id')

                if not bus_id:
                    return "❌ Select Bus for student"

                cursor.execute("""
                INSERT INTO students(name,register_number,password,bus_id)
                VALUES(?,?,?,?)
                """,(name,reg,password,bus_id))

            # ADD DRIVER
            if 'driver_name' in request.form:
                name = request.form['driver_name']
                password = generate_password_hash(request.form['password'])
                bus_id = request.form.get('bus_id')

                if not bus_id:
                    return "❌ Select Bus for driver"

                cursor.execute("""
                INSERT INTO drivers(name,password,bus_id)
                VALUES(?,?,?)
                """,(name,password,bus_id))

            conn.commit()

        except Exception as e:
            return f"Error: {str(e)}"

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
            return "Invalid Login ❌"

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
            return "Invalid Login ❌"

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

# ---------------- DRIVER LIST ----------------

@app.route('/drivers')
def drivers():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT drivers.name, buses.bus_number
    FROM drivers
    LEFT JOIN buses ON drivers.bus_id = buses.id
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("drivers.html", drivers=data)

# ---------------- STUDENT LIST ----------------

@app.route('/students')
def students():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT students.name, students.register_number, buses.bus_number
    FROM students
    LEFT JOIN buses ON students.bus_id = buses.id
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("students.html", students=data)

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
