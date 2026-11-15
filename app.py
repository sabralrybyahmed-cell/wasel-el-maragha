from flask import Flask, request, redirect, session
from markupsafe import escape
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
app.secret_key = os.getenv("SECRET_KEY")

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

def db():
    con = sqlite3.connect("wasel.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        address TEXT NOT NULL,
        details TEXT NOT NULL,
        status TEXT DEFAULT 'new',
        driver_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    con.commit()
    con.close()

def page(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(title)}</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: Arial, sans-serif;
                background: #24140F;
                color: #fff;
                padding: 12px;
                margin: 0;
            }}

            .box {{
                background: #2D1A13;
                padding: 22px;
                border-radius: 20px;
                max-width: 600px;
                margin: 18px auto;
                box-shadow: 0 5px 20px #120905;
                border: 1px solid #58301E;
            }}

            h2, h3 {{
                color: #FF9F1C;
            }}

            input, textarea, select {{
                width: 100%;
                padding: 14px;
                margin: 9px 0;
                border-radius: 11px;
                border: 1px solid #70412A;
                background: #382017;
                color: white;
                font-size: 16px;
            }}

            input::placeholder, textarea::placeholder {{
                color: #C7AA99;
            }}

            button {{
                width: 100%;
                padding: 15px;
                margin: 9px 0;
                border: none;
                border-radius: 12px;
                background: #E85D04;
                color: white;
                font-size: 17px;
                font-weight: bold;
                cursor: pointer;
            }}

            button:active {{
                transform: scale(.97);
                background: #FF9F1C;
            }}

            a {{
                color: #FF9F1C;
                text-decoration: none;
            }}

            .item {{
                background: #382017;
                padding: 14px;
                margin: 10px 0;
                border-radius: 12px;
            }}

            .danger {{
                background: #B52B2B;
            }}

            .success {{
                background: #16834A;
            }}

            .sound-control {{
                display: block;
                text-align: left;
                color: #FF9F1C;
                font-size: 13px;
                margin-bottom: 12px;
            }}
        </style>
    </head>

    <body>
        <div class="box">
            <div class="sound-control">
                <button type="button" id="soundToggle"
                    style="width:auto;padding:7px 12px;font-size:13px">
                    🔊 الصوت يعمل
                </button>
            </div>

            <h2 style="text-align:center">🛵 وصل المراغة</h2>

            {content}
        </div>

        <script>
            let soundEnabled = true;
            let audioContext;

            const soundButton = document.getElementById("soundToggle");

            soundButton.addEventListener("click", function() {{
                soundEnabled = !soundEnabled;
                soundButton.textContent =
                    soundEnabled ? "🔊 الصوت يعمل" : "🔇 الصوت مكتوم";
            }});

            function playTouchSound() {{
                if (!soundEnabled) return;

                try {{
                    audioContext = audioContext ||
                        new (window.AudioContext || window.webkitAudioContext)();

                    if (audioContext.state === "suspended") {{
                        audioContext.resume();
                    }}

                    const oscillator = audioContext.createOscillator();
                    const gain = audioContext.createGain();

                    oscillator.connect(gain);
                    gain.connect(audioContext.destination);

                    oscillator.frequency.value = 650;
                    gain.gain.setValueAtTime(0.06, audioContext.currentTime);
                    gain.gain.exponentialRampToValueAtTime(
                        0.001, audioContext.currentTime + 0.08
                    );

                    oscillator.start();
                    oscillator.stop(audioContext.currentTime + 0.08);
                }} catch (e) {{}}
            }}

            document.addEventListener("click", function(event) {{
                if (event.target.closest("button, a")) {{
                    playTouchSound();
                }}
            }});
        </script>
    </body>
    </html>
    """

def login_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                return redirect("/admin-login" if role == "admin" else "/login")
            return func(*args, **kwargs)
        return wrapper
    return decorator
@app.route("/")
def landing():
    content = """
    <style>
        body {
            background:#101827 !important;
            padding:10px !important;
        }
        .box {
            max-width:700px !important;
            padding:10px !important;
            margin:10px auto !important;
            background:#101827 !important;
            border:0 !important;
            box-shadow:none !important;
        }
        h2, .sound-control { display:none !important; }
        .poster {
            display:block;
            width:100%;
            height:auto;
            border-radius:16px;
        }
        .open-app {
            display:block;
            background:linear-gradient(135deg,#ffb000,#f05a18);
            color:white;
            text-align:center;
            padding:19px;
            margin:18px 0;
            border-radius:15px;
            font-size:22px;
            font-weight:bold;
        }
    </style>
    <img class="poster" src="/static/poster.png" alt="وصل المراغة">
    <a class="open-app" href="/app">افتح التطبيق الآن ←</a>
    """
    return page("وصل المراغة", content)


@app.route("/app")
def home():
    con = db()

    drivers = con.execute("""
        SELECT name
        FROM drivers
        WHERE approved=1 AND available=1
        ORDER BY name
    """).fetchall()

    con.close()

    drivers_html = ""

    for driver in drivers:
        drivers_html += f"""
        <div class="driver-card">
            <div class="driver-icon">🛵</div>
            <div class="driver-info">
                <strong>{escape(driver['name'])}</strong>
                <span>متاح لاستقبال الطلبات</span>
            </div>
            <div class="online-dot"></div>
        </div>
        """

    if not drivers:
        drivers_html = """
        <div class="empty">
            <div style="font-size:35px">🛵</div>
            <strong>لا يوجد سائقون متاحون حاليًا</strong>
            <p>حاول مرة أخرى بعد قليل.</p>
        </div>
        """

    content = f"""
    <style>
        body {{
            background:#24140F !important;
            color:#fff;
            margin:0;
            padding:12px !important;
        }}

        .box {{
            background:#24140F !important;
            color:white;
            max-width:650px !important;
            padding:12px !important;
            box-shadow:none !important;
        }}

        h2 {{ display:none; }}

        .hero {{
            background:linear-gradient(135deg,#E85D04,#9E3500);
            padding:28px 20px;
            border-radius:22px;
            margin-bottom:22px;
        }}

        .logo {{
            font-size:30px;
            font-weight:bold;
            margin-bottom:18px;
        }}

        .hero h1 {{
            font-size:27px;
            margin:8px 0;
        }}

        .hero p {{
            color:#ffe0c5;
            line-height:1.8;
        }}

        .main-btn {{
            display:block;
            background:#fff;
            color:#B84400;
            text-align:center;
            padding:16px;
            border-radius:13px;
            font-weight:bold;
            margin-top:20px;
            font-size:17px;
        }}

        .section-title {{
            font-size:20px;
            margin:25px 4px 14px;
        }}

        .driver-card {{
            display:flex;
            align-items:center;
            background:#382017;
            padding:15px;
            border-radius:15px;
            margin-bottom:10px;
            gap:12px;
            border:1px solid #58301e;
        }}

        .driver-icon {{
            background:#542b19;
            padding:12px;
            border-radius:12px;
            font-size:25px;
        }}

        .driver-info {{
            flex:1;
        }}

        .driver-info strong {{
            display:block;
            font-size:16px;
        }}

        .driver-info span {{
            display:block;
            color:#FF9F1C;
            font-size:13px;
            margin-top:6px;
        }}

        .online-dot {{
            width:11px;
            height:11px;
            background:#35D07F;
            border-radius:50%;
        }}

        .empty {{
            background:#382017;
            padding:22px;
            text-align:center;
            border-radius:15px;
            line-height:1.8;
        }}

        .empty p {{
            color:#c9b5aa;
        }}

        .secondary {{
            display:block;
            color:#FF9F1C;
            text-align:center;
            padding:15px;
            border:1px solid #79401f;
            border-radius:12px;
            margin-top:12px;
        }}

        .footer {{
            text-align:center;
            color:#a98d7e;
            font-size:12px;
            margin-top:30px;
        }}
    </style>

    <div class="hero">
        <div class="logo">🛵 وصل</div>
        <h1>توصيلك بقى أسهل!</h1>
        <p>اطلب توصيل طلبك بسهولة، وشوف السائقين المتاحين في منطقتك.</p>
        <a class="main-btn" href="/order">اطلب توصيل الآن ←</a>
    </div>


    <h3 class="section-title">✨ خدماتنا</h3>

    <div class="driver-card">
        <div class="driver-icon">🛍️</div>
        <div class="driver-info">
            <strong>توصيل الطلبات</strong>
            <span>طلباتك لحد باب بيتك</span>
        </div>
    </div>

    <div class="driver-card">
        <div class="driver-icon">🏠</div>
        <div class="driver-info">
            <strong>توصيل للمنازل</strong>
            <span>خدمة سهلة وسريعة داخل المنطقة</span>
        </div>
    </div>

    <h3 class="section-title">📦 إزاي تطلب؟</h3>

    <div class="empty">
        1️⃣ افتح صفحة اطلب توصيل الآن<br>
        2️⃣ اكتب بيانات طلبك<br>
        3️⃣ انتظر السائق يستلم طلبك<br>
        4️⃣ استلم طلبك لحد باب البيت ❤️
    </div>

    <h3 class="section-title">🟢 السائقون المتاحون الآن</h3>

    {drivers_html}

    <h3 class="section-title">حساب السائق</h3>

    <a class="secondary" href="/login">دخول السائق</a>
    <a class="secondary" href="/register">تسجيل سائق جديد</a>

    <div class="footer">
        وصل المراغة - راحتك في توصيل طلبك ❤️
    </div>
    """

    return page("وصل المراغة", content)


@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        details = request.form.get("details", "").strip()

        try:
            lat = float(request.form.get("latitude", ""))
            lng = float(request.form.get("longitude", ""))
        except (ValueError, TypeError):
            return page("طلب توصيل", "<p>من فضلك حدد موقعك GPS أولاً.</p><a href='/order'>رجوع</a>")

        if not all([name, phone, address, details]):
            return page("طلب توصيل", "<p>من فضلك أكمل جميع البيانات.</p><a href='/order'>رجوع</a>")

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return page("طلب توصيل", "<p>الموقع غير صحيح.</p><a href='/order'>رجوع</a>")

        con = db()
        con.execute("""
        INSERT INTO orders
        (customer_name, customer_phone, address, details, customer_lat, customer_lng)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, address, details, lat, lng))
        con.commit()
        con.close()

        return page("تم الطلب", """
        <h3>✅ تم إرسال طلبك بنجاح</h3>
        <p>تم حفظ موقعك، وسيتم تحديد أقرب سائق متاح.</p>
        <a href="/">العودة للرئيسية</a>
        """)

    return page("طلب توصيل", """
    <h3>اطلب توصيل طلبك</h3>

    <form method="post">
    <input name="name" placeholder="اسمك" required>
    <input name="phone" placeholder="رقم هاتفك" required>
    <input name="address" placeholder="عنوان التوصيل بالتفصيل" required>
    <textarea name="details" placeholder="تفاصيل الطلب" required></textarea>

    <button type="button" onclick="getLocation()">📍 تحديد موقعي</button>
    <p id="gpsStatus">لم يتم تحديد موقعك بعد</p>

    <input type="hidden" name="latitude" id="latitude">
    <input type="hidden" name="longitude" id="longitude">

    <button type="submit" id="submitOrder" disabled>إرسال الطلب</button>
    </form>

    <a href="/">رجوع</a>

    <script>
    function getLocation() {
        const status = document.getElementById("gpsStatus");
        status.innerText = "جاري تحديد موقعك...";

        if (!navigator.geolocation) {
            status.innerText = "المتصفح لا يدعم تحديد الموقع";
            return;
        }

        navigator.geolocation.getCurrentPosition(
            function(position) {
                document.getElementById("latitude").value = position.coords.latitude;
                document.getElementById("longitude").value = position.coords.longitude;
                status.innerText = "✅ تم تحديد موقعك بنجاح";
                document.getElementById("submitOrder").disabled = false;
            },
            function(error) {
                status.innerText = "تعذر تحديد الموقع. فعّل GPS واسمح للموقع بالوصول إليه.";
            },
            {enableHighAccuracy: true, timeout: 15000, maximumAge: 30000}
        );
    }
    </script>
    """)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not name or not phone or len(password) < 6:
            return page("تسجيل السائق", "<p>أكمل البيانات، وكلمة المرور لا تقل عن 6 أحرف.</p><a href='/register'>رجوع</a>")

        con = db()
        try:
            con.execute("""
            INSERT INTO drivers (name, phone, password)
            VALUES (?, ?, ?)
            """, (name, phone, generate_password_hash(password)))
            con.commit()
        except sqlite3.IntegrityError:
            con.close()
            return page("تسجيل السائق", "<p>رقم الهاتف مسجل من قبل.</p><a href='/register'>رجوع</a>")

        con.close()
        return page("تم التسجيل", """
        <h3>تم إرسال طلب تسجيلك بنجاح.</h3>
        <p>انتظر موافقة المدير لتفعيل حسابك.</p>
        <a href="/">الرئيسية</a>
        """)

    return page("تسجيل السائق", """
    <h3>تسجيل سائق جديد</h3>
    <form method="post">
    <input name="name" placeholder="الاسم" required>
    <input name="phone" placeholder="رقم الهاتف" required>
    <input name="password" type="password" placeholder="كلمة المرور - 6 أحرف على الأقل" required>
    <button>تسجيل</button>
    </form>
    <a href="/">الرئيسية</a>
    """)

