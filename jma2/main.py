import flet as ft
import json
import requests
from collections import defaultdict
from datetime import datetime

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
    
    # 複数日の天気情報を表示するためのリストビュー
    weather_list = ft.ListView(
        expand=True,
        auto_scroll=True,
        spacing=10,
        padding=10
    )
    
    loading_indicator = ft.ProgressRing(visible=False)

    # 天気情報を表示するためのコンテナ
    weather_container = ft.Column(
        controls=[
            city_text,
            weather_list
        ],
        spacing=10,
        expand=True  # ListViewが拡張されるように設定
    )

    def fetch_weather(region_code, office_name):
        url = API_BASE_URL.format(region_code)
        print(f"Fetching weather data from URL: {url}")  # デバッグ

        # ローディングインディケータを表示
        loading_indicator.visible = True
        page.update()

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    raise ValueError("APIからのデータが空です。")
                
                # 最初のレポートを使用
                report = data[0]
                time_series_list = report.get('timeSeries', [])
                if not time_series_list:
                    raise ValueError("timeSeries データが見つかりません。")
                
                # 各timeSeriesをタイプ別に分類
                weather_ts = None
                pops_ts = None
                temps_ts = None

                # 天気コードのタイムシリーズを取得
                weather_codes_ts = None

                for ts in time_series_list:
                    areas = ts.get('areas', [])
                    if not areas:
                        continue
                    # 天気関連のキーが存在するか確認
                    if 'weathers' in areas[0]:
                        weather_ts = ts
                    elif 'pops' in areas[0]:
                        pops_ts = ts
                    elif 'temps' in areas[0]:
                        temps_ts = ts
                    elif 'weatherCodes' in areas[0]:  # 天気コードのキーがある場合
                        weather_codes_ts = ts

                if not weather_ts or not pops_ts:
                    raise ValueError("必要なtimeSeriesデータが不足しています。")

                # データ取得関数の定義
                def get_first_area_data(ts, key):
                    areas = ts.get('areas', [])
                    if not areas:
                        return []
                    area = areas[0]  # 最初のareaを取得
                    print(f"Processing area: {area['area']['name']}")  # デバッグ
                    return area.get(key, [])

                # 気温データはtimeSeries内の別のオブジェクトに存在する場合がある
                temps_times = []
                temps = []
                if temps_ts:
                    temps_times = temps_ts.get('timeDefines', [])
                    temps = get_first_area_data(temps_ts, 'temps')

                # 時間定義の取得
                weather_times = weather_ts.get('timeDefines', [])
                pops_times = pops_ts.get('timeDefines', [])

                weathers = get_first_area_data(weather_ts, 'weathers')
                winds = get_first_area_data(weather_ts, 'winds')
                waves = get_first_area_data(weather_ts, 'waves')
                pops = get_first_area_data(pops_ts, 'pops')

                # 天気コードの取得
                # 天気コードを取得する部分を修正
                if weather_ts:
                    areas = weather_ts.get('areas', [])
                    if areas:
                        # 最初のエリアから天気コードを取得
                        weather_codes = areas[0].get('weatherCodes', [])
                    else:
                        weather_codes = ["unknown"] * len(weathers)
                else:
                    weather_codes = ["unknown"] * len(weathers)

                # 日付をキーとする辞書にデータを統合
                daily_data = defaultdict(dict)

                # Helper function to extract date string
                def extract_date(time_str):
                    return datetime.fromisoformat(time_str).strftime("%Y-%m-%d")

                # 天気、風、波のデータを統合
                for i, time_define in enumerate(weather_times):
                    date = extract_date(time_define)
                    daily_data[date]['description'] = weathers[i] if i < len(weathers) else "データなし"
                    daily_data[date]['wind'] = winds[i] if i < len(winds) else "データなし"
                    daily_data[date]['wave'] = waves[i] if i < len(waves) else "データなし"
                    daily_data[date]['weather_code'] = weather_codes[i] if i < len(weather_codes) else "unknown"

                # 降水確率のデータを統合
                for i, time_define in enumerate(pops_times):
                    date = extract_date(time_define)
                    daily_data[date]['pop'] = pops[i] if i < len(pops) else "データなし"

                # 気温のデータを統合（存在する場合）
                for i, time_define in enumerate(temps_times):
                    date = extract_date(time_define)
                    daily_data[date]['temp'] = temps[i] if i < len(temps) else "データなし"

                # UIをクリア
                weather_list.controls.clear()

                # 各日のデータをリストビューに追加
                for date in sorted(daily_data.keys()):
                    day_info = daily_data[date]
                    
                    weather_code = day_info.get('weather_code', 'unknown')
                    
                    # PNG形式に変更
                    icon_url = f"https://www.jma.go.jp/bosai/forecast/img/{weather_code}.png"
                    fallback_icon_url = "https://www.jma.go.jp/bosai/forecast/img/unknown.png"

                    # デバッグ用にURLを表示
                    print(f"Date: {date}, Weather Code: {weather_code}, Icon URL: {icon_url}")

                    # アイコンを表示するImageコンポーネント
                    weather_icon = ft.Image(
                        src=icon_url,
                        width=100,
                        height=100,
                        fit=ft.ImageFit.CONTAIN,
                    )

                    # 有効な画像か確認するための関数
                    def is_valid_image(url):
                        try:
                            head = requests.head(url)
                            return head.status_code == 200
                        except:
                            return False

                    if not is_valid_image(icon_url):
                        icon_url = fallback_icon_url
                        weather_icon.src = icon_url  # 代替画像を設定
                        print(f"Fallback icon used for date {date}")

                    # 天気内容を表示するTextコンポーネント
                    weather_description = ft.Text(
                        value=f"天気: {day_info.get('description', 'データなし')}",
                        size=16
                    )

                    # 天気アイコンと天気説明を左右に配置
                    weather_row = ft.Row(
                        controls=[
                            weather_description,
                            weather_icon
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # 左右に配置
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    )

                    # その他の天気情報（風、波、降水確率、気温）をテキストで表示
                    wind_text = ft.Text(
                        value=f"風: {day_info.get('wind', 'データなし')}",
                        size=16
                    )
                    wave_text = ft.Text(
                        value=f"波: {day_info.get('wave', 'データなし')}",
                        size=16
                    )
                    pop_text = ft.Text(
                        value=f"降水確率: {day_info.get('pop', 'データなし')}%",
                        size=16
                    )
                    temp_text = ft.Text(
                        value=f"気温: {day_info.get('temp', 'データなし')}°C",
                        size=16
                    )

                    # Card内に表示するコンテンツを配置
                    card_content = ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(value=f"日付: {date}", size=18, weight="bold"),
                            weather_row,
                            wind_text,
                            wave_text,
                            pop_text,
                            temp_text,
                        ])
                    )

                    # Cardコンポーネントにコンテンツを設定
                    item = ft.Card(
                        content=card_content
                    )
                    weather_list.controls.append(item)

                # デバッグ用にデータを出力
                print(f"Fetched weather data for {office_name}:")
                for date in sorted(daily_data.keys()):
                    print(date, daily_data[date])

                weather_list.update()

            else:
                # エラーメッセージの表示
                city_text.value = "エラー"
                weather_list.controls.clear()
                error_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(value="天気情報の取得に失敗しました。", size=20, color=ft.colors.RED),
                            ft.Text(value=f"ステータスコード: {response.status_code}", size=16)
                        ])
                    )
                )
                weather_list.controls.append(error_card)
                weather_list.update()
        except Exception as ex:
            # エラーメッセージの表示
            city_text.value = "エラー"
            weather_list.controls.clear()
            error_card = ft.Card(
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text(value="エラーが発生しました。", size=20, color=ft.colors.RED),
                        ft.Text(value=str(ex), size=16)
                    ])
                )
            )
            weather_list.controls.append(error_card)
            weather_list.update()
            print(f"Exception occurred: {ex}")  # デバッグ
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
        weather_list.controls.clear()
        weather_list.update()
        page.update()

    def on_office_change(e):
        selected_office = office_dropdown.value
        if selected_office:
            office_code = OFFICE_CODES.get(selected_office)
            if office_code:
                fetch_weather(office_code, selected_office)
            else:
                city_text.value = "エラー"
                weather_list.controls.clear()
                error_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(value="無効な地域コードです。", size=20, color=ft.colors.RED)
                        ])
                    )
                )
                weather_list.controls.append(error_card)
                weather_list.update()
        else:
            city_text.value = "地域を選択して天気を確認してください。"
            weather_list.controls.clear()
            weather_list.update()

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

    # ローディングインディケータを配置
    loading_view = ft.Row(
        controls=[loading_indicator],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # 地方ドロップダウンと地域ドロップダウンを横並びで配置
    dropdown_row = ft.Row(
        controls=[
            center_dropdown,
            ft.Container(width=20),  # ドロップダウン間のスペース
            office_dropdown
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10  # Row内の間隔を設定
    )

    # レイアウトを構築
    page.add(
        dropdown_row,
        loading_view,
        ft.Divider(height=20, color=ft.colors.GREY),
        weather_container
    )

# Fletアプリケーションを実行
ft.app(target=main)