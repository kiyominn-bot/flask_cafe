import os
import sqlite3

# データベースがなければ作成
if not os.path.exists("cafe.db"):
    conn = sqlite3.connect("cafe.db")
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()

from flask import Flask, render_template,request, redirect, url_for, Response
import sqlite3
app = Flask(__name__)
app.secret_key = "sunabaco" 
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from flask import flash
import datetime
from datetime import date as dt_date

INVITE_CODE = "sunabaco2025"  # ← 好きな文字列に変更してください

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

        conn = sqlite3.connect("cafe.db")
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                         (username,password))
            conn.commit()
            flash("登録しました。ログインしてください。")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("そのユーザー名はすでに使われています")
        conn.close()
    return render_template("register.html")


app.secret_key = "your_secret_key"  # ← 適当な文字列に変更してください

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --- ユーザークラス ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user["id"], user["username"], user["password"])
    return None

# --- ログインページ ---
from flask import request, render_template, redirect, url_for
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

# --- ログアウト ---
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------------
#  ログイン設定（ユーザー名とパスワード）
# -----------------------------


# データベースに接続して items テーブルの内容を取得
def get_items():
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row  # 結果を辞書形式で取得
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()
    return items

# トップページ（在庫一覧）
@app.route("/")
@login_required
def index():
    conn = sqlite3.connect("cafe.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()
    return render_template("index.html", items=items)

@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        unit = request.form["unit"]
        supplier = request.form["supplier"]
        min_quantity = int(request.form["min_quantity"])

        conn = sqlite3.connect('cafe.db')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, quantity, unit, supplier, min_quantity) VALUES (?, ?, ?, ?, ?)",
            (name, quantity, unit, supplier, min_quantity)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_item.html")
@app.route("/purchase_history")
def purchase_history():
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 今日から30日前の日付を取得
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    cur.execute("""
        SELECT purchases.id, purchases.date, items.name AS item_name, 
           purchases.quantity, purchases.price, items.supplier
        FROM purchases
        JOIN items ON purchases.item_id = items.id
        WHERE purchases.date >= ?
        ORDER BY purchases.date DESC
    """, (thirty_days_ago.isoformat(),))
    records = cur.fetchall()

    conn.close()
    return render_template("purchase_history.html", purchases=records)
@app.route("/delete_purchase/<int:purchase_id>", methods=["POST"])
def delete_purchase(purchase_id):
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 削除対象の仕入れ情報を取得
    cur.execute("SELECT item_id, quantity FROM purchases WHERE id = ?", (purchase_id,))
    purchase = cur.fetchone()

    if purchase:
        item_id = purchase["item_id"]
        quantity = purchase["quantity"]

        # 仕入れ記録を削除
        cur.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        # 在庫数を減算
        cur.execute("UPDATE items SET quantity = quantity - ? WHERE id = ?", (quantity, item_id))

        conn.commit()

    conn.close()
    return redirect(url_for("purchase_history"))
@app.route("/add_purchase", methods=["GET", "POST"])
def add_purchase():
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 商品一覧を取得（プルダウン表示用）
    cur.execute("SELECT id, name FROM items")
    items = cur.fetchall()

    if request.method == "POST":
        item_id = int(request.form["item_id"])
        input_date = request.form["date"].strip()
        # 入力が空なら今日の日付を使う
        if input_date == "":
            input_date = dt_date.today().isoformat()
        quantity = int(request.form["quantity"])
        price = int(request.form["price"])

        # 仕入れ記録を登録
        cur.execute(
            "INSERT INTO purchases (item_id, date, quantity, price) VALUES (?, ?, ?, ?)",
            (item_id, input_date, quantity, price)
        )

        # 在庫数を加算
        cur.execute(
            "UPDATE items SET quantity = quantity + ? WHERE id = ?",
            (quantity, item_id)
        )

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("add_purchase.html", items=items)
import secrets

# パスワードリセット申請
@app.route("/reset_password", methods=["GET","POST"])
def reset_password():
    if request.method == "POST":
        username = request.form["username"]
        token = secrets.token_hex(16)
        conn = sqlite3.connect("cafe.db")
        cur = conn.cursor()
        cur.execute("UPDATE users SET reset_token=? WHERE username=?", (token, username))
        conn.commit()
        conn.close()
        # 実際はメール送信だが、今回は画面にリンクを表示
        return f"再設定リンク: <a href='/new_password/{token}'>こちら</a>"
    return render_template("reset_password.html")

# 新しいパスワード入力
@app.route("/new_password/<token>", methods=["GET","POST"])
def new_password(token):
    if request.method == "POST":
        new_pass = request.form["password"]
        conn = sqlite3.connect("cafe.db")
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=?, reset_token=NULL WHERE reset_token=?",
                    (new_pass, token))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("new_password.html")
from flask_login import logout_user

@app.route("/delete_item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    conn = sqlite3.connect("cafe.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))
@app.route("/update_quantity/<int:item_id>/<string:action>", methods=["POST"])
@login_required
def update_quantity(item_id, action):
    conn = sqlite3.connect("cafe.db")
    cur = conn.cursor()

    if action == "plus":
        cur.execute("UPDATE items SET quantity = quantity + 1 WHERE id = ?", (item_id,))
    elif action == "minus":
        cur.execute("UPDATE items SET quantity = quantity - 1 WHERE id = ? AND quantity > 0", (item_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
