import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, Response, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime
from datetime import date as dt_date
import secrets

# -----------------------------
# 初期設定
# -----------------------------
app = Flask(__name__)
app.secret_key = "sunabaco"   # 任意の秘密鍵
# SQLite の絶対パスを指定（PythonAnywhere用）
DATABASE = "/home/kiyominn/flask_cafe/cafe.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 招待コード（初回登録用）
INVITE_CODE = "sunabaco2025"

# -----------------------------
# ログイン管理
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = None

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user["id"], user["username"], user["password"])
    return None

# -----------------------------
# ユーザー登録
# -----------------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        invite_code = request.form["invite_code"]

        # 招待コードチェック
        if invite_code != INVITE_CODE:
            flash("招待コードが違います")
            return redirect(url_for("register"))

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)

        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                         (username,password))
            conn.commit()
            conn.close()

            # 登録後にそのままログイン状態にする
            conn = sqlite3.connect(DATABASE)

            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=?", (username,))
            user_id = cur.fetchone()
            conn.close()
            if user_id:
                login_user(User(user_id[0], username, password))
                flash("登録してログインしました！")
                return redirect(url_for("index"))

        except sqlite3.IntegrityError:
            flash("そのユーザー名はすでに使われています")
            conn.close()
    return render_template("register.html")

# -----------------------------
# ログイン・ログアウト
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect('cafe.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            login_user(User(user["id"], user["username"], user["password"]))
            return redirect(url_for("index"))
        else:
            flash("ユーザー名またはパスワードが正しくありません。<a href='/reset_password'>パスワードを忘れた方はこちら</a>", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------------
# 在庫一覧
# -----------------------------
@app.route("/")
@login_required
def index():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()
    return render_template("index.html", items=items)

# -----------------------------
# 商品追加
# -----------------------------
@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        unit = request.form["unit"]
        supplier = request.form["supplier"]
        min_quantity = int(request.form["min_quantity"])
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, quantity, unit, supplier, min_quantity) VALUES (?, ?, ?, ?, ?)",
            (name, quantity, unit, supplier, min_quantity)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_item.html")

# -----------------------------
# 仕入れ履歴
# -----------------------------
@app.route("/purchase_history")
@login_required
def purchase_history():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    cur.execute("""
        SELECT purchases.id, purchases.date, items.name AS item_name, 
               purchases.quantity, purchases.price, items.supplier, purchases.user_name
        FROM purchases
        JOIN items ON purchases.item_id = items.id
        WHERE purchases.date >= ?
        ORDER BY purchases.date DESC
    """, (thirty_days_ago.isoformat(),))
    records = cur.fetchall()

    conn.close()
    return render_template("purchase_history.html", purchases=records)

# -----------------------------
# 仕入れ削除
# -----------------------------
@app.route("/delete_purchase/<int:purchase_id>", methods=["POST"])
@login_required
def delete_purchase(purchase_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT item_id, quantity FROM purchases WHERE id = ?", (purchase_id,))
    purchase = cur.fetchone()

    if purchase:
        item_id = purchase["item_id"]
        quantity = purchase["quantity"]

        cur.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        cur.execute("UPDATE items SET quantity = quantity - ? WHERE id = ?", (quantity, item_id))
        conn.commit()

    conn.close()
    return redirect(url_for("purchase_history"))

# -----------------------------
# 仕入れ登録
# -----------------------------
@app.route("/add_purchase", methods=["GET", "POST"])
@login_required
def add_purchase():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM items")
    items = cur.fetchall()

    if request.method == "POST":
        item_id = int(request.form["item_id"])
        input_date = request.form["date"].strip()
        if input_date == "":
            input_date = dt_date.today().isoformat()
        quantity = int(request.form["quantity"])
        price = int(request.form["price"])

        # ユーザー名を一緒に保存
        cur.execute("""
            INSERT INTO purchases (item_id, date, quantity, price, user_name)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, input_date, quantity, price, current_user.username))

        cur.execute(
            "UPDATE items SET quantity = quantity + ? WHERE id = ?",
            (quantity, item_id)
        )

        conn.commit()
        conn.close()

        # 通知を出す
        flash(f"{current_user.username} さんが仕入れを登録しました！")
        return redirect(url_for("purchase_history"))

    conn.close()
    return render_template("add_purchase.html", items=items)

# -----------------------------
# パスワード再設定
# -----------------------------
@app.route("/reset_password", methods=["GET","POST"])
def reset_password():
    if request.method == "POST":
        username = request.form["username"]
        token = secrets.token_hex(16)
        conn = sqlite3.connect(DATABASE)

        cur = conn.cursor()
        cur.execute("UPDATE users SET reset_token=? WHERE username=?", (token, username))
        conn.commit()
        conn.close()
        return f"再設定リンク: <a href='/new_password/{token}'>こちら</a>"
    return render_template("reset_password.html")

@app.route("/new_password/<token>", methods=["GET","POST"])
def new_password(token):
    if request.method == "POST":
        new_pass = request.form["password"]
        conn = sqlite3.connect(DATABASE)

        cur = conn.cursor()
        cur.execute("UPDATE users SET password=?, reset_token=NULL WHERE reset_token=?",
                    (new_pass, token))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("new_password.html")

# -----------------------------
# 在庫削除
# -----------------------------
@app.route("/delete_item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    conn = sqlite3.connect(DATABASE)

    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# -----------------------------
# 在庫数の更新
# -----------------------------
@app.route("/update_quantity/<int:item_id>/<string:action>", methods=["POST"])
@login_required
def update_quantity(item_id, action):
    conn = sqlite3.connect(DATABASE)

    cur = conn.cursor()

    if action == "plus":
        cur.execute("UPDATE items SET quantity = quantity + 1 WHERE id = ?", (item_id,))
    elif action == "minus":
        cur.execute("UPDATE items SET quantity = quantity - 1 WHERE id = ? AND quantity > 0", (item_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# -----------------------------
# メイン
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