@app.route("/login", methods=["GET", "POST"])
def driver_login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        con = db()
        user = con.execute(
            "SELECT * FROM drivers WHERE phone=?", (phone,)
        ).fetchone()
        con.close()

        if user and check_password_hash(user["password"], password):
            if user["approved"] != 1:
                return page("الحساب", "<h3>حسابك لم تتم الموافقة عليه بعد.</h3>")

            session.clear()
            session["role"] = "driver"
            session["driver_id"] = user["id"]
            return redirect("/driver")

        return page("دخول", "<p>بيانات الدخول غير صحيحة.</p><a href='/login'>حاول مرة أخرى</a>")

    return page("دخول السائق", """
    <h3>دخول السائق</h3>
    <form method="post">
    <input name="phone" placeholder="رقم الهاتف" required>
    <input name="password" type="password" placeholder="كلمة المرور" required>
    <button>دخول</button>
    </form>
    <a href="/">الرئيسية</a>
    """)

@app.route("/driver")
@login_required("driver")
def driver():
    con = db()
    user = con.execute(
        "SELECT * FROM drivers WHERE id=?", (session["driver_id"],)
    ).fetchone()

    if not user or user["approved"] != 1:
        con.close()
        session.clear()
        return redirect("/login")

    orders = con.execute(
        "SELECT * FROM orders WHERE driver_id=? ORDER BY id DESC",
        (user["id"],)
    ).fetchall()
    con.close()

    content = f"<h3>أهلاً يا {escape(user['name'])} 🛵</h3>"

    content += """
    <div class="item">
        <h3>📍 موقعك الحالي</h3>
        <p id="driverGpsStatus">اضغط لتحديث موقعك</p>

        <form id="driverGpsForm" method="post" action="/driver-location">
            <input type="hidden" name="latitude" id="driverLatitude">
            <input type="hidden" name="longitude" id="driverLongitude">

            <button type="button" onclick="updateDriverLocation()">
                📍 تحديث موقعي GPS
            </button>
        </form>
    </div>

    <script>
    function updateDriverLocation() {
        const status = document.getElementById("driverGpsStatus");
        status.innerText = "جاري تحديد موقعك...";

        if (!navigator.geolocation) {
            status.innerText = "المتصفح لا يدعم GPS";
            return;
        }

        navigator.geolocation.getCurrentPosition(
            function(position) {
                document.getElementById("driverLatitude").value =
                    position.coords.latitude;

                document.getElementById("driverLongitude").value =
                    position.coords.longitude;

                status.innerText = "تم تحديد الموقع، جاري الحفظ...";
                document.getElementById("driverGpsForm").submit();
            },
            function(error) {
                status.innerText =
                    "تعذر تحديد الموقع. فعّل GPS واسمح للمتصفح بالوصول إليه.";
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 30000
            }
        );
    }
    </script>
    """


    current_available = int(user["available"] or 0)
    next_available = 0 if current_available else 1
    availability_text = "🟢 متاح لاستقبال الطلبات" if current_available else "🔴 غير متاح لاستقبال الطلبات"
    button_text = "إيقاف استقبال الطلبات" if current_available else "تشغيل استقبال الطلبات"

    content += f"""
    <div class="item">
        <h3>حالة استقبال الطلبات</h3>
        <p>{availability_text}</p>
        <form method="post" action="/driver-availability">
            <input type="hidden" name="available" value="{next_available}">
            <button type="submit">{button_text}</button>
        </form>
    </div>
    """

    content += "<h3>طلباتك</h3>"

    if not orders:
        content += "<p>لا توجد طلبات مسندة إليك حاليًا.</p>"

    for o in orders:
        content += f"""
        <div class="item">
        <b>طلب رقم:</b> {o['id']}<br>
        <b>العميل:</b> {escape(o['customer_name'])}<br>
        <b>الهاتف:</b> {escape(o['customer_phone'])}<br>
        <b>العنوان:</b> {escape(o['address'])}<br>
        <b>التفاصيل:</b> {escape(o['details'])}<br>
        <b>الحالة:</b> {escape(o['status'])}
        """
        if o["status"] != "delivered":
            content += f"""
            <form method="post" action="/delivered/{o['id']}">
            <button class="success">تم التوصيل</button>
            </form>
            """
        content += "</div>"

    content += "<a href='/logout'>تسجيل الخروج</a>"
    return page("لوحة السائق", content)



