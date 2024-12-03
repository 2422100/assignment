import flet as ft
import json
import requests

# JSONファイルのパス
json_file_path = "/Users/marina/Lecture/DS-Programming2/jma/area.json"

# JSONデータの読み込み
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# centersから地方名と地方コードを抽出
centers = data.get('centers', {})
CENTER_CODES = {}
for center_id, center_info in centers.items():
    name = center_info.get('name')
    if name and center_id:
        CENTER_CODES[name] = center_id

# officesから地域名と地域コードを抽出
offices = data.get('offices', {})
OFFICE_CODES = {}
for office_id, office_info in offices.items():
    name = office_info.get('name')
    if name and office_id:
        OFFICE_CODES[name] = office_id

# 地方ごとに対応する地域名のリストを作成
CENTER_TO_OFFICES = {}
for center_name, center_id in CENTER_CODES.items():
    center_info = centers.get(center_id, {})
    children_ids = center_info.get('children', [])
    office_names = []
    for office_id in children_ids:
        office_info = offices.get(office_id, {})
        office_name = office_info.get('name')
        if office_name:
            office_names.append(office_name)
    CENTER_TO_OFFICES[center_name] = office_names

# デバッグ用にCENTER_CODESとCENTER_TO_OFFICESを表示
print("CENTER_CODES:", CENTER_CODES)
print("CENTER_TO_OFFICES:", CENTER_TO_OFFICES)

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
                # JMA APIでは直接的な温度データが含まれていない場合が多いため、必要に応じて別のAPIやデータソースを使用して温度情報を取得する

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

    def on_center_change(e):
        selected_center = center_dropdown.value
        if selected_center:
            # オフィスドロップダウンを更新
            offices_list = CENTER_TO_OFFICES.get(selected_center, [])
            office_dropdown.options = [ft.dropdown.Option(office) for office in offices_list]
            office_dropdown.value = None  # 選択をリセット
            office_dropdown.disabled = False  # 有効にする
        else:
            office_dropdown.options = []
            office_dropdown.value = None
            office_dropdown.disabled = True

        # 天気情報をリセット
        city_text.value = "地域を選択して天気を確認してください。"
        description_text.value = ""
        wind_text.value = ""
        wave_text.value = ""
        weather_icon.visible = False
        page.update()

    def on_office_change(e):
        selected_office = office_dropdown.value
        if selected_office:
            office_code = OFFICE_CODES.get(selected_office)
            if office_code:
                fetch_weather(office_code, selected_office)
            else:
                city_text.value = "エラー"
                description_text.value = "無効な地域コードです。"
                wind_text.value = ""
                wave_text.value = ""
                weather_icon.visible = False
                page.update()

    # センタードロップダウンを作成
    center_dropdown = ft.Dropdown(
        label="地方を選択",
        options=[ft.dropdown.Option(center) for center in CENTER_CODES.keys()],
        width=300,
        on_change=on_center_change,
    )

    # オフィスドロップダウンを作成（初期状態では無効）
    office_dropdown = ft.Dropdown(
        label="地域を選択",
        options=[],
        width=300,
        on_change=on_office_change,
        disabled=True  # センターが選択されるまで無効
    )

    # ローディングインディケータを中央に配置
    loading_view = ft.Row(
        controls=[loading_indicator],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # レイアウトを構築
    page.add(
        center_dropdown,
        ft.Container(height=10),  # スペースを追加
        office_dropdown,
        loading_view,
        ft.Divider(height=20, color=ft.colors.GREY),
        weather_container
    )

# Fletアプリケーションを実行
ft.app(target=main)