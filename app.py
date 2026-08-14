from flask import Flask,request,session,redirect,url_for,render_template_string
from functools import wraps
import sqlite3,os
from datetime import datetime
app=Flask(__name__); app.secret_key=os.environ.get("SECRET_KEY","CHANGE_THIS_SECRET")
DB="trekking.db"
ADMIN_EMAIL=os.environ.get("SUPERIOR_ADMIN_EMAIL","bhattsmit451@gmail.com").lower()
ADMIN_PASSWORD=os.environ.get("SUPERIOR_ADMIN_PASSWORD","CHANGE_THIS")
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
c=db();c.execute("""CREATE TABLE IF NOT EXISTS registrations(id INTEGER PRIMARY KEY AUTOINCREMENT,full_name TEXT,enrollment TEXT,mobile TEXT,email TEXT,college_class TEXT,emergency_name TEXT,emergency_mobile TEXT,address TEXT,attendance TEXT DEFAULT 'Absent',created_at TEXT)""");c.commit();c.close()
def needlogin(f):
 @wraps(f)
 def w(*a,**k):
  if not session.get("admin"): return redirect("/login")
  return f(*a,**k)
 return w
CSS="""*{box-sizing:border-box}body{font-family:Arial;margin:0;background:#f3f7f2;color:#183322}header{background:#235b35;color:white;padding:22px;text-align:center}main{max-width:1000px;margin:auto;padding:20px}.card{background:white;padding:20px;margin:16px 0;border-radius:14px;box-shadow:0 2px 9px #0002}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:650px){.grid{grid-template-columns:1fr}}label{display:block;font-weight:bold;margin-top:8px}input,textarea{width:100%;padding:10px;margin-top:4px;border:1px solid #bbb;border-radius:8px}button,.btn{background:#235b35;color:white;border:0;padding:10px 14px;border-radius:8px;text-decoration:none;display:inline-block;margin:3px;cursor:pointer}.fee{text-align:center;font-size:28px;font-weight:bold;color:#985c00}.note,.success{padding:12px;border-radius:8px}.note{background:#fff3cd}.success{background:#d1e7dd;color:#0f5132}.login{max-width:430px;margin:70px auto}table{width:100%;border-collapse:collapse}th,td{padding:9px;border-bottom:1px solid #ddd;text-align:left}.scroll{overflow:auto}"""
HOME="""<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><style>"""+CSS+"""</style><header><h1>🌿 Ambla One Day Trekking Camp</h1><p>23/08/2026 • 6:00 AM – 6:00 PM</p><p>Organized by Ignited Youth Form BVN</p></header><main><div class=card><div class=fee>💰 Trip Fee: ₹300</div></div>{% if msg %}<div class='card success'>{{msg}}</div>{% endif %}<div class=card><h2>📝 Student Registration / વિદ્યાર્થી નોંધણી</h2><form method=post action='/register'><div class=grid><div><label>Full Name / પૂરું નામ *</label><input name=full_name required></div><div><label>Enrollment Number *</label><input name=enrollment required></div><div><label>Mobile Number *</label><input name=mobile required></div><div><label>Email</label><input name=email type=email></div><div><label>College / Class *</label><input name=college_class required></div><div><label>Emergency Contact Name *</label><input name=emergency_name required></div><div><label>Emergency Contact Mobile *</label><input name=emergency_mobile required></div></div><label>Address</label><textarea name=address></textarea><p class=note><b>Payment QR will be added later.</b></p><button>Submit Registration</button></form></div><div class=card><h2>📌 Rules</h2><ul><li>Do not harm nature.</li><li>Stay together.</li><li>Do not do any mischief — strictly.</li><li>Wear green, brown or nature camouflage colours.</li><li>Carry your lunchbox.</li></ul></div><div class=card><h2>📞 Contact</h2><p><b>IYF Vice President — Smit Bhatt</b><br>📱 7405485180</p><p>IYF Secretary: Shivang Gohel<br>સાહસ સંયોજક: Sagar Parmar</p></div><div class=card><h2>🔐 Admin Area</h2><a class=btn href='/login'>Admin Login</a></div><div class=card><div class=fee>Amount to Pay: ₹300</div></div></main>"""
LOGIN="""<style>"""+CSS+"""</style><div class='card login'><h2>🔐 Admin Login</h2><p>{{error}}</p><form method=post><label>Email</label><input name=email type=email required><label>Password</label><input name=password type=password required><button>Login</button></form><a href='/'>← Back</a></div>"""
ADMIN="""<style>"""+CSS+"""</style><header><h1>👑 Protected Admin Dashboard</h1><p>{{email}} — Superior Admin</p></header><main><div class=card><h2>Student Registrations ({{students|length}})</h2><a class=btn href='/logout'>Logout</a><div class=scroll><table><tr><th>ID</th><th>Name</th><th>Enrollment</th><th>Mobile</th><th>Class</th><th>Attendance</th><th>Action</th></tr>{% for s in students %}<tr><td>{{s.id}}</td><td>{{s.full_name}}</td><td>{{s.enrollment}}</td><td>{{s.mobile}}</td><td>{{s.college_class}}</td><td>{{s.attendance}}</td><td><a class=btn href='/attendance/{{s.id}}/Present'>Present</a><a class=btn href='/attendance/{{s.id}}/Late'>Late</a><a class=btn href='/attendance/{{s.id}}/Absent'>Absent</a></td></tr>{% else %}<tr><td colspan=7>No registrations yet.</td></tr>{% endfor %}</table></div></div></main>"""
@app.route("/")
def home(): return render_template_string(HOME,msg=request.args.get("message"))
@app.route("/register",methods=["POST"])
def register():
 req=["full_name","enrollment","mobile","college_class","emergency_name","emergency_mobile"]
 if any(not request.form.get(x,"").strip() for x in req): return redirect(url_for("home",message="Please fill all required fields."))
 c=db();c.execute("INSERT INTO registrations(full_name,enrollment,mobile,email,college_class,emergency_name,emergency_mobile,address,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(request.form["full_name"],request.form["enrollment"],request.form["mobile"],request.form.get("email",""),request.form["college_class"],request.form["emergency_name"],request.form["emergency_mobile"],request.form.get("address",""),datetime.now().isoformat()));c.commit();c.close()
 return redirect(url_for("home",message="Registration submitted successfully!"))
@app.route("/login",methods=["GET","POST"])
def login():
 error=""
 if request.method=="POST":
  if request.form.get("email","").lower()==ADMIN_EMAIL and request.form.get("password")==ADMIN_PASSWORD:
   session["admin"]=ADMIN_EMAIL;return redirect("/admin")
  error="Invalid email or password."
 return render_template_string(LOGIN,error=error)
@app.route("/admin")
@needlogin
def admin():
 c=db();students=c.execute("SELECT * FROM registrations ORDER BY id DESC").fetchall();c.close();return render_template_string(ADMIN,email=session["admin"],students=students)
@app.route("/attendance/<int:i>/<status>")
@needlogin
def attendance(i,status):
 if status in ("Present","Absent","Late"):
  c=db();c.execute("UPDATE registrations SET attendance=? WHERE id=?",(status,i));c.commit();c.close()
 return redirect("/admin")
@app.route("/logout")
def logout():session.clear();return redirect("/")
if __name__=="__main__":app.run(host="127.0.0.1",port=5000)