@app.route("/driver-availability", methods=["POST"])
@login_required("driver")
def driver_availability():
    try:
        available = int(request.form.get("available", "-1"))
    except ValueError:
        return redirect("/driver")

    if available not in (0, 1):
        return redirect("/driver")

    con = db()

    user = con.execute(
        "SELECT approved, latitude, longitude FROM drivers WHERE id=?",
        (session["driver_id"],)
    ).fetchone()

    if not user or user["approved"] != 1:
        con.close()
        session.clear()
        return redirect("/login")

    if available == 1 and (
        user["latitude"] is None or user["longitude"] is None
    ):
        con.close()
        return page(
            "تحديد الموقع",
            "<h3>📍 حدد موقعك GPS أولاً قبل استقبال الطلبات.</h3><a href='/driver'>رجوع</a>"
        )

    con.execute(
        "UPDATE drivers SET available=? WHERE id=?",
        (available, session["driver_id"])
    )

    con.commit()
    con.close()

    return redirect("/driver")


@app.route("/driver-location", methods=["POST"])
@login_required("driver")
def driver_location():
    try:
        lat = float(request.form.get("latitude", ""))
        lng = float(request.form.get("longitude", ""))
    except (ValueError, TypeError):
        return page("خطأ", "<p>إحداثيات الموقع غير صحيحة.</p><a href='/driver'>رجوع</a>")

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return page("خطأ", "<p>الموقع خارج النطاق الصحيح.</p><a href='/driver'>رجوع</a>")

    con = db()
    con.execute("""
        UPDATE drivers
        SET latitude=?, longitude=?, location_updated=CURRENT_TIMESTAMP
        WHERE id=?
    """, (lat, lng, session["driver_id"]))

    con.commit()
    con.close()

    return redirect("/driver")


