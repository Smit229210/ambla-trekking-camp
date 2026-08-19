```python
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    send_file,
    render_template_string
)

from werkzeug.utils import secure_filename

import sqlite3
import io
import os
import time
import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ambla-trekking-secret-2026"
)


# =========================================================
# ADMIN DETAILS
# =========================================================

ADMIN_EMAIL = "bhattsmit451@gmail.com"
ADMIN_PASSWORD = "sm229210"


# =========================================================
# DATABASE AND UPLOAD SETTINGS
# =========================================================

DB = "trekking.db"

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def db():

    con = sqlite3.connect(DB)

    con.row_factory = sqlite3.Row

    return con


def add_column_if_missing(
    con,
    table,
    column,
    definition
):

    columns = con.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    column_names = [
        row["name"]
        for row in columns
    ]

    if column not in column_names:

        con.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition}
            """
        )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    con = db()


    # -----------------------------------------------------
    # REGISTRATIONS TABLE
    # -----------------------------------------------------

    con.execute("""
    CREATE TABLE IF NOT EXISTS registrations (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT NOT NULL,

        enrollment TEXT NOT NULL,

        mobile TEXT NOT NULL,

        email TEXT NOT NULL,

        college_class TEXT NOT NULL,

        emergency_name TEXT NOT NULL,

        emergency_mobile TEXT NOT NULL,

        payment_method TEXT NOT NULL,

        payment_status TEXT DEFAULT 'Pending',

        attendance TEXT DEFAULT 'Pending',

        payment_screenshot TEXT DEFAULT ''

    )
    """)


    # Add screenshot column automatically if database
    # already existed before this update

    add_column_if_missing(
        con,
        "registrations",
        "payment_screenshot",
        "TEXT DEFAULT ''"
    )


    # -----------------------------------------------------
    # ADMINS TABLE
    # -----------------------------------------------------

    con.execute("""
    CREATE TABLE IF NOT EXISTS admins (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT DEFAULT 'admin'

    )
    """)


    # -----------------------------------------------------
    # CREATE SUPERIOR ADMIN
    # -----------------------------------------------------

    existing = con.execute(
        """
        SELECT * FROM admins
        WHERE email=?
        """,
        (ADMIN_EMAIL,)
    ).fetchone()


    if not existing:

        con.execute(
            """
            INSERT INTO admins
            (
                name,
                email,
                password,
                role
            )

            VALUES (?,?,?,?)
            """,

            (
                "Superior Admin",
                ADMIN_EMAIL,
                ADMIN_PASSWORD,
                "superior"
            )
        )


    con.commit()

    con.close()


init_db()


# =========================================================
# CSS
# =========================================================

CSS = """

<style>

*{
    box-sizing:border-box;
}


body{
    margin:0;
    font-family:Arial,sans-serif;
    background:#eef3ee;
    color:#20352b;
}


nav{
    background:#193d2c;
    color:white;
    padding:16px 7%;
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-wrap:wrap;
}


nav a{
    color:white;
    text-decoration:none;
    margin-left:16px;
}


.hero{
    background:
    linear-gradient(
        135deg,
        #214d35,
        #557b45
    );

    color:white;
    text-align:center;
    padding:70px 20px;
}


.hero h1{
    font-size:42px;
    margin:0 0 15px;
}


.container{
    max-width:1100px;
    margin:auto;
    padding:30px 20px;
}


.card{
    background:white;
    padding:25px;
    border-radius:14px;
    margin-bottom:25px;
    box-shadow:
    0 5px 18px
    rgba(0,0,0,.08);
}


h1,
h2,
h3{
    color:#234d36;
}


input,
select{
    width:100%;
    padding:13px;
    margin:7px 0 16px;
    border:
    1px solid
    #b7c5b9;
    border-radius:8px;
    font-size:16px;
}


button,
.btn{
    display:inline-block;
    background:#245a3d;
    color:white;
    padding:13px 22px;
    border:none;
    border-radius:8px;
    cursor:pointer;
    text-decoration:none;
    font-size:16px;
    margin:3px;
}


.btn:hover,
button:hover{
    background:#173e2a;
}


.warning{
    background:#fff3cd;
    padding:15px;
    border-radius:8px;
    border-left:
    5px solid
    #e3a600;
}


.success{
    background:#d8f3dc;
    padding:15px;
    border-radius:8px;
    border-left:
    5px solid
    #3c9b58;
}


.danger{
    background:#f8d7da;
    padding:15px;
    border-radius:8px;
    border-left:
    5px solid
    #c0392b;
}


.info{
    background:#dbeafe;
    padding:15px;
    border-radius:8px;
    border-left:
    5px solid
    #2563eb;
}


table{
    width:100%;
    border-collapse:collapse;
}


th,
td{
    padding:10px;
    border-bottom:
    1px solid #ddd;
    text-align:left;
    vertical-align:top;
}


th{
    background:#214d35;
    color:white;
}


.footer{
    background:#193d2c;
    color:white;
    text-align:center;
    padding:20px;
    margin-top:30px;
}


.small{
    color:#666;
    font-size:14px;
}


.fee{
    font-size:26px;
    font-weight:bold;
    color:#b03a2e;
}


.qr-payment{
    display:block;
    max-width:320px;
    width:100%;
    margin:15px auto;
    border-radius:10px;
    border:
    2px solid #ddd;
}


.status-success{
    color:#16803a;
}


.status-pending{
    color:#b77900;
}


.status-failed{
    color:#c62828;
}


@media(max-width:700px){

    nav{
        gap:10px;
    }

    nav a{
        margin-left:8px;
    }

    .hero h1{
        font-size:30px;
    }

}

</style>

"""


# =========================================================
# HOME PAGE
# =========================================================

HOME = """

<!DOCTYPE html>

<html>

<head>

<title>
Ambla One Day Trekking Camp
</title>

""" + CSS + """

</head>


<body>


<nav>

<div>

<b>
🌿 Ambla Trekking Camp
</b>

</div>


<div>

<a href="/">
Home
</a>

<a href="#register">
Registration
</a>

<a href="/login">
Admin
</a>

</div>

</nav>


<section class="hero">

<h1>
🌿 Ambla One Day Trekking Camp
</h1>

<h2 style="color:white;">
23/08/2026
</h2>

<p>
🕕 6:00 AM to 6:00 PM
</p>

<p>
Organized by Ignited Youth Form BVN
</p>

</section>


<div class="container">


{% if message %}

<div class="warning">

<b>
{{message}}
</b>

</div>

<br>

{% endif %}


<div class="card">

<h2>
💰 Trekking Camp Fee
</h2>

<p class="fee">
₹300 per student
</p>

<p>

Choose Online Payment or Cash Payment.

</p>

</div>


<div class="card">

<h2>
📋 મહત્વપૂર્ણ સૂચનાઓ
</h2>

<ul>

<li>
કૃપા કરીને તમામ વિગતો સાચી રીતે ભરો.
</li>

<li>
રજીસ્ટ્રેશન પૂર્ણ થયા પછી તમારું
Registration Details PDF ડાઉનલોડ કરો.
</li>

<li>
PDF માં તમારો વ્યક્તિગત QR Code આપવામાં આવશે.
</li>

<li>
ટ્રેકિંગ દરમિયાન QR Code attendance માટે ઉપયોગી રહેશે.
</li>

<li>
કોઈપણ સમસ્યા હોય તો આયોજકોનો સંપર્ક કરો.
</li>

</ul>

</div>


<div class="card">

<h2>
🎒 Packing List
</h2>

<ul>

<li>
પાણીની બોટલ
</li>

<li>
લંચબોક્સ
</li>

<li>
વ્યક્તિગત જરૂરી વસ્તુઓ
</li>

<li>
આરામદાયક ટ્રેકિંગ શૂઝ
</li>

</ul>

</div>


<div class="card">

<h2>
🌳 Trekking Rules
</h2>

<ul>

<li>
<b>
પ્રકૃતિને નુકસાન ન પહોંચાડવું.
</b>
</li>

<li>
<b>
હંમેશા ગ્રુપ સાથે રહેવું.
</b>
</li>

<li>
<b>
કોઈપણ પ્રકારની મસ્તી કે
mischief કડક રીતે પ્રતિબંધિત છે.
</b>
</li>

<li>
આયોજકોની સૂચનાઓનું પાલન કરવું.
</li>

<li>
સલામતીના નિયમોનું પાલન કરવું.
</li>

</ul>


<div class="warning">

<b>
⚠️ Important Note:
</b>

<br>

Wear green, brown and nature camouflage colors.

</div>

</div>


<!-- ================================================ -->
<!-- REGISTRATION -->
<!-- ================================================ -->

<div
class="card"
id="register"
>

<h2>
📝 વિદ્યાર્થી નોંધણી
</h2>

<p class="fee">
Fees: ₹300
</p>


<form
method="POST"
action="/register"
enctype="multipart/form-data"
>


<label>
વિદ્યાર્થીનું સંપૂર્ણ નામ / Full Name
</label>

<input
name="full_name"
required
>


<label>
Enrollment Number
</label>

<input
name="enrollment"
required
>


<label>
Mobile Number
</label>

<input
name="mobile"
required
>


<label>
Email Address
</label>

<input
type="email"
name="email"
required
>


<label>
College / Class
</label>

<input
name="college_class"
required
>


<label>
Emergency Contact Name
</label>

<input
name="emergency_name"
required
>


<label>
Emergency Mobile Number
</label>

<input
name="emergency_mobile"
required
>


<!-- ================================================ -->
<!-- PAYMENT METHOD -->
<!-- ================================================ -->

<label>
Payment Method
</label>


<select
name="payment_method"
id="payment_method"
required
onchange="togglePayment()"
>

<option value="">
Select Payment Method
</option>

<option value="Online">
Online Payment
</option>

<option value="Cash">
Cash Payment
</option>

</select>


<!-- ================================================ -->
<!-- ONLINE PAYMENT -->
<!-- ================================================ -->

<div
id="online_payment"
style="display:none;"
>

<h3>
📱 Online Payment
</h3>

<p>

Scan the QR code and pay
₹300.

</p>


<img
class="qr-payment"
src="/payment-qr"
alt="Payment QR Code"
>


<label>
Upload Payment Screenshot
</label>


<input
type="file"
name="payment_screenshot"
id="payment_screenshot"
accept=".png,.jpg,.jpeg,.webp"
>


<div class="warning">

<b>
⚠️ Important:
</b>

Payment screenshot is compulsory
for Online Payment.

</div>

<br>

</div>


<!-- ================================================ -->
<!-- CASH PAYMENT -->
<!-- ================================================ -->

<div
id="cash_payment"
style="display:none;"
>

<div class="info">

<h3>
💵 Cash Payment
</h3>

Give the ₹300 fee to the authorized organizer.

<br><br>

<b>
No payment screenshot is required.
</b>

<br><br>

Your payment status will remain
<b>Pending</b>
until the admin confirms that the cash
has been received.

</div>

<br>

</div>


<button type="submit">

Register & Generate PDF

</button>


</form>


<script>

function togglePayment(){

    const method =
        document.getElementById(
            "payment_method"
        ).value;


    const online =
        document.getElementById(
            "online_payment"
        );


    const cash =
        document.getElementById(
            "cash_payment"
        );


    const screenshot =
        document.getElementById(
            "payment_screenshot"
        );


    if(method === "Online"){

        online.style.display =
            "block";

        cash.style.display =
            "none";

        screenshot.required =
            true;

    }


    else if(method === "Cash"){

        online.style.display =
            "none";

        cash.style.display =
            "block";

        screenshot.required =
            false;

        screenshot.value =
            "";

    }


    else{

        online.style.display =
            "none";

        cash.style.display =
            "none";

        screenshot.required =
            false;

        screenshot.value =
            "";

    }

}

</script>


</div>


<div class="card">

<h2>
📞 મદદ અને સંપર્ક
</h2>

<p>

કોઈપણ સમસ્યા અથવા માહિતી માટે
Trekking Camp organizers નો સંપર્ક કરો.

</p>

</div>


</div>


<div class="footer">

<p>
Ambla One Day Trekking Camp
</p>

<p>
Credit: ChatGPT
</p>

</div>


</body>

</html>

"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template_string(

        HOME,

        message=request.args.get(
            "message",
            ""
        )

    )


# =========================================================
# PAYMENT QR IMAGE
# =========================================================

@app.route("/payment-qr")
def payment_qr():

    possible_files = [

        "unnamed.png",

        "unnemed.png",

        "payment_qr.png"

    ]


    for filename in possible_files:

        if os.path.exists(filename):

            return send_file(filename)


    return (
        "Payment QR image not found. "
        "Please upload unnamed.png to GitHub.",
        404
    )


# =========================================================
# REGISTRATION
# =========================================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():


    fields = [

        "full_name",

        "enrollment",

        "mobile",

        "email",

        "college_class",

        "emergency_name",

        "emergency_mobile",

        "payment_method"

    ]


    # -----------------------------------------------------
    # CHECK REQUIRED FIELDS
    # -----------------------------------------------------

    for field in fields:

        if not request.form.get(
            field,
            ""
        ).strip():

            return redirect(

                url_for(

                    "home",

                    message=
                    "Please fill all required details."

                )

            )


    payment_method = request.form.get(
        "payment_method",
        ""
    ).strip()


    screenshot_filename = ""


    # -----------------------------------------------------
    # ONLINE PAYMENT
    # -----------------------------------------------------

    if payment_method == "Online":

        screenshot = request.files.get(
            "payment_screenshot"
        )


        if (
            not screenshot
            or screenshot.filename == ""
        ):

            return redirect(

                url_for(

                    "home",

                    message=
                    "Please upload your payment screenshot for Online Payment."

                )

            )


        if not allowed_file(
            screenshot.filename
        ):

            return redirect(

                url_for(

                    "home",

                    message=
                    "Invalid screenshot format. Please upload PNG, JPG, JPEG or WEBP."

                )

            )


        original_filename = secure_filename(
            screenshot.filename
        )


        timestamp = str(
            int(
                time.time()
            )
        )


        enrollment = secure_filename(

            request.form[
                "enrollment"
            ].strip()

        )


        screenshot_filename = (

            enrollment

            + "_"

            + timestamp

            + "_"

            + original_filename

        )


        screenshot.save(

            os.path.join(

                app.config[
                    "UPLOAD_FOLDER"
                ],

                screenshot_filename

            )

        )


        payment_status = (
            "Pending Verification"
        )


    # -----------------------------------------------------
    # CASH PAYMENT
    # -----------------------------------------------------

    elif payment_method == "Cash":

        screenshot_filename = ""

        payment_status = "Pending"


    # -----------------------------------------------------
    # INVALID METHOD
    # -----------------------------------------------------

    else:

        return redirect(

            url_for(

                "home",

                message=
                "Please select a valid payment method."

            )

        )


    # -----------------------------------------------------
    # SAVE STUDENT
    # -----------------------------------------------------

    con = db()


    cur = con.execute(

        """

        INSERT INTO registrations
        (

            full_name,

            enrollment,

            mobile,

            email,

            college_class,

            emergency_name,

            emergency_mobile,

            payment_method,

            payment_status,

            attendance,

            payment_screenshot

        )

        VALUES (?,?,?,?,?,?,?,?,?,?,?)

        """,

        (

            request.form[
                "full_name"
            ].strip(),


            request.form[
                "enrollment"
            ].strip(),


            request.form[
                "mobile"
            ].strip(),


            request.form[
                "email"
            ].strip(),


            request.form[
                "college_class"
            ].strip(),


            request.form[
                "emergency_name"
            ].strip(),


            request.form[
                "emergency_mobile"
            ].strip(),


            payment_method,


            payment_status,


            "Pending",


            screenshot_filename

        )

    )


    student_id = cur.lastrowid


    con.commit()

    con.close()


    return redirect(

        url_for(

            "registration_success",

            student_id=student_id

        )

    )


# =========================================================
# REGISTRATION SUCCESS
# =========================================================

@app.route(
    "/success/<int:student_id>"
)
def registration_success(student_id):


    con = db()


    student = con.execute(

        """
        SELECT *
        FROM registrations
        WHERE id=?
        """,

        (student_id,)

    ).fetchone()


    con.close()


    if not student:

        return (
            "Student not found",
            404
        )


    page = """

    <!DOCTYPE html>

    <html>

    <head>

    <title>
    Registration Successful
    </title>

    """ + CSS + """

    </head>


    <body>


    <div class="container">


    <div
    class="card"
    style="text-align:center;"
    >


    <h1>
    🎉 Registration Submitted!
    </h1>


    <p>

    Your registration has been successfully submitted.

    </p>


    <p>

    <b>
    Student:
    </b>

    {{student["full_name"]}}

    </p>


    <p>

    <b>
    Enrollment:
    </b>

    {{student["enrollment"]}}

    </p>


    <p>

    <b>
    Payment Method:
    </b>

    {{student["payment_method"]}}

    </p>


    <p>

    <b>
    Payment Status:
    </b>

    {{student["payment_status"]}}

    </p>


    {% if student["payment_method"] == "Online" %}

    <div class="info">

    Your payment screenshot has been submitted.

    The admin will verify the payment.

    </div>

    {% else %}

    <div class="info">

    Please give the cash fee to the authorized organizer.

    The admin will update your payment status
    after receiving the cash.

    </div>

    {% endif %}


    <br>


    <p>

    Download your registration details PDF
    and keep it safely.

    </p>


    <a
    class="btn"
    href="/registration-pdf/{{student["id"]}}"
    >

    📄 Download Registration PDF

    </a>


    <br><br>


    <a href="/">

    ← Back to Home

    </a>


    </div>


    </div>


    </body>

    </html>

    """


    return render_template_string(

        page,

        student=student

    )


# =========================================================
# PDF GENERATION
# =========================================================

@app.route(
    "/registration-pdf/<int:student_id>"
)
def registration_pdf(student_id):


    con = db()


    student = con.execute(

        """
        SELECT *
        FROM registrations
        WHERE id=?
        """,

        (student_id,)

    ).fetchone()


    con.close()


    if not student:

        return (
            "Student not found",
            404
        )


    buffer = io.BytesIO()


    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=40

    )


    styles = getSampleStyleSheet()


    story = []


    story.append(

        Paragraph(

            "<b>AMBLA ONE DAY TREKKING CAMP</b>",

            styles["Title"]

        )

    )


    story.append(

        Paragraph(

            "Date: 23/08/2026 | Time: 6:00 AM to 6:00 PM",

            styles["Normal"]

        )

    )


    story.append(

        Paragraph(

            "Organized by Ignited Youth Form BVN",

            styles["Normal"]

        )

    )


    story.append(
        Spacer(1, 20)
    )


    data = [

        [
            "Student ID",
            str(student["id"])
        ],

        [
            "Full Name",
            student["full_name"]
        ],

        [
            "Enrollment Number",
            student["enrollment"]
        ],

        [
            "Mobile",
            student["mobile"]
        ],

        [
            "Email",
            student["email"]
        ],

        [
            "College / Class",
            student["college_class"]
        ],

        [
            "Emergency Contact",
            student["emergency_name"]
        ],

        [
            "Emergency Mobile",
            student["emergency_mobile"]
        ],

        [
            "Fee",
            "₹300"
        ],

        [
            "Payment Method",
            student["payment_method"]
        ],

        [
            "Payment Status",
            student["payment_status"]
        ],

        [
            "Attendance",
            student["attendance"]
        ]

    ]


    table = Table(

        data,

        colWidths=[
            170,
            330
        ]

    )


    table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0, 0),

                (0, -1),

                colors.HexColor(
                    "#214d35"
                )

            ),

            (

                "TEXTCOLOR",

                (0, 0),

                (0, -1),

                colors.white

            ),

            (

                "GRID",

                (0, 0),

                (-1, -1),

                1,

                colors.grey

            ),

            (

                "VALIGN",

                (0, 0),

                (-1, -1),

                "MIDDLE"

            ),

            (

                "PADDING",

                (0, 0),

                (-1, -1),

                8

            )

        ])

    )


    story.append(table)


    story.append(
        Spacer(1, 25)
    )


    # -----------------------------------------------------
    # INDIVIDUAL QR CODE
    # -----------------------------------------------------

    qr_data = (

        "AMBLA-TREK-2026-STUDENT-"

        + str(
            student["id"]
        )

    )


    qr = qrcode.make(
        qr_data
    )


    qr_buffer = io.BytesIO()


    qr.save(

        qr_buffer,

        format="PNG"

    )


    qr_buffer.seek(0)


    qr_image = Image(

        qr_buffer,

        width=140,

        height=140

    )


    story.append(

        Paragraph(

            "<b>Individual Attendance QR Code</b>",

            styles["Heading2"]

        )

    )


    story.append(
        qr_image
    )


    story.append(
        Spacer(1, 15)
    )


    story.append(

        Paragraph(

            "Important: Keep this PDF safely. "
            "The QR code may be used for attendance verification.",

            styles["Normal"]

        )

    )


    story.append(
        Spacer(1, 25)
    )


    story.append(

        Paragraph(

            "Rules: Do not harm nature. "
            "Stay together. "
            "Do not do any mischief. "
            "Follow organizer instructions.",

            styles["Normal"]

        )

    )


    story.append(

        Paragraph(

            "Important Note: "
            "Wear green, brown and nature camouflage colors.",

            styles["Normal"]

        )

    )


    story.append(
        Spacer(1, 25)
    )


    story.append(

        Paragraph(

            "Credit: ChatGPT",

            styles["Normal"]

        )

    )


    doc.build(
        story
    )


    buffer.seek(0)


    filename = (

        "Ambla_Trekking_Registration_"

        + str(
            student["id"]
        )

        + ".pdf"

    )


    return send_file(

        buffer,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"

    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = ""


    if request.method == "POST":

        email = request.form.get(

            "email",

            ""

        ).lower().strip()


        password = request.form.get(

            "password",

            ""

        )


        con = db()


        admin = con.execute(

            """
            SELECT *
            FROM admins
            WHERE email=?
            AND password=?
            """,

            (
                email,
                password
            )

        ).fetchone()


        con.close()


        if admin:

            session["admin"] = True

            session["admin_email"] = (
                admin["email"]
            )

            session["admin_role"] = (
                admin["role"]
            )


            return redirect(
                "/admin"
            )


        error = (
            "Invalid email or password."
        )


    page = """

    <!DOCTYPE html>

    <html>

    <head>

    <title>
    Admin Login
    </title>

    """ + CSS + """

    </head>


    <body>


    <div class="container">


    <div class="card">


    <h1>
    🔐 Admin Login
    </h1>


    {% if error %}

    <p style="color:red;">

    <b>
    {{error}}
    </b>

    </p>

    {% endif %}


    <form method="POST">


    <label>
    Email
    </label>


    <input

        type="email"

        name="email"

        required

    >


    <label>
    Password
    </label>


    <input

        type="password"

        name="password"

        required

    >


    <button type="submit">

    Login

    </button>


    </form>


    <br>


    <a href="/">

    ← Back

    </a>


    </div>


    </div>


    </body>

    </html>

    """


    return render_template_string(

        page,

        error=error

    )


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required():

    if not session.get(
        "admin"
    ):

        return False


    return True


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():


    if not login_required():

        return redirect(
            "/login"
        )


    con = db()


    students = con.execute(

        """
        SELECT *
        FROM registrations
        ORDER BY id DESC
        """

    ).fetchall()


    con.close()


    page = """

    <!DOCTYPE html>

    <html>

    <head>

    <title>
    Admin Dashboard
    </title>

    """ + CSS + """

    </head>


    <body>


    <nav>


    <div>

    <b>
    🌿 Admin Dashboard
    </b>

    </div>


    <div>

    <a href="/admin">
    Students
    </a>

    <a href="/attendance">
    Attendance
    </a>


    {% if session.get("admin_role") == "superior" %}

    <a href="/admins">
    Admins
    </a>

    {% endif %}


    <a href="/logout">
    Logout
    </a>

    </div>


    </nav>


    <div class="container">


    <div class="card">


    <h1>
    Registered Students
    </h1>


    <p>

    Total Registrations:

    <b>
    {{students|length}}
    </b>

    </p>


    <div
    style="overflow-x:auto;"
    >


    <table>


    <tr>

    <th>
    ID
    </th>

    <th>
    Name
    </th>

    <th>
    Enrollment
    </th>

    <th>
    Mobile
    </th>

    <th>
    Payment
    </th>

    <th>
    Screenshot
    </th>

    <th>
    Payment Action
    </th>

    <th>
    Attendance
    </th>

    <th>
    PDF
    </th>

    </tr>


    {% for s in students %}


    <tr>


    <td>

    {{s["id"]}}

    </td>


    <td>

    {{s["full_name"]}}

    </td>


    <td>

    {{s["enrollment"]}}

    </td>


    <td>

    {{s["mobile"]}}

    </td>


    <!-- PAYMENT -->

    <td>

    <b>
    {{s["payment_method"]}}
    </b>

    <br><br>

    <b>

    {{s["payment_status"]}}

    </b>

    </td>


    <!-- SCREENSHOT -->

    <td>

    {% if s["payment_screenshot"] %}

    <a
    class="btn"
    href="/payment-screenshot/{{s["id"]}}"
    target="_blank"
    >

    👁 View

    </a>

    {% else %}

    No Screenshot

    {% endif %}

    </td>


    <!-- PAYMENT STATUS -->

    <td>


    <a
    class="btn"
    href="/payment/{{s["id"]}}/Success"
    >

    ✅ Success

    </a>


    <a
    class="btn"
    href="/payment/{{s["id"]}}/Pending"
    >

    ⏳ Pending

    </a>


    <a
    class="btn"
    href="/payment/{{s["id"]}}/Rejected"
    >

    ❌ Reject

    </a>


    </td>


    <td>

    {{s["attendance"]}}

    </td>


    <td>

    <a
    class="btn"
    href="/registration-pdf/{{s["id"]}}"
    >

    📄 PDF

    </a>

    </td>


    </tr>


    {% endfor %}


    </table>


    </div>


    </div>


    </div>


    </body>

    </html>

    """


    return render_template_string(

        page,

        students=students

    )


# =========================================================
# VIEW PAYMENT SCREENSHOT
# =========================================================

@app.route(
    "/payment-screenshot/<int:student_id>"
)
def payment_screenshot(student_id):


    if not login_required():

        return redirect(
            "/login"
        )


    con = db()


    student = con.execute(

        """
        SELECT payment_screenshot
        FROM registrations
        WHERE id=?
        """,

        (student_id,)

    ).fetchone()


    con.close()


    if not student:

        return (
            "Student not found",
            404
        )


    filename = student[
        "payment_screenshot"
    ]


    if not filename:

        return (
            "No payment screenshot uploaded.",
            404
        )


    filepath = os.path.join(

        app.config[
            "UPLOAD_FOLDER"
        ],

        filename

    )


    if not os.path.exists(
        filepath
    ):

        return (
            "Payment screenshot file not found.",
            404
        )


    return send_file(
        filepath
    )


# =========================================================
# UPDATE PAYMENT STATUS
# =========================================================

@app.route(
    "/payment/<int:student_id>/<status>"
)
def update_payment_status(

    student_id,
    status

):


    if not login_required():

        return redirect(
            "/login"
        )


    allowed_statuses = [

        "Success",

        "Pending",

        "Pending Verification",

        "Rejected"

    ]


    if status not in allowed_statuses:

        return (
            "Invalid payment status",
            400
        )


    con = db()


    con.execute(

        """
        UPDATE registrations
        SET payment_status=?
        WHERE id=?
        """,

        (
            status,
            student_id
        )

    )


    con.commit()

    con.close()


    return redirect(
        "/admin"
    )


# =========================================================
# ATTENDANCE
# =========================================================

@app.route("/attendance")
def attendance():


    if not login_required():

        return redirect(
            "/login"
        )


    con = db()


    students = con.execute(

        """
        SELECT *
        FROM registrations
        ORDER BY full_name
        """

    ).fetchall()


    con.close()


    page = """

    <!DOCTYPE html>

    <html>

    <head>

    <title>
    Attendance
    </title>

    """ + CSS + """

    </head>


    <body>


    <nav>


    <div>

    <b>
    ✅ Attendance Management
    </b>

    </div>


    <div>

    <a href="/admin">
    Admin Dashboard
    </a>

    <a href="/logout">
    Logout
    </a>

    </div>


    </nav>


    <div class="container">


    <div class="card">


    <h1>
    Student Attendance
    </h1>


    <p>

    You can mark students as
    Present or Absent.

    </p>


    <div
    style="overflow-x:auto;"
    >


    <table>


    <tr>

    <th>
    ID
    </th>

    <th>
    Student
    </th>

    <th>
    Enrollment
    </th>

    <th>
    Current Status
    </th>

    <th>
    Action
    </th>

    </tr>


    {% for s in students %}


    <tr>


    <td>

    {{s["id"]}}

    </td>


    <td>

    {{s["full_name"]}}

    </td>


    <td>

    {{s["enrollment"]}}

    </td>


    <td>

    <b>
    {{s["attendance"]}}
    </b>

    </td>


    <td>


    <a

    class="btn"

    href="/attendance/{{s["id"]}}/Present"

    >

    Present

    </a>


    <a

    class="btn"

    href="/attendance/{{s["id"]}}/Absent"

    >

    Absent

    </a>


    </td>


    </tr>


    {% endfor %}


    </table>


    </div>


    </div>


    </div>


    </body>

    </html>

    """


    return render_template_string(

        page,

        students=students

    )


# =========================================================
# UPDATE ATTENDANCE
# =========================================================

@app.route(
    "/attendance/<int:student_id>/<status>"
)
def update_attendance(

    student_id,
    status

):


    if not login_required():

        return redirect(
            "/login"
        )


    if status not in [

        "Present",

        "Absent",

        "Pending"

    ]:

        return (
            "Invalid attendance status",
            400
        )


    con = db()


    con.execute(

        """
        UPDATE registrations
        SET attendance=?
        WHERE id=?
        """,

        (
            status,
            student_id
        )

    )


    con.commit()

    con.close()


    return redirect(
        "/attendance"
    )


# =========================================================
# SUPERIOR ADMIN MANAGEMENT
# =========================================================

@app.route("/admins")
def admins():


    if not login_required():

        return redirect(
            "/login"
        )


    if session.get(
        "admin_role"
    ) != "superior":

        return (
            "Access denied",
            403
        )


    con = db()


    admin_list = con.execute(

        """
        SELECT
        id,
        name,
        email,
        role
        FROM admins
        ORDER BY id
        """

    ).fetchall()


    con.close()


    page = """

    <!DOCTYPE html>

    <html>

    <head>

    <title>
    Manage Admins
    </title>

    """ + CSS + """

    </head>


    <body>


    <nav>


    <div>

    <b>
    👥 Admin Management
    </b>

    </div>


    <div>

    <a href="/admin">
    Dashboard
    </a>

    <a href="/logout">
    Logout
    </a>

    </div>


    </nav>


    <div class="container">


    <div class="card">


    <h2>
    Add New Admin
    </h2>


    <form
    method="POST"
    action="/admins/add"
    >


    <label>
    Name
    </label>

    <input
    name="name"
    required
    >


    <label>
    Email
    </label>

    <input
    type="email"
    name="email"
    required
    >


    <label>
    Password
    </label>

    <input
    type="password"
    name="password"
    required
    >


    <button type="submit">

    Add Admin

    </button>


    </form>


    </div>


    <div class="card">


    <h2>
    Existing Admins
    </h2>


    <div
    style="overflow-x:auto;"
    >


    <table>


    <tr>

    <th>
    Name
    </th>

    <th>
    Email
    </th>

    <th>
    Role
    </th>

    <th>
    Action
    </th>

    </tr>


    {% for a in admins %}


    <tr>


    <td>

    {{a["name"]}}

    </td>


    <td>

    {{a["email"]}}

    </td>


    <td>

    {{a["role"]}}

    </td>


    <td>


    {% if a["role"] != "superior" %}


    <a
    href="/admins/delete/{{a["id"]}}"
    >

    Remove

    </a>


    {% else %}


    Superior Admin


    {% endif %}


    </td>


    </tr>


    {% endfor %}


    </table>


    </div>


    </div>


    </div>


    </body>

    </html>

    """


    return render_template_string(

        page,

        admins=admin_list

    )


# =========================================================
# ADD ADMIN
# =========================================================

@app.route(
    "/admins/add",
    methods=["POST"]
)
def add_admin():


    if not login_required():

        return redirect(
            "/login"
        )


    if session.get(
        "admin_role"
    ) != "superior":

        return (
            "Access denied",
            403
        )


    name = request.form.get(

        "name",

        ""

    ).strip()


    email = request.form.get(

        "email",

        ""

    ).lower().strip()


    password = request.form.get(

        "password",

        ""

    )


    if (

        not name

        or not email

        or not password

    ):

        return redirect(
            "/admins"
        )


    con = db()


    try:


        con.execute(

            """
            INSERT INTO admins
            (
                name,
                email,
                password,
                role
            )

            VALUES (?,?,?,?)
            """,

            (
                name,
                email,
                password,
                "admin"
            )

        )


        con.commit()


    except sqlite3.IntegrityError:

        pass


    con.close()


    return redirect(
        "/admins"
    )


# =========================================================
# DELETE ADMIN
# =========================================================

@app.route(
    "/admins/delete/<int:admin_id>"
)
def delete_admin(admin_id):


    if not login_required():

        return redirect(
            "/login"
        )


    if session.get(
        "admin_role"
    ) != "superior":

        return (
            "Access denied",
            403
        )


    con = db()


    con.execute(

        """
        DELETE FROM admins
        WHERE id=?
        AND role!='superior'
        """,

        (admin_id,)

    )


    con.commit()

    con.close()


    return redirect(
        "/admins"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/login"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(

            os.environ.get(

                "PORT",

                5000

            )

        )

    )
```
