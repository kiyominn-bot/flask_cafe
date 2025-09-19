-- 商品（在庫）テーブル
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 商品ID
    name TEXT NOT NULL,                   -- 商品名
    quantity INTEGER NOT NULL DEFAULT 0,  -- 在庫数
    unit TEXT,                            -- 単位（個、本、g など）
    supplier TEXT                         -- 仕入れ先
);

-- 仕入れ記録テーブル
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 仕入れID
    item_id INTEGER NOT NULL,             -- 紐づく商品ID
    date TEXT NOT NULL,                   -- 仕入れ日
    quantity INTEGER NOT NULL,            -- 仕入れ数量
    price INTEGER,                         -- 仕入れ価格
    FOREIGN KEY (item_id) REFERENCES items(id)
);
