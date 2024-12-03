import flet as ft
import json
import requests

# 地域名と対応する地域コードの辞書
REGION_CODES = {
    '東京': '130000',
    '大阪': '270000',
    '名古屋': '230000',
    '札幌': '016000',
    '福岡': '400000'
}

# JMAのAPIのベースURL
API_BASE_URL = 'https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json'

def main(page: ft.Page):
    page.title = "地域別天気アプリ（JMA）"
    page.padding = 20
    page.window_width = 600
    page.window_height = 400
    page.vertical_alignment = ft.MainAxisAlignment.START

    city_text = ft.Text(value="地域を選択して天気を確認してください。", size=24, weight="bold")
    description_text = ft.Text(value="", size=20)
    temperature_text = ft.Text(value="", size=20)
    weather_icon = ft.Image(src="", width=100, height=100, visible=False)
    loading_indicator = ft.ProgressRing(visible=False)

    def fetch_weather(e):
        city = e.control.data
        region_code = REGION_CODES.get(city)
        if not region_code:
            city_text.value = "エラー"
            description_text.value = "無効な地域コードです。"
            temperature_text.value = ""
            weather_icon.visible = False
            page.update()
            return

        url = API_BASE_URL.format(region_code)

        loading_indicator.visible = True
        page.update()

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                time_series = data[0].get('timeSeries', [])
                if not time_series:
                    raise ValueError("天気情報が見つかりません。")

                current_weather = time_series[0]
                weather_description = current_weather['areas'][0]['weathers'][0]
                weather_temp = "データなし"

                city_text.value = f"{city} の天気"
                description_text.value = f"状況: {weather_description}"
                temperature_text.value = f"温度: {weather_temp}"
                weather_icon.visible = False
            else:
                city_text.value = "エラー"
                description_text.value = f"天気情報の取得に失敗しました。ステータスコード: {response.status_code}"
                description_text.size = 16
                temperature_text.value = ""
                weather_icon.visible = False
        except Exception as ex:
            city_text.value = "エラー"
            description_text.value = f"エラーが発生しました: {ex}"
            temperature_text.value = ""
            weather_icon.visible = False
        finally:
            loading_indicator.visible = False
            page.update()

    buttons = []
    for city in REGION_CODES.keys():
        btn = ft.ElevatedButton(
            text=city,
            data=city,
            on_click=fetch_weather
        )
        buttons.append(btn)

    page.add(
        ft.Row(
            buttons,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.Row([loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(height=20, color=ft.colors.GREY),
        description_text,
        temperature_text,
        weather_icon
    )

ft.app(target=main)