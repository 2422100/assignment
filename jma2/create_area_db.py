import sqlite3
import json
import os
import csv

def create_database(db_name='area.db'):
    """
    SQLiteデータベースを作成し、指定されたテーブルを定義します。
    
    :param db_name: 作成するデータベースファイルの名前（デフォルトは 'area.db'）
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            code TEXT UNIQUE,
            name TEXT,
            enName TEXT,
            parent TEXT,
            children TEXT,
            officeName TEXT,
            kana TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"データベース '{db_name}' とテーブル 'area' を作成しました。")

def insert_data_from_json(json_file, db_name='area.db'):
    """
    JSONファイルからデータを読み込み、SQLiteデータベースに挿入します。
    
    :param json_file: 読み込むJSONファイルのパス
    :param db_name: 接続するデータベースファイルの名前（デフォルトは 'area.db'）
    """
    if not os.path.exists(json_file):
        print(f"JSONファイルが存在しません: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSONの解析中にエラーが発生しました: {e}")
            return
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 各レベルの処理
    levels = ['centers', 'offices', 'class10s', 'class15s', 'class20s']
    for level in levels:
        if level not in data:
            print(f"レベル '{level}' はJSONデータに含まれていません。スキップします。")
            continue
        entries = data[level]
        for code, details in entries.items():
            name = details.get('name')
            enName = details.get('enName')
            parent = details.get('parent') if level in ['offices', 'class10s', 'class15s', 'class20s'] else None
            children = details.get('children') if level in ['centers', 'offices'] else None
            officeName = details.get('officeName') if level in ['centers', 'offices'] else None
            kana = details.get('kana') if level == 'class20s' else None

            try:
                cursor.execute('''
                    INSERT INTO area (level, code, name, enName, parent, children, officeName, kana)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (level, code, name, enName, parent, 
                    ','.join(children) if children else None,
                    officeName, 
                    kana))
            except sqlite3.IntegrityError:
                print(f"重複したコードのためスキップしました: {code}")
                continue
            except Exception as e:
                print(f"データの挿入中にエラーが発生しました（コード: {code}）: {e}")
                continue
    
    conn.commit()
    conn.close()
    print("データの挿入が完了しました。")

def fetch_all_data(db_name='area.db'):
    """
    データベースから全データを取得して表示します。
    
    :param db_name: 接続するデータベースファイルの名前（デフォルトは 'area.db'）
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM area")
        rows = cursor.fetchall()
        
        # ヘッダーの表示
        print("{:<5} {:<12} {:<10} {:<30} {:<30} {:<30} {:<20}".format(
            "ID", "Level", "Code", "Name", "English Name", "Parent", "Children", "Office Name", "Kana"))
        print("-" * 140)
        
        for row in rows:
            id_, level, code, name, enName, parent, children, officeName, kana = row
            print("{:<5} {:<12} {:<10} {:<30} {:<30} {:<30} {:<20}".format(
                id_,
                level if level else "",
                code if code else "",
                name if name else "",
                enName if enName else "",
                parent if parent else "",
                children if children else "",
                officeName if officeName else "",
                kana if kana else ""
            ))
    except sqlite3.Error as e:
        print(f"エラーが発生しました: {e}")
    finally:
        conn.close()

def main():
    """
    メイン関数。データベースの作成、JSONデータの挿入、データの表示を実行します。
    """
    json_file = '/Users/marina/Lecture/DS-Programming2/jma2/area.json'
    db_name = 'area.db'      # SQLiteデータベースの名前
    
    create_database(db_name)
    insert_data_from_json(json_file, db_name)
    print("\n挿入されたデータを表示します:\n")
    fetch_all_data(db_name)

def export_to_csv(db_name='area.db', csv_file='area.csv'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM area")
    rows = cursor.fetchall()
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Level', 'Code', 'Name', 'enName', 'parent', 'children', 'officeName', 'Kana'])
        writer.writerows(rows)
    
    conn.close()
    print(f"{csv_file} にデータをエクスポートしました。")

if __name__ == '__main__':
    main()
    export_to_csv()