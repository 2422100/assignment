import sqlite3
import json
import os
import csv
import requests
from datetime import datetime

def create_database(db_name='weather.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publishing_offices (
            id INTEGER PRIMARY KEY,
            name TEXT,
            code TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            code TEXT PRIMARY KEY,
            name TEXT,
            area_type TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_forecasts (
            id INTEGER PRIMARY KEY,
            publishing_office_id INTEGER,
            report_datetime TEXT,
            area_code TEXT,
            target_datetime TEXT,
            weather_code TEXT,
            weather_text TEXT,
            wind_text TEXT,
            wave_text TEXT,
            FOREIGN KEY (publishing_office_id) REFERENCES publishing_offices(id),
            FOREIGN KEY (area_code) REFERENCES areas(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precipitation_probability_forecasts (
            id INTEGER PRIMARY KEY,
            publishing_office_id INTEGER,
            report_datetime TEXT,
            area_code TEXT,
            target_datetime TEXT,
            probability INTEGER,
            FOREIGN KEY (publishing_office_id) REFERENCES publishing_offices(id),
            FOREIGN KEY (area_code) REFERENCES areas(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temperature_forecasts (
            id INTEGER PRIMARY KEY,
            publishing_office_id INTEGER,
            report_datetime TEXT,
            area_code TEXT,
            target_datetime TEXT,
            temp_type TEXT,
            temperature REAL,
            temperature_upper REAL,
            temperature_lower REAL,
            FOREIGN KEY (publishing_office_id) REFERENCES publishing_offices(id),
            FOREIGN KEY (area_code) REFERENCES areas(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_forecasts (
            id INTEGER PRIMARY KEY,
            publishing_office_id INTEGER,
            report_datetime TEXT,
            area_code TEXT,
            target_date TEXT,
            weather_code TEXT,
            precipitation_probability INTEGER,
            reliability TEXT,
            FOREIGN KEY (publishing_office_id) REFERENCES publishing_offices(id),
            FOREIGN KEY (area_code) REFERENCES areas(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS climate_averages (
            id INTEGER PRIMARY KEY,
            publishing_office_id INTEGER,
            report_datetime TEXT,
            area_code TEXT,
            type TEXT,
            min_value REAL,
            max_value REAL,
            FOREIGN KEY (publishing_office_id) REFERENCES publishing_offices(id),
            FOREIGN KEY (area_code) REFERENCES areas(code)
        )
    ''')

    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_weather_forecasts_datetime 
                     ON weather_forecasts(target_datetime)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_precipitation_forecasts_datetime 
                     ON precipitation_probability_forecasts(target_datetime)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_temperature_forecasts_datetime 
                     ON temperature_forecasts(target_datetime)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_weekly_forecasts_date 
                     ON weekly_forecasts(target_date)''')

    conn.commit()
    conn.close()
    print(f"データベース '{db_name}' とテーブルを作成しました。")

def fetch_weather_data(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"データの取得中にエラーが発生しました: {e}")
        return None

def insert_data_from_json(data, db_name='weather.db'):
    if not data:
        print("データがありません")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        # publishing_officesテーブルにデータを挿入
        cursor.execute('''
            INSERT OR IGNORE INTO publishing_offices (name, code)
            VALUES (?, ?)
        ''', (data[0]['publishingOffice'], None))
        publishing_office_id = cursor.lastrowid

        # 各種データの挿入
        for forecast in data[0]['timeSeries']:
            # weather_forecastsテーブル
            if 'areas' in forecast and 'weatherCodes' in forecast['areas'][0]:
                for area in forecast['areas']:
                    for i, time in enumerate(forecast['timeDefines']):
                        cursor.execute('''
                            INSERT INTO weather_forecasts (
                                publishing_office_id, report_datetime, area_code,
                                target_datetime, weather_code, weather_text,
                                wind_text, wave_text
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            publishing_office_id,
                            data[0]['reportDatetime'],
                            area['area']['code'],
                            time,
                            area['weatherCodes'][i] if 'weatherCodes' in area else None,
                            area['weathers'][i] if 'weathers' in area else None,
                            area['winds'][i] if 'winds' in area else None,
                            area['waves'][i] if 'waves' in area else None
                        ))

            # precipitation_probability_forecastsテーブル
            elif 'areas' in forecast and 'pops' in forecast['areas'][0]:
                for area in forecast['areas']:
                    for i, time in enumerate(forecast['timeDefines']):
                        cursor.execute('''
                            INSERT INTO precipitation_probability_forecasts (
                                publishing_office_id, report_datetime, area_code,
                                target_datetime, probability
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (
                            publishing_office_id,
                            data[0]['reportDatetime'],
                            area['area']['code'],
                            time,
                            area['pops'][i] if area['pops'][i] != '' else None
                        ))

            # temperature_forecastsテーブル
            elif 'areas' in forecast and 'temps' in forecast['areas'][0]:
                for area in forecast['areas']:
                    for i, time in enumerate(forecast['timeDefines']):
                        cursor.execute('''
                            INSERT INTO temperature_forecasts (
                                publishing_office_id, report_datetime, area_code,
                                target_datetime, temperature
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (
                            publishing_office_id,
                            data[0]['reportDatetime'],
                            area['area']['code'],
                            time,
                            area['temps'][i] if area['temps'][i] != '' else None
                        ))

        # 週間予報データの挿入
        if len(data) > 1 and 'timeSeries' in data[1]:
            for forecast in data[1]['timeSeries']:
                for area in forecast['areas']:
                    for i, time in enumerate(forecast['timeDefines']):
                        cursor.execute('''
                            INSERT INTO weekly_forecasts (
                                publishing_office_id, report_datetime, area_code,
                                target_date, weather_code, precipitation_probability,
                                reliability
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            publishing_office_id,
                            data[1]['reportDatetime'],
                            area['area']['code'],
                            time,
                            area['weatherCodes'][i] if 'weatherCodes' in area else None,
                            area['pops'][i] if 'pops' in area and area['pops'][i] != '' else None,
                            area['reliabilities'][i] if 'reliabilities' in area else None
                        ))

        # 平均値データの挿入
        if 'tempAverage' in data[1]:
            for area in data[1]['tempAverage']['areas']:
                cursor.execute('''
                    INSERT INTO climate_averages (
                        publishing_office_id, report_datetime, area_code,
                        type, min_value, max_value
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    publishing_office_id,
                    data[1]['reportDatetime'],
                    area['area']['code'],
                    'temperature',
                    area['min'],
                    area['max']
                ))

        conn.commit()
        print("データベースへの挿入が完了しました")

    except sqlite3.Error as e:
        print(f"データベースエラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()

def get_area_codes_from_csv(csv_path='/Users/marina/Lecture/DS-Programming2/jma2/area.csv'):
    """CSVファイルからエリアコードを読み込む関数"""
    area_codes = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                if 'Code' in row:
                    area_codes.append(row['Code'])
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {e}")
    return area_codes

def main():
    # データベースの作成
    create_database()
    
    # CSVファイルからエリアコードを取得
    area_codes = get_area_codes_from_csv()
    
    if not area_codes:
        print("エリアコードを取得できませんでした。")
        return
    
    # 各エリアの天気予報データを取得してデータベースに格納
    for area_code in area_codes:
        print(f"エリアコード {area_code} の天気データを取得中...")
        weather_data = fetch_weather_data(area_code)
        if weather_data:
            insert_data_from_json(weather_data)
            print(f"エリアコード {area_code} のデータを保存しました。")
        else:
            print(f"エリアコード {area_code} のデータ取得に失敗しました。")

if __name__ == "__main__":
    main()