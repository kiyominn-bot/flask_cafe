-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- 商品テーブル
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit TEXT,
    supplier TEXT,
    min_quantity INTEGER
);

-- 仕入れ履歴テーブル
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    price INTEGER,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