@app.route("/delivered/<int:order_id>", methods=["POST"])
@login_required("driver")
def delivered(order_id):
    con = db()
    con.execute("""
    UPDATE orders SET status='delivered'
    WHERE id=? AND driver_id=?
    """, (order_id, session["driver_id"]))
    con.commit()
    con.close()
    return redirect("/driver")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session.clear()
            session["role"] = "admin"
            return redirect("/admin")

        return page("دخول المدير", "<p>بيانات الدخول غير صحيحة.</p>")

    return page("دخول المدير", """
    <h3>دخول المدير</h3>
    <form method="post">
    <input name="username" placeholder="اسم المستخدم" required>
    <input name="password" type="password" placeholder="كلمة المرور" required>
    <button>دخول</button>
    </form>
    <a href="/">الرئيسية</a>
    """)

@app.route("/admin")
@login_required("admin")
def admin():
    con = db()
    drivers = con.execute("SELECT * FROM drivers ORDER BY id DESC").fetchall()
    orders = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    approved = con.execute("SELECT * FROM drivers WHERE approved=1").fetchall()

    content = "<h3>لوحة المدير</h3>"
    content += f"<p>عدد السائقين: {len(drivers)}</p>"
    content += f"<p>عدد السائقين المقبولين: {len(approved)}</p>"
    content += f"<p>عدد الطلبات: {len(orders)}</p>"

    content += "<h3>طلبات تسجيل السائقين</h3>"
    for d in drivers:
        if d["approved"] == 0:
            content += f"""
            <div class="item">
            {escape(d['name'])} - {escape(d['phone'])}
            <form method="post" action="/approve/{d['id']}">
            <button class="success">قبول السائق</button>
            </form>
            <form method="post" action="/reject/{d['id']}">
            <button class="danger">رفض السائق</button>
            </form>
            </div>
            """

    content += "<h3>الطلبات</h3>"
    for o in orders:
        content += f"""
        <div class="item">
        <b>طلب رقم:</b> {o['id']}<br>
        <b>العميل:</b> {escape(o['customer_name'])}<br>
        <b>الهاتف:</b> {escape(o['customer_phone'])}<br>
        <b>العنوان:</b> {escape(o['address'])}<br>
        <b>التفاصيل:</b> {escape(o['details'])}<br>
        <b>الحالة:</b> {escape(o['status'])}<br>
        """

        if o["status"] != "delivered":
            content += f"""
            <form method="post" action="/assign/{o['id']}">
            <select name="driver_id" required>
            <option value="">اختار السائق</option>
            """
            for d in approved:
                content += f"<option value='{d['id']}'>{escape(d['name'])} - {escape(d['phone'])}</option>"
            content += """
            </select>
            <button>إسناد الطلب للسائق</button>
            </form>
            """
        content += "</div>"

    con.close()
    content += "<a href='/logout'>تسجيل الخروج</a>"
    return page("لوحة المدير", content)

@app.route("/approve/<int:driver_id>", methods=["POST"])
@login_required("admin")
def approve(driver_id):
    con = db()
    con.execute(
        "UPDATE drivers SET approved=1 WHERE id=? AND approved=0",
        (driver_id,)
    )
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/reject/<int:driver_id>", methods=["POST"])
@login_required("admin")
def reject(driver_id):
    con = db()
    con.execute(
        "DELETE FROM drivers WHERE id=? AND approved=0",
        (driver_id,)
    )
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/assign/<int:order_id>", methods=["POST"])
@login_required("admin")
def assign(order_id):
    driver_id = request.form.get("driver_id", type=int)
    con = db()

    driver = con.execute(
        "SELECT id FROM drivers WHERE id=? AND approved=1",
        (driver_id,)
    ).fetchone()

    if driver:
        con.execute("""
        UPDATE orders SET driver_id=?, status='assigned'
        WHERE id=?
        """, (driver_id, order_id))
        con.commit()

    con.close()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
