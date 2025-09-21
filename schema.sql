-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- 商品テーブル
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,          -- 商品名（日本語入力可）
    quantity INTEGER NOT NULL,   -- 在庫数量
    unit TEXT,                   -- 単位（例: 個, 枚, 箱）
    supplier TEXT,               -- 仕入れ先（日本語入力可）
    min_quantity INTEGER         -- 最低在庫数
);

-- 仕入れ履歴テーブル
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,   -- 仕入れ数量
    price INTEGER,               -- 仕入れ価格（直接入力）
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
