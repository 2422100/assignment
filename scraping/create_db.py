import pandas as pd
import sqlite3

# CSVファイルのパス
csv_file_path = '/Users/marina/Lecture/DS-Programming2/scraping/job_ranking_data.csv'

# データベースのパス
db_file_path = '/Users/marina/Lecture/DS-Programming2/scraping/job_ranking_data.db'

# CSVファイルを読み込み
df = pd.read_csv(csv_file_path)

# SQLiteデータベースに接続
conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()

# テーブルを作成
cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_ranking (
        企業名 TEXT,
        順位 INTEGER,
        カテゴリー TEXT,
        年収 TEXT,
        設立 TEXT,
        従業員数 TEXT,
        資本金 TEXT
    )
''')

# データを挿入
df.to_sql('job_ranking', conn, if_exists='append', index=False)

# コミットして閉じる
conn.commit()
conn.close()