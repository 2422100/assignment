import flet as ft
import json
import requests

# JSONファイルのパス
json_file_path = "/Users/marina/Lecture/DS-Programming2/jma/area.json"

# JSONデータの読み込み
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# officesから地域名と地域コードを抽出
offices = data.get('offices', {})
REGION_CODES = {}
for offices_id, offices_info in offices.items():
    name = offices_info.get('name')
    if name and offices_id:
        REGION_CODES[name] = offices_id

# デバッグ用にREGION_CODESを表示（開発中のみ）
print("REGION_CODES:", REGION_CODES)

# JMAのAPIのベースURL
API_BASE_URL = 'https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json'

def main(page: ft.Page):
    page.title = "地域別天気アプリ（JMA）"
    page.padding = 20
    page.window_width = 800
    page.window_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.debug_show = True  # デバッグ情報を表示（オプション）

    # 天気情報を表示するためのコントロール
    city_text = ft.Text(
        value="地域を選択して天気を確認してください。",
        size=24,
        weight="bold"
    )
    description_text = ft.Text(value="", size=20)
    wind_text = ft.Text(value="", size=20)
    wave_text = ft.Text(value="", size=20)
    weather_icon = ft.Image(src="", width=100, height=100, visible=False)
    loading_indicator = ft.ProgressRing(visible=False)

    # 天気情報を表示するためのコンテナ
    weather_container = ft.Column(
        controls=[
            city_text,
            description_text,
            wind_text,
            wave_text,
            weather_icon
        ],
        spacing=10
    )

    def fetch_weather(region_code, city_name):
        url = API_BASE_URL.format(region_code)

        # ローディングインディケータを表示
        loading_indicator.visible = True
        page.update()

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    raise ValueError("APIからのデータが空です。")

                # JMAのデータ構造に基づいて必要な情報を抽出
                time_series = data[0].get('timeSeries', [])
                if not time_series:
                    raise ValueError("timeSeries データが見つかりません。")

                # 直近の天気情報を取得
                current_weather = time_series[0]
                weathers = current_weather.get('areas', [])
                if not weathers:
                    raise ValueError("areas データが見つかりません。")

                weather_description = weathers[0].get('weathers', ["データなし"])[0]
                weather_wind = weathers[0].get('winds', ["データなし"])[0]
                weather_wave = weathers[0].get('waves', ["データなし"])[0]
                # JMA APIでは直接的な温度データが含まれていない場合が多い
                # 必要に応じて別のAPIやデータソースを使用して温度情報を取得する

                # 天気情報を更新
                city_text.value = f"{city_name} の天気"
                description_text.value = f"状況: {weather_description}"
                wind_text.value = f"風: {weather_wind}"
                wave_text.value = f"波: {weather_wave}"

                weather_icon.visible = False  # JMA APIには公式のアイコンがないため非表示
            else:
                city_text.value = "エラー"
                description_text.value = f"天気情報の取得に失敗しました。ステータスコード: {response.status_code}"
                description_text.size = 16
                wind_text.value = f"天気情報の取得に失敗しました。ステータスコード: {response.status_code}"
                wind_text.size = 16
                wave_text.value = f"天気情報の取得に失敗しました。ステータスコード: {response.status_code}"
                wave_text.size = 16
                weather_icon.visible = False
        except Exception as ex:
            city_text.value = "エラー"
            description_text.value = f"エラーが発生しました: {ex}"
            wind_text.value = f"エラーが発生しました: {ex}"
            wave_text.value = f"エラーが発生しました: {ex}"
            weather_icon.visible = False
        finally:
            # ローディングインディケータを非表示
            loading_indicator.visible = False
            page.update()

    def on_region_change(e):
        selected = region_dropdown.value
        if selected:
            region_code = REGION_CODES.get(selected)
            if region_code:
                fetch_weather(region_code, selected)
            else:
                city_text.value = "エラー"
                description_text.value = "無効な地域コードです。"
                wind_text.value = ""
                wave_text.value = ""
                weather_icon.visible = False
                page.update()

    # Dropdownを作成
    region_dropdown = ft.Dropdown(
        label="地域を選択",
        options=[ft.dropdown.Option(city) for city in REGION_CODES.keys()],
        width=300,
        on_change=on_region_change,
    )

    # ローディングインディケータを中央に配置
    loading_view = ft.Row(
        controls=[loading_indicator],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # レイアウトを構築
    page.add(
        region_dropdown,
        loading_view,
        ft.Divider(height=20, color=ft.colors.GREY),
        weather_container
    )

# Fletアプリケーションを実行
ft.app(target=main)