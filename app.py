from flask import Flask, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"   # required for session

# ---------------- DATABASE ----------------
def init_db():
    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS rides (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        source TEXT,
                        destination TEXT,
                        seats INTEGER
                    )''')

init_db()

# ---------------- CSS ----------------
style = """
<style>
body {font-family: Arial; background:#f2f2f2; text-align:center;}
h1,h2 {color:#333;}
form {background:white; padding:20px; margin:20px auto; width:260px; border-radius:10px;}
input {margin:10px; padding:8px; width:80%;}
button {padding:8px 15px; background:blue; color:white; border:none; border-radius:5px;}
a {display:block; margin:10px; color:blue; text-decoration:none;}
</style>
"""

# ---------------- HOME ----------------
@app.route('/')
def home():
    return style + """
    <h1>🚗 Carpooling System</h1>
    <a href='/login'>Login</a>
    <a href='/register'>Register</a>
    """

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            return style + "<h3>All fields required</h3><a href='/register'>Back</a>"

        try:
            with sqlite3.connect('carpool.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        except sqlite3.IntegrityError:
            return style + "<h3>User already exists</h3><a href='/register'>Try Again</a>"

        return redirect('/login')

    return style + """
    <h2>Register</h2>
    <form method="POST">
        <input name="username" placeholder="Username" required><br>
        <input name="password" type="password" placeholder="Password" required><br>
        <button type="submit">Register</button>
    </form>
    """

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('carpool.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            return style + "<h3>Invalid Login</h3><a href='/login'>Try Again</a>"

    return style + """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username" required><br>
        <input name="password" type="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
    """

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return style + f"""
    <h1>Welcome {session['user']} 🚗</h1>
    <a href='/post_ride'>Post Ride</a>
    <a href='/view_rides'>View Rides</a>
    <a href='/logout'>Logout</a>
    """

# ---------------- POST RIDE ----------------
@app.route('/post_ride', methods=['GET', 'POST'])
def post_ride():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        seats = request.form['seats']

        if not source or not destination or not seats.isdigit():
            return style + "<h3>Invalid input</h3><a href='/post_ride'>Try Again</a>"

        with sqlite3.connect('carpool.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO rides (username, source, destination, seats) VALUES (?, ?, ?, ?)",
                      (session['user'], source, destination, int(seats)))

        return redirect('/view_rides')

    return style + """
    <h2>Post Ride 🚗</h2>
    <form method="POST">
        <input name="source" placeholder="Source" required><br>
        <input name="destination" placeholder="Destination" required><br>
        <input name="seats" placeholder="Seats" required><br>
        <button type="submit">Post Ride</button>
    </form>
    """

# ---------------- VIEW RIDES ----------------
@app.route('/view_rides')
def view_rides():
    if 'user' not in session:
        return redirect('/login')

    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()
        c.execute("SELECT username, source, destination, seats FROM rides")
        rides = c.fetchall()

    output = "<h2>Available Rides 🚗</h2>"

    if not rides:
        output += "<p>No rides available</p>"

    for r in rides:
        output += f"<p><b>{r[0]}</b>: {r[1]} → {r[2]} | Seats: {r[3]}</p>"

    output += "<a href='/dashboard'>Back</a>"

    return style + output


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)