import flet as ft
import sqlite3
from datetime import datetime

class WeatherApp:
    def __init__(self, weather_db='/Users/marina/Lecture/DS-Programming2/jma2/weather.db', area_db='/Users/marina/Lecture/DS-Programming2/jma2/area.db'):
        self.weather_db = weather_db
        self.area_db = area_db

    def connect_weather_db(self):
        return sqlite3.connect(self.weather_db)

    def connect_area_db(self):
        return sqlite3.connect(self.area_db)

    def get_regions(self):
        """地方の一覧を取得"""
        conn = self.connect_area_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT Code, Name 
                FROM area 
                WHERE Level = 'centers'
                ORDER BY ID
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"データベースエラー: {e}")
            return []
        finally:
            conn.close()

    def get_prefectures(self, region_code):
        """選択された地方に属する都道府県の一覧を取得"""
        conn = self.connect_area_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT Code, Name 
                FROM area 
                WHERE Level = 'offices' 
                AND parent = ?
                ORDER BY ID
            """, (region_code,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"データベースエラー: {e}")
            return []
        finally:
            conn.close()

    def get_weather_forecast(self, area_code):
        """weather.dbから特定のエリアの天気予報を取得"""
        conn = self.connect_weather_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    w.target_datetime,
                    w.weather_text,
                    w.wind_text,
                    p.probability,
                    t.temperature
                FROM weather_forecasts w
                LEFT JOIN precipitation_probability_forecasts p 
                    ON w.area_code = p.area_code 
                    AND w.target_datetime = p.target_datetime
                LEFT JOIN temperature_forecasts t 
                    ON w.area_code = t.area_code 
                    AND w.target_datetime = t.target_datetime
                WHERE w.area_code = ?
                ORDER BY w.target_datetime
                LIMIT 10
            """, (area_code,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"データベースエラー: {e}")
            return []
        finally:
            conn.close()

def main(page: ft.Page):
    page.title = "天気情報アプリ"
    page.padding = 20
    
    app = WeatherApp()

    # データテーブルの定義
    weather_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("日時")),
            ft.DataColumn(ft.Text("天気")),
            ft.DataColumn(ft.Text("風")),
            ft.DataColumn(ft.Text("降水確率")),
            ft.DataColumn(ft.Text("気温")),
        ],
        rows=[],
        border=ft.border.all(2, "grey"),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(3, "grey"),
        horizontal_lines=ft.border.BorderSide(1, "grey"),
    )

    # 都道府県選択用ドロップダウン
    prefecture_dd = ft.Dropdown(
        width=400,
        label="都道府県を選択",
        options=[],
        disabled=True
    )

    def on_region_change(e):
        # 地方が選択されたときの処理
        if region_dd.value:
            prefectures = app.get_prefectures(region_dd.value)
            prefecture_dd.options = [
                ft.dropdown.Option(key=code, text=name)
                for code, name in prefectures
            ]
            prefecture_dd.disabled = False
        else:
            prefecture_dd.options = []
            prefecture_dd.disabled = True
        page.update()

    def search_weather(e):
        # テーブルの行をクリア
        weather_table.rows.clear()
        
        if not prefecture_dd.value:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("都道府県を選択してください")))
            return
        
        print(f"選択された都道府県のコード: {prefecture_dd.value}")

        # 選択されたエリアの天気予報を取得
        forecasts = app.get_weather_forecast(prefecture_dd.value)
        
        if not forecasts:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("データが見つかりませんでした")))
            return

        # テーブルに天気予報データを追加
        for forecast in forecasts:
            target_time = datetime.fromisoformat(forecast[0].replace('Z', '+00:00'))
            weather_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(target_time.strftime('%Y-%m-%d %H:%M'))),
                        ft.DataCell(ft.Text(forecast[1] if forecast[1] else "-")),
                        ft.DataCell(ft.Text(forecast[2] if forecast[2] else "-")),
                        ft.DataCell(ft.Text(f"{forecast[3]}%" if forecast[3] else "-")),
                        ft.DataCell(ft.Text(f"{forecast[4]}℃" if forecast[4] else "-")),
                    ]
                )
            )
        
        page.update()

    # 地方選択用ドロップダウン
    regions = app.get_regions()
    region_dd = ft.Dropdown(
        width=400,
        label="地方を選択",
        options=[ft.dropdown.Option(key=code, text=name) for code, name in regions],
        on_change=on_region_change
    )

    # 検索ボタン
    search_button = ft.ElevatedButton(
        "天気を検索", 
        on_click=search_weather,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "white",
            },
            bgcolor={
                ft.MaterialState.DEFAULT: "blue",
            },
        )
    )

    # レイアウトの設定
    page.add(
        ft.Column([
            ft.Container(
                content=ft.Text("天気情報検索", size=30, weight=ft.FontWeight.BOLD),
                margin=ft.margin.only(bottom=20),
                alignment=ft.alignment.center
            ),
            ft.Container(
                content=region_dd,
                margin=ft.margin.only(bottom=10)
            ),
            ft.Container(
                content=prefecture_dd,
                margin=ft.margin.only(bottom=10)
            ),
            ft.Container(
                content=search_button,
                margin=ft.margin.only(bottom=20),
                alignment=ft.alignment.center
            ),
            weather_table
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)