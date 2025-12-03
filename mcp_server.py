"""
温度取得や電気コンロを制御するMCPサーバー
"""
from mcp.server.fastmcp import FastMCP
import cv2
import base64
import os
import signal
import sys
import atexit
from gpiozero import OutputDevice
from openai import OpenAI

# 自作モジュールのインポート
from capture import capture_image
from vlm import load_image_as_base64, analyze_thermometer, DEFAULT_IMAGE_PATH, DEFAULT_MODEL_NAME

# GPIO設定
PIN = 17  # ピン番号(BCMの番号)
stove_relay = OutputDevice(PIN)

# OpenAIクライアントの初期化
#openai_client = OpenAI(
#    api_key=os.getenv("OPENAI_API_KEY"),
#    base_url=os.getenv("OPENAI_BASE_URL")
#)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# サーバーインスタンス作成
mcp = FastMCP("cooking-controller", host="0.0.0.0", port=8000)


@mcp.tool()
def get_pot_temperature(sensor_id: str) -> float:
    """鍋の温度を取得する

    Args:
        sensor_id: センサーID

    Returns:
        温度（摂氏）
    """
    print(f"センサーID {sensor_id} の温度を取得中...")

    # 1. Webカメラから画像を取得
    print("画像をキャプチャしています...")
    capture_success = capture_image()
    if not capture_success:
        print("エラー: 画像のキャプチャに失敗しました")
        return -1.0

    # 2. 画像をBase64エンコード
    print("画像を読み込んでいます...")
    try:
        image_base64 = load_image_as_base64(DEFAULT_IMAGE_PATH)
    except Exception as e:
        print(f"エラー: 画像の読み込みに失敗しました: {e}")
        return -1.0

    # 3. VLMで温度計を解析
    print("温度計を解析しています...")
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)
    result = analyze_thermometer(openai_client, model_name, image_base64)

    if result is None:
        print("エラー: 温度計の解析に失敗しました")
        return -1.0

    if not result.detectable:
        print("エラー: 温度計が検出できませんでした")
        return -1.0

    if not result.readable or result.temp is None:
        print("エラー: 温度計の値が読み取れませんでした")
        return -1.0

    temperature = float(result.temp)
    print(f"取得した温度: {temperature}{result.unit or '°C'}")
    return temperature


@mcp.tool()
def turn_on_stove(stove_id: int) -> str:
    """電気コンロをONにする

    Args:
        stove_id: 電気コンロのID（数字）

    Returns:
        実行結果のメッセージ
    """
    print(f"電気コンロ {stove_id} をONにしています...")
    stove_relay.on()
    result = f"電気コンロ {stove_id} をONにしました（GPIO {PIN} HIGH）"
    print(result)
    return result


@mcp.tool()
def turn_off_stove(stove_id: int) -> str:
    """電気コンロをOFFにする

    Args:
        stove_id: 電気コンロのID（数字）

    Returns:
        実行結果のメッセージ
    """
    print(f"電気コンロ {stove_id} をOFFにしています...")
    stove_relay.off()
    result = f"電気コンロ {stove_id} をOFFにしました（GPIO {PIN} LOW）"
    print(result)
    return result


# メイン実行部分（直接実行する場合）
if __name__ == "__main__":
    mcp.run(transport="sse")
