from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bus_tracking_secret_2026"


# ---------------- DATABASE INITIALIZATION ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT NOT NULL,
        route_id INTEGER,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        register_number TEXT NOT NULL,
        password TEXT NOT NULL,
        route_id INTEGER,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER,
        latitude TEXT,
        longitude TEXT,
        time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bus_id) REFERENCES buses(id)
    )
    """)

    conn.commit()
    conn.close()


# ---------------- ADMIN LOGIN ----------------

@app.route('/admin-login', methods=['GET','POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/')

        else:
            return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- DRIVER LOGIN ----------------

@app.route('/driver-login', methods=['GET','POST'])
def driver_login():

    if request.method == 'POST':

        password = request.form['password']

        if password == "driver123":
            session['driver'] = True
            return redirect('/driver')

        else:
            return "Invalid Driver Login"

    return render_template("driver_login.html")


# ---------------- ADMIN HOME ----------------

@app.route('/', methods=['GET', 'POST'])
def home():

    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':

        if 'route_name' in request.form:
            route_name = request.form['route_name']
            cursor.execute("INSERT INTO routes (route_name) VALUES (?)", (route_name,))
            conn.commit()

        if 'bus_number' in request.form:
            bus_number = request.form['bus_number']
            route_id = request.form['route_id']
            cursor.execute("INSERT INTO buses (bus_number, route_id) VALUES (?, ?)", (bus_number, route_id))
            conn.commit()

        if 'student_name' in request.form:
            name = request.form['student_name']
            reg_no = request.form['register_number']
            password = generate_password_hash(request.form['password'])
            route_id = request.form['route_id']

            cursor.execute("""
            INSERT INTO students (name, register_number, password, route_id)
            VALUES (?, ?, ?, ?)
            """, (name, reg_no, password, route_id))

            conn.commit()

        return redirect('/')

    cursor.execute("SELECT * FROM routes")
    routes = cursor.fetchall()

    cursor.execute("""
    SELECT buses.bus_number, routes.route_name
    FROM buses
    JOIN routes ON buses.route_id = routes.id
    """)
    buses = cursor.fetchall()

    conn.close()

    return render_template("index.html", routes=routes, buses=buses)


# ---------------- STUDENT LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        reg_no = request.form['register_number']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT students.name, students.password, routes.route_name
        FROM students
        JOIN routes ON students.route_id = routes.id
        WHERE students.register_number=?
        """, (reg_no,))

        student = cursor.fetchone()
        conn.close()

        if student and check_password_hash(student[1], password):

            session['student_name'] = student[0]
            session['route_name'] = student[2]

            return redirect('/dashboard')

        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    if 'student_name' in session:
        return render_template(
            "dashboard.html",
            name=session['student_name'],
            route=session['route_name']
        )

    return redirect('/login')


# ---------------- DRIVER PAGE ----------------

@app.route('/driver')
def driver():

    if 'driver' not in session:
        return redirect('/driver-login')

    return render_template("driver.html")


# ---------------- DRIVER LOCATION UPDATE ----------------

@app.route('/update_location', methods=['POST'])
def update_location():

    bus_id = request.form['bus_id']
    latitude = request.form['latitude']
    longitude = request.form['longitude']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO locations (bus_id, latitude, longitude)
    VALUES (?, ?, ?)
    """, (bus_id, latitude, longitude))

    conn.commit()
    conn.close()

    return "OK"


# ---------------- GET BUS LOCATION ----------------

@app.route('/get_location')
def get_location():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT latitude, longitude
    FROM locations
    ORDER BY id DESC
    LIMIT 1
    """)

    data = cursor.fetchone()
    conn.close()

    if data:
        return {"lat": data[0], "lng": data[1]}
    else:
        return {"lat": 0, "lng": 0}


# ---------------- MAP PAGE ----------------

@app.route('/map')
def map():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT latitude, longitude
    FROM locations
    ORDER BY id DESC
    LIMIT 1
    """)

    location = cursor.fetchone()
    conn.close()

    return render_template("map.html", location=location)


# ---------------- BUS LIST ----------------

@app.route('/buses')
def buses():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses")
    buses = cursor.fetchall()

    conn.close()

    return render_template("buses.html", buses=buses)


# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin-login')


# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True)from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bus_tracking_secret_2026"


# ---------------- DATABASE INITIALIZATION ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT NOT NULL,
        route_id INTEGER,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        register_number TEXT NOT NULL,
        password TEXT NOT NULL,
        route_id INTEGER,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER,
        latitude TEXT,
        longitude TEXT,
        time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bus_id) REFERENCES buses(id)
    )
    """)

    conn.commit()
    conn.close()


