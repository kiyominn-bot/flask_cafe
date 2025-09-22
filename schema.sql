-- ユーザーテーブル
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    reset_token TEXT               -- パスワードリセット用の列を追加
);

-- 商品テーブル
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,            -- 商品名（日本語入力可）
    quantity INTEGER NOT NULL,     -- 在庫数量
    unit TEXT,                     -- 単位（例: 個, 枚, 箱）
    supplier TEXT,                 -- 仕入れ先（日本語入力可）
    min_quantity INTEGER           -- 最低在庫数
);

-- 仕入れ履歴テーブル
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    date TEXT,                    -- 追加: 登録日
    quantity INTEGER NOT NULL,     -- 仕入れ数量
    price INTEGER,                 -- 仕入れ価格
    user_name TEXT,                -- 追加: 登録したユーザー名
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
