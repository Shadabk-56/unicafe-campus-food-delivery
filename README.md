# UNICAFE – Campus Food Delivery Portal
**FAST-NUCES Islamabad** | Team: Maryam Abid, Aftab Ahmed, Shadab Ahad

---

## Quick Start

### Windows
```
Double-click run.bat
```

### Linux / Mac
```bash
chmod +x run.sh
./run.sh
```

### Manual
```bash
pip install flask flask-cors bcrypt
python3 app.py
```

Then open: **http://localhost:5000**

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Red Cafe Owner | redcafe@unicafe.com | redcafe123 |
| Blue Cafe Owner | bluecafe@unicafe.com | bluecafe123 |

Sign up as **Student** or **Delivery Boy** from the signup page.

---

## Workflow

### Student
1. Sign up → Login → You land on **menu.html**
2. Go to **Subscription** tab → Request subscription for a cafe
3. Owner verifies subscription → You can now place orders
4. Browse menu → Add to cart → Enter room number → Place Order
5. Track order status in **My Orders** tab
6. After delivery: Rate order or file complaint

### Cafe Owner
1. Login → You land on **owner.html**
2. **Menu Items** tab → Add/edit/delete food items
3. **Orders** tab → See incoming orders → Mark Preparing → Mark Ready → Assign Delivery Boy
4. **Subscriptions** tab → Verify student subscription requests
5. **Complaints** tab → Resolve student complaints
6. **Feedback** tab → View ratings

### Delivery Boy
1. Sign up (select your cafe) → Login → **delivery.html**
2. **Active Orders** tab → See assigned orders → Mark as Delivered
3. **Delivery History** tab → View past deliveries and earnings (Rs. 10/delivery)

---

## Tech Stack
- **Backend**: Python Flask + SQLite3
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Auth**: Server-side sessions
- **DB**: unicafe.db (auto-created on first run)

## File Structure
```
unicafe/
├── app.py              ← Flask backend (all API routes)
├── unicafe.db          ← SQLite database (auto-created)
├── run.bat             ← Windows launcher
├── run.sh              ← Linux/Mac launcher
└── public/
    ├── index.html      ← Login / Signup page
    ├── menu.html       ← Student dashboard
    ├── owner.html      ← Cafe owner dashboard
    ├── delivery.html   ← Delivery boy dashboard
    ├── style.css       ← All styles
    └── utils.js        ← Shared JS utilities
```
