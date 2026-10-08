from flask import Flask, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

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
style = "<link rel='stylesheet' href='/static/style.css'>"
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
        try:
            with sqlite3.connect('carpool.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?, ?)",
                          (request.form['username'], request.form['password']))
        except:
            return style + "<h3>User already exists</h3><a href='/register'>Back</a>"

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
        with sqlite3.connect('carpool.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (request.form['username'], request.form['password']))
            user = c.fetchone()

        if user:
            session['user'] = request.form['username']
            return redirect('/dashboard')
        else:
            return style + "<h3>Invalid Login</h3><a href='/login'>Try Again</a>"

    return style + """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br>
        <input name="password" type="password" placeholder="Password"><br>
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
    <a href='/view_rides'>View All Rides</a>
    <a href='/my_rides'>My Rides</a>
    <a href='/logout'>Logout</a>
    """

# ---------------- POST RIDE ----------------
@app.route('/post_ride', methods=['GET', 'POST'])
def post_ride():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        with sqlite3.connect('carpool.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO rides (username, source, destination, seats) VALUES (?, ?, ?, ?)",
                      (session['user'], request.form['source'],
                       request.form['destination'], int(request.form['seats'])))

        return redirect('/view_rides')

    return style + """
    <h2>Post Ride</h2>
    <form method="POST">
        <input name="source" placeholder="Source" required><br>
        <input name="destination" placeholder="Destination" required><br>
        <input name="seats" placeholder="Seats" required><br>
        <button type="submit">Post</button>
    </form>
    """

# ---------------- VIEW RIDES ----------------
@app.route('/view_rides')
def view_rides():
    if 'user' not in session:
        return redirect('/login')

    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, source, destination, seats FROM rides")
        rides = c.fetchall()

    output = "<h2>All Rides 🚗</h2>"

    for r in rides:
        output += f"""
        <div class='card'>
        <b>{r[1]}</b><br>
        {r[2]} → {r[3]}<br>
        Seats: {r[4]}<br>
        """

        # Booking
        if r[1] != session['user'] and r[4] > 0:
            output += f"<a href='/book/{r[0]}'><button>Book</button></a>"

        # Delete own ride
        if r[1] == session['user']:
            output += f"<a href='/delete/{r[0]}'><button>Delete</button></a>"

        output += "</div>"

    output += "<a href='/dashboard'>Back</a>"

    return style + output

# ---------------- BOOK RIDE ----------------
@app.route('/book/<int:ride_id>')
def book(ride_id):
    if 'user' not in session:
        return redirect('/login')

    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()
        c.execute("SELECT seats FROM rides WHERE id=?", (ride_id,))
        ride = c.fetchone()

        if ride and ride[0] > 0:
            c.execute("UPDATE rides SET seats = seats - 1 WHERE id=?", (ride_id,))
            conn.commit()

    return redirect('/view_rides')

# ---------------- DELETE RIDE ----------------
@app.route('/delete/<int:ride_id>')
def delete(ride_id):
    if 'user' not in session:
        return redirect('/login')

    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM rides WHERE id=? AND username=?",
                  (ride_id, session['user']))
        conn.commit()

    return redirect('/view_rides')

# ---------------- MY RIDES ----------------
@app.route('/my_rides')
def my_rides():
    if 'user' not in session:
        return redirect('/login')

    with sqlite3.connect('carpool.db') as conn:
        c = conn.cursor()
        c.execute("SELECT source, destination, seats FROM rides WHERE username=?",
                  (session['user'],))
        rides = c.fetchall()

    output = "<h2>My Rides 🚗</h2>"

    for r in rides:
        output += f"<p>{r[0]} → {r[1]} | Seats: {r[2]}</p>"

    output += "<a href='/dashboard'>Back</a>"

    return style + output


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)