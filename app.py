from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import bcrypt
import os
import re
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = 'unicafe_secret_key_2026'
CORS(app, supports_credentials=True)

DB_PATH = 'unicafe.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS cafes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            owner_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','owner','delivery')),
            cafe_id INTEGER,
            roll_no TEXT,
            cnic TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cafe_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT DEFAULT 'https://via.placeholder.com/150x100?text=Food',
            available INTEGER DEFAULT 1,
            category TEXT DEFAULT 'general',
            FOREIGN KEY(cafe_id) REFERENCES cafes(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            cafe_id INTEGER NOT NULL,
            delivery_boy_id INTEGER,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            room_no TEXT,
            special_instructions TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            delivered_at TEXT,
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(cafe_id) REFERENCES cafes(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_time REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            cafe_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            start_date TEXT,
            end_date TEXT,
            verified_by_owner INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(cafe_id) REFERENCES cafes(id)
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            complaint_text TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL UNIQUE,
            student_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
    ''')

    # Seed Red Cafe and Blue Cafe with owners
    c.execute("SELECT id FROM cafes WHERE name='Red Cafe'")
    if not c.fetchone():
        pw = bcrypt.hashpw(b'redcafe123', bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                  ('Red Cafe Owner','redcafe@unicafe.com',pw,'owner'))
        owner_id = c.lastrowid
        c.execute("INSERT INTO cafes(name,owner_id) VALUES(?,?)", ('Red Cafe', owner_id))
        cafe_id = c.lastrowid
        c.execute("UPDATE users SET cafe_id=? WHERE id=?", (cafe_id, owner_id))
        # seed items
        items = [
            ('Biryani','A flavorful rice dish',180,'lunch'),
            ('Burger','Crispy chicken burger',150,'lunch'),
            ('Chai','Hot doodh pati chai',30,'beverages'),
            ('Paratha Roll','Crispy paratha with filling',100,'breakfast'),
            ('Dahi Bhalla','Cool yogurt snack',60,'snacks'),
            ('Sandwich','Grilled club sandwich',120,'breakfast'),
            ('Cold Coffee','Chilled coffee blend',80,'beverages'),
            ('Samosa','Fried potato snack',20,'snacks'),
        ]
        for name, desc, price, cat in items:
            c.execute("INSERT INTO items(cafe_id,name,price,description,category) VALUES(?,?,?,?,?)",
                      (cafe_id, name, price, desc, cat))

    c.execute("SELECT id FROM cafes WHERE name='Blue Cafe'")
    if not c.fetchone():
        pw = bcrypt.hashpw(b'bluecafe123', bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                  ('Blue Cafe Owner','bluecafe@unicafe.com',pw,'owner'))
        owner_id = c.lastrowid
        c.execute("INSERT INTO cafes(name,owner_id) VALUES(?,?)", ('Blue Cafe', owner_id))
        cafe_id = c.lastrowid
        c.execute("UPDATE users SET cafe_id=? WHERE id=?", (cafe_id, owner_id))
        items = [
            ('Chicken Karahi','Spicy chicken karahi',200,'lunch'),
            ('Zinger Burger','Spicy zinger burger',170,'lunch'),
            ('Green Tea','Refreshing green tea',25,'beverages'),
            ('Omelette','Egg omelette with bread',70,'breakfast'),
            ('French Fries','Crispy golden fries',80,'snacks'),
            ('Pizza Slice','Cheesy pizza slice',130,'lunch'),
            ('Mango Shake','Fresh mango milkshake',90,'beverages'),
            ('Puff Pastry','Flaky chicken puff',50,'snacks'),
        ]
        for name, desc, price, cat in items:
            c.execute("INSERT INTO items(cafe_id,name,price,description,category) VALUES(?,?,?,?,?)",
                      (cafe_id, name, price, desc, cat))

    conn.commit()
    conn.close()

# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    d = request.json
    role = d.get('role','student')
    name = d.get('name','').strip()
    if( role == "student" or role == "owner" or role == "delivery" ) and (len(name)<2 or len(name) >100):
        return jsonify({'error': 'Name must co ntain atleast 2 characters and atmost 100 characters.'}), 400
    
    
    email = d.get('email','').strip().lower()
    pattern = r'^[a-zA-Z0-9]+@isb\.nu\.com\.pk$'
    if role == "student" and not re.match(pattern, email):
        return jsonify({'error': 'Only @isb.nu.edu.pk emails are allowed'}), 400

    password = d.get('password','')
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).+$'

    if( role == "student" or role == "owner" or role == "delivery" ) and (not re.fullmatch(pattern, password)):
        return jsonify({'error': 'Weak Password'}), 400
    
    
    roll_no = d.get('roll_no','')
    pattern = r'^\d{2}[A-Za-z]-\d{4}$'
    if role == "student" and not re.fullmatch(pattern, roll_no):
        return jsonify({'error': 'Roll number must be in format 12X-1111'}), 400
    
    cnic = d.get('cnic','')
    if(role == "owner" or role == "delivery" ) and not (cnic.isdigit() and len(cnic) == 13):
        return jsonify({'error': 'CNIC must be exactly 13 digits'}), 400
    cafe_id = d.get('cafe_id')
    cafe_name = d.get('cafe_name','').strip()

    if not name or not email or not password:
        return jsonify({'error':'All fields required'}), 400

    
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            return jsonify({'error':'Email already registered'}), 400

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        if role == 'owner':
            if not cafe_name:
                return jsonify({'error':'Cafe name required'}), 400
            
            pattern = r'^[a-zA-Z0-9]+@unicafe\.com$'
            if not re.match(pattern, email):
                return jsonify({'error': 'Only @unicafe.com emails are allowed'}), 400
            
            c.execute("SELECT id FROM cafes WHERE name=?", (cafe_name,))
            if c.fetchone():
                return jsonify({'error':'Cafe name already taken'}), 400
            c.execute("INSERT INTO users(name,email,password_hash,role,cnic) VALUES(?,?,?,?,?)",
                      (name,email,pw_hash,'owner',cnic))
            uid = c.lastrowid
            c.execute("INSERT INTO cafes(name,owner_id) VALUES(?,?)", (cafe_name, uid))
            new_cafe_id = c.lastrowid
            c.execute("UPDATE users SET cafe_id=? WHERE id=?", (new_cafe_id, uid))

        elif role == 'delivery':
            if not cafe_id:
                return jsonify({'error':'Select a cafe'}), 400
            c.execute("INSERT INTO users(name,email,password_hash,role,cafe_id,cnic) VALUES(?,?,?,?,?,?)",
                      (name,email,pw_hash,'delivery',cafe_id,cnic))

        else:  # student
            c.execute("INSERT INTO users(name,email,password_hash,role,roll_no) VALUES(?,?,?,?,?)",
                      (name,email,pw_hash,'student',roll_no))

        conn.commit()
        return jsonify({'message':'Registered successfully'}), 201
    except Exception as e:
        return jsonify({'error':str(e)}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    email = d.get('email','').strip().lower()
    password = d.get('password','')

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        if not user:
            return jsonify({'error':'Invalid credentials'}), 401
        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({'error':'Invalid credentials'}), 401

        session['user_id'] = user['id']
        session['role'] = user['role']
        return jsonify({
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'cafe_id': user['cafe_id'],
            'roll_no': user['roll_no']
        })
    finally:
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message':'Logged out'})

@app.route('/api/me', methods=['GET'])
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error':'Not logged in'}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id,name,email,role,cafe_id,roll_no FROM users WHERE id=?", (uid,))
    u = c.fetchone()
    conn.close()
    if not u:
        return jsonify({'error':'User not found'}), 404
    return jsonify(dict(u))

# ─── CAFES ───────────────────────────────────────────────────────────────────

@app.route('/api/cafes', methods=['GET'])
def get_cafes():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM cafes")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# ─── ITEMS ───────────────────────────────────────────────────────────────────

@app.route('/api/items', methods=['GET'])
def get_items():
    cafe_id = request.args.get('cafe_id')
    conn = get_db()
    c = conn.cursor()
    if cafe_id:
        c.execute("SELECT * FROM items WHERE cafe_id=?", (cafe_id,))
    else:
        c.execute("SELECT * FROM items")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/items', methods=['POST'])
def add_item():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    d = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("INSERT INTO items(cafe_id,name,price,description,image,available,category) VALUES(?,?,?,?,?,?,?)",
              (cafe_id, d['name'], d['price'], d.get('description',''), d.get('image','https://via.placeholder.com/150x100?text=Food'), d.get('available',1), d.get('category','general')))
    conn.commit()
    conn.close()
    return jsonify({'message':'Item added'}), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    d = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("UPDATE items SET name=?,price=?,description=?,image=?,available=?,category=? WHERE id=? AND cafe_id=?",
              (d['name'],d['price'],d.get('description',''),d.get('image','https://via.placeholder.com/150x100?text=Food'),d.get('available',1),d.get('category','general'),item_id,cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Item updated'})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("DELETE FROM items WHERE id=? AND cafe_id=?", (item_id, cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Item deleted'})

# ─── ORDERS ──────────────────────────────────────────────────────────────────

@app.route('/api/orders', methods=['GET'])
def get_orders():
    uid = session.get('user_id')
    role = session.get('role')
    if not uid:
        return jsonify({'error':'Not logged in'}), 401
    conn = get_db()
    c = conn.cursor()
    if role == 'student':
        c.execute("""SELECT o.*, ca.name as cafe_name FROM orders o 
                     JOIN cafes ca ON o.cafe_id=ca.id 
                     WHERE o.student_id=? ORDER BY o.created_at DESC""", (uid,))
    elif role == 'owner':
        c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
        cafe_id = c.fetchone()['cafe_id']
        c.execute("""SELECT o.*, u.name as student_name, u.roll_no, ca.name as cafe_name 
                     FROM orders o JOIN users u ON o.student_id=u.id
                     JOIN cafes ca ON o.cafe_id=ca.id
                     WHERE o.cafe_id=? ORDER BY o.created_at DESC""", (cafe_id,))
    elif role == 'delivery':
        c.execute("""SELECT o.*, u.name as student_name, ca.name as cafe_name 
                     FROM orders o JOIN users u ON o.student_id=u.id
                     JOIN cafes ca ON o.cafe_id=ca.id
                     WHERE o.delivery_boy_id=? ORDER BY o.created_at DESC""", (uid,))
    rows = []
    for r in c.fetchall():
        order = dict(r)
        c.execute("""SELECT oi.*, i.name as item_name FROM order_items oi 
                     JOIN items i ON oi.item_id=i.id WHERE oi.order_id=?""", (order['id'],))
        order['items'] = [dict(x) for x in c.fetchall()]
        rows.append(order)
    conn.close()
    return jsonify(rows)

@app.route('/api/orders', methods=['POST'])
def place_order():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'student':
        return jsonify({'error':'Students only'}), 403
    d = request.json
    items = d.get('items', [])
    if not items:
        return jsonify({'error':'Cart is empty'}), 400
    conn = get_db()
    c = conn.cursor()

    # Check subscription
    cafe_id = d.get('cafe_id')
    c.execute("SELECT id FROM subscriptions WHERE student_id=? AND cafe_id=? AND status='active'", (uid, cafe_id))
    if not c.fetchone():
        conn.close()
        return jsonify({'error':'Active subscription required. Please subscribe first.'}), 403

    total = sum(i['price'] * i['quantity'] for i in items)
    c.execute("INSERT INTO orders(student_id,cafe_id,total_amount,room_no,special_instructions) VALUES(?,?,?,?,?)",
              (uid, cafe_id, total, d.get('room_no',''), d.get('special_instructions','')))
    order_id = c.lastrowid
    for i in items:
        c.execute("INSERT INTO order_items(order_id,item_id,quantity,price_at_time) VALUES(?,?,?,?)",
                  (order_id, i['item_id'], i['quantity'], i['price']))
    conn.commit()
    conn.close()
    return jsonify({'message':'Order placed', 'order_id': order_id}), 201

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    uid = session.get('user_id')
    role = session.get('role')
    if not uid:
        return jsonify({'error':'Not logged in'}), 401
    d = request.json
    new_status = d.get('status')
    conn = get_db()
    c = conn.cursor()
    if role == 'owner':
        c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
        cafe_id = c.fetchone()['cafe_id']
        c.execute("UPDATE orders SET status=? WHERE id=? AND cafe_id=?", (new_status, order_id, cafe_id))
    elif role == 'delivery':
        if new_status == 'delivered':
            c.execute("UPDATE orders SET status='delivered', delivered_at=datetime('now') WHERE id=? AND delivery_boy_id=?", (order_id, uid))
        else:
            conn.close()
            return jsonify({'error':'Delivery boys can only mark as delivered'}), 403
    conn.commit()
    conn.close()
    return jsonify({'message':'Status updated'})

@app.route('/api/orders/<int:order_id>/assign-delivery', methods=['POST'])
def assign_delivery(order_id):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    d = request.json
    delivery_boy_id = d.get('delivery_boy_id')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("UPDATE orders SET delivery_boy_id=?, status='out_for_delivery' WHERE id=? AND cafe_id=?",
              (delivery_boy_id, order_id, cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Delivery assigned'})

# ─── DELIVERY BOYS ───────────────────────────────────────────────────────────

@app.route('/api/delivery-boys', methods=['GET'])
def get_delivery_boys():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("SELECT id,name,email FROM users WHERE role='delivery' AND cafe_id=?", (cafe_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# ─── SUBSCRIPTIONS ────────────────────────────────────────────────────────────

@app.route('/api/subscriptions', methods=['POST'])
def request_subscription():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'student':
        return jsonify({'error':'Students only'}), 403
    d = request.json
    cafe_id = d.get('cafe_id')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM subscriptions WHERE student_id=? AND cafe_id=? AND status IN ('pending','active')", (uid, cafe_id))
    if c.fetchone():
        conn.close()
        return jsonify({'error':'Already have active/pending subscription'}), 400
    c.execute("INSERT INTO subscriptions(student_id,cafe_id) VALUES(?,?)", (uid, cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Subscription requested. Awaiting owner verification.'}), 201

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    uid = session.get('user_id')
    role = session.get('role')
    if not uid:
        return jsonify({'error':'Not logged in'}), 401
    conn = get_db()
    c = conn.cursor()
    if role == 'owner':
        c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
        cafe_id = c.fetchone()['cafe_id']
        c.execute("""SELECT s.*, u.name as student_name, u.email as student_email, u.roll_no
                     FROM subscriptions s JOIN users u ON s.student_id=u.id
                     WHERE s.cafe_id=? ORDER BY s.created_at DESC""", (cafe_id,))
    else:
        c.execute("""SELECT s.*, ca.name as cafe_name FROM subscriptions s 
                     JOIN cafes ca ON s.cafe_id=ca.id WHERE s.student_id=?""", (uid,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/subscriptions/<int:sub_id>/verify', methods=['PUT'])
def verify_subscription(sub_id):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    start = datetime.now().strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    c.execute("UPDATE subscriptions SET status='active', verified_by_owner=1, start_date=?, end_date=? WHERE id=? AND cafe_id=?",
              (start, end, sub_id, cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Subscription verified'})

@app.route('/api/subscriptions/<int:sub_id>/reject', methods=['PUT'])
def reject_subscription(sub_id):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("UPDATE subscriptions SET status='inactive' WHERE id=? AND cafe_id=?", (sub_id, cafe_id))
    conn.commit()
    conn.close()
    return jsonify({'message':'Subscription rejected'})

# ─── COMPLAINTS ──────────────────────────────────────────────────────────────

@app.route('/api/complaints', methods=['POST'])
def file_complaint():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'student':
        return jsonify({'error':'Students only'}), 403
    d = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO complaints(order_id,student_id,complaint_text) VALUES(?,?,?)",
              (d['order_id'], uid, d['complaint_text']))
    conn.commit()
    conn.close()
    return jsonify({'message':'Complaint filed'}), 201

@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    uid = session.get('user_id')
    role = session.get('role')
    if not uid:
        return jsonify({'error':'Not logged in'}), 401
    conn = get_db()
    c = conn.cursor()
    if role == 'owner':
        c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
        cafe_id = c.fetchone()['cafe_id']
        c.execute("""SELECT cp.*, u.name as student_name, o.room_no
                     FROM complaints cp JOIN users u ON cp.student_id=u.id
                     JOIN orders o ON cp.order_id=o.id
                     WHERE o.cafe_id=? ORDER BY cp.created_at DESC""", (cafe_id,))
    else:
        c.execute("SELECT * FROM complaints WHERE student_id=?", (uid,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/complaints/<int:cid>/resolve', methods=['PUT'])
def resolve_complaint(cid):
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE complaints SET status='resolved' WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return jsonify({'message':'Complaint resolved'})

# ─── FEEDBACK ────────────────────────────────────────────────────────────────

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'student':
        return jsonify({'error':'Students only'}), 403
    d = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO feedback(order_id,student_id,rating,comment) VALUES(?,?,?,?)",
                  (d['order_id'], uid, d['rating'], d.get('comment','')))
        conn.commit()
    except:
        conn.close()
        return jsonify({'error':'Feedback already submitted for this order'}), 400
    conn.close()
    return jsonify({'message':'Feedback submitted'}), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    c.execute("""SELECT f.*, u.name as student_name, o.room_no
                 FROM feedback f JOIN users u ON f.student_id=u.id
                 JOIN orders o ON f.order_id=o.id
                 WHERE o.cafe_id=? ORDER BY f.created_at DESC""", (cafe_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# ─── OWNER STATS ─────────────────────────────────────────────────────────────

@app.route('/api/owner/stats', methods=['GET'])
def owner_stats():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'owner':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT cafe_id FROM users WHERE id=?", (uid,))
    cafe_id = c.fetchone()['cafe_id']
    today = datetime.now().strftime('%Y-%m-%d')
    month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT COUNT(*) as cnt FROM orders WHERE cafe_id=? AND date(created_at)=?", (cafe_id, today))
    orders_today = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM orders WHERE cafe_id=? AND status='pending'", (cafe_id,))
    pending = c.fetchone()['cnt']
    c.execute("SELECT COALESCE(SUM(total_amount),0) as rev FROM orders WHERE cafe_id=? AND strftime('%Y-%m',created_at)=?", (cafe_id, month))
    revenue = c.fetchone()['rev']
    c.execute("SELECT COUNT(*) as cnt FROM subscriptions WHERE cafe_id=? AND status='active'", (cafe_id,))
    active_subs = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM complaints WHERE status='open' AND order_id IN (SELECT id FROM orders WHERE cafe_id=?)", (cafe_id,))
    open_complaints = c.fetchone()['cnt']
    conn.close()
    return jsonify({
        'orders_today': orders_today,
        'pending_orders': pending,
        'monthly_revenue': revenue,
        'active_subscribers': active_subs,
        'open_complaints': open_complaints
    })

# ─── DELIVERY HISTORY ────────────────────────────────────────────────────────

@app.route('/api/delivery/history', methods=['GET'])
def delivery_history():
    uid = session.get('user_id')
    if not uid or session.get('role') != 'delivery':
        return jsonify({'error':'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT o.*, u.name as student_name, ca.name as cafe_name 
                 FROM orders o JOIN users u ON o.student_id=u.id
                 JOIN cafes ca ON o.cafe_id=ca.id
                 WHERE o.delivery_boy_id=? AND o.status='delivered' 
                 ORDER BY o.delivered_at DESC""", (uid,))
    rows = []
    for r in c.fetchall():
        order = dict(r)
        c.execute("SELECT oi.*, i.name as item_name FROM order_items oi JOIN items i ON oi.item_id=i.id WHERE oi.order_id=?", (order['id'],))
        order['items'] = [dict(x) for x in c.fetchall()]
        rows.append(order)
    conn.close()
    return jsonify(rows)

# ─── SERVE FRONTEND ──────────────────────────────────────────────────────────

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

if __name__ == '__main__':
    os.makedirs('public', exist_ok=True)
    init_db()
    print("UNICAFE server running on http://localhost:5000")
    app.run(debug=False, port=5000)