# ---------------- ADMIN LOGIN ----------------

@app.route('/admin-login', methods=['GET','POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/')

        else:
            return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- DRIVER LOGIN ----------------

@app.route('/driver-login', methods=['GET','POST'])
def driver_login():

    if request.method == 'POST':

        password = request.form['password']

        if password == "driver123":
            session['driver'] = True
            return redirect('/driver')

        else:
            return "Invalid Driver Login"

    return render_template("driver_login.html")


# ---------------- ADMIN HOME ----------------

@app.route('/', methods=['GET', 'POST'])
def home():

    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':

        if 'route_name' in request.form:
            route_name = request.form['route_name']
            cursor.execute("INSERT INTO routes (route_name) VALUES (?)", (route_name,))
            conn.commit()

        if 'bus_number' in request.form:
            bus_number = request.form['bus_number']
            route_id = request.form['route_id']
            cursor.execute("INSERT INTO buses (bus_number, route_id) VALUES (?, ?)", (bus_number, route_id))
            conn.commit()

        if 'student_name' in request.form:
            name = request.form['student_name']
            reg_no = request.form['register_number']
            password = generate_password_hash(request.form['password'])
            route_id = request.form['route_id']

            cursor.execute("""
            INSERT INTO students (name, register_number, password, route_id)
            VALUES (?, ?, ?, ?)
            """, (name, reg_no, password, route_id))

            conn.commit()

        return redirect('/')

    cursor.execute("SELECT * FROM routes")
    routes = cursor.fetchall()

    cursor.execute("""
    SELECT buses.bus_number, routes.route_name
    FROM buses
    JOIN routes ON buses.route_id = routes.id
    """)
    buses = cursor.fetchall()

    conn.close()

    return render_template("index.html", routes=routes, buses=buses)


# ---------------- STUDENT LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        reg_no = request.form['register_number']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT students.name, students.password, routes.route_name
        FROM students
        JOIN routes ON students.route_id = routes.id
        WHERE students.register_number=?
        """, (reg_no,))

        student = cursor.fetchone()
        conn.close()

        if student and check_password_hash(student[1], password):

            session['student_name'] = student[0]
            session['route_name'] = student[2]

            return redirect('/dashboard')

        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    if 'student_name' in session:
        return render_template(
            "dashboard.html",
            name=session['student_name'],
            route=session['route_name']
        )

    return redirect('/login')


# ---------------- DRIVER PAGE ----------------

@app.route('/driver')
def driver():

    if 'driver' not in session:
        return redirect('/driver-login')

    return render_template("driver.html")


# ---------------- DRIVER LOCATION UPDATE ----------------

@app.route('/update_location', methods=['POST'])
def update_location():

    bus_id = request.form['bus_id']
    latitude = request.form['latitude']
    longitude = request.form['longitude']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO locations (bus_id, latitude, longitude)
    VALUES (?, ?, ?)
    """, (bus_id, latitude, longitude))

    conn.commit()
    conn.close()

    return "OK"


# ---------------- GET BUS LOCATION ----------------

@app.route('/get_location')
def get_location():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT latitude, longitude
    FROM locations
    ORDER BY id DESC
    LIMIT 1
    """)

    data = cursor.fetchone()
    conn.close()

    if data:
        return {"lat": data[0], "lng": data[1]}
    else:
        return {"lat": 0, "lng": 0}


# ---------------- MAP PAGE ----------------

@app.route('/map')
def map():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT latitude, longitude
    FROM locations
    ORDER BY id DESC
    LIMIT 1
    """)

    location = cursor.fetchone()
    conn.close()

    return render_template("map.html", location=location)


# ---------------- BUS LIST ----------------

@app.route('/buses')
def buses():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses")
    buses = cursor.fetchall()

    conn.close()

    return render_template("buses.html", buses=buses)


# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin-login')


# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True)
