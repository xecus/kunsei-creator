import base64
import os
from io import BytesIO
from typing import Optional

from openai import OpenAI
from PIL import Image
from pydantic import BaseModel, Field


# データモデル定義
class DetectionResult(BaseModel):
    """温度計検出結果のデータモデル"""

    detectable: Optional[bool] = Field(..., description="温度計を画像から検出できたか")
    readable: Optional[bool] = Field(..., description="温度計の値を画像から読み込めるかどうか")
    temp: Optional[float] = Field(..., description="温度計が指し示す温度")
    unit: Optional[str] = Field(..., description="温度計の温度の単位系")
    raw_digits: Optional[str] = Field(..., description="温度計の表示")


# システムプロンプト定義
SYSTEM_INSTRUCTIONS = """
You are a vision-language model specialized in detecting and reading digital thermometers.
Your task is to extract the EXACT digits shown on the display.

You MUST follow these rules strictly:

1. Detect the digital display area.
2. Read the digits EXACTLY as shown, including the decimal point.
3. Set "raw_digits" to the EXACT characters you see (example: "79.2", "173.1").
4. The "temp" value MUST be created by parsing raw_digits as a float.
   - If raw_digits = "173.1", then temp MUST BE 173.1
   - If raw_digits = "79.2", then temp MUST BE 79.2
   - Never remove or move the decimal point.
5. You MUST verify that temp == parsed(raw_digits). 
   If the values do NOT match, set:
     readable = false
     temp = null
     note = "Mismatch between raw_digits and temp (sanity check failed)."
6. Perform the read 3 times internally.
   If any of the 3 differ, set readable = false.
7. Apply the realistic temperature check:
   - If temp < -30 or temp > 200 (°C range), set readable = false and note why.
8. Never modify, reinterpret, or normalize raw_digits.
   raw_digits is the single source of truth.
"""

USER_PROMPT = """
Please analyze this image and extract the value displayed on the digital thermometer.

Steps you must follow:
1. Locate the digital display area.
2. Verify that the digits are fully visible.
3. Carefully read the digits exactly as they appear (including decimal point).
4. Determine whether the unit (°C or °F) is shown.
5. Cross-check the digits twice before returning the result.

Return the result strictly in the JSON format defined in the system instructions.
"""

# デフォルト設定
#DEFAULT_MODEL_NAME = "gpt-5-mini"
DEFAULT_MODEL_NAME = "gpt-4o-mini"
DEFAULT_IMAGE_PATH = "captured_image_latest.jpg"


def load_image_as_base64(image_path: str) -> str:
    """
    画像を読み込み、Base64エンコードして返す

    Args:
        image_path: 画像ファイルのパス

    Returns:
        Base64エンコードされた画像データ
    """
    with open(image_path, "rb") as f:
        img = Image.open(BytesIO(f.read()))

    print(f"画像サイズ: {img.size}")

    # PNG形式でBase64エンコード
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    print("画像を読み込みました")
    return image_base64


def analyze_thermometer(
    client: OpenAI, model_name: str, image_base64: str
) -> Optional[DetectionResult]:
    """
    温度計の画像を解析する

    Args:
        client: OpenAIクライアント
        model_name: 使用するモデル名
        image_base64: Base64エンコードされた画像データ

    Returns:
        DetectionResult: 検出結果（エラー時はNone）
    """
    try:
        response = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                    ],
                },
            ],
            response_format=DetectionResult,
        )

        result = response.choices[0].message.parsed
        return result

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print(f"使用モデル: {model_name}")
        return None


def main():
    """メイン処理"""
    # 環境変数から設定を読み込み
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)
    image_path = os.getenv("IMAGE_PATH", DEFAULT_IMAGE_PATH)

    # OpenAIクライアントの初期化
    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"API接続先: {base_url or 'OpenAI公式'}")
    print(f"使用モデル: {model_name}")

    # 画像を読み込み
    image_base64 = load_image_as_base64(image_path)

    # 温度計を解析
    result = analyze_thermometer(client, model_name, image_base64)

    # 結果を表示
    if result:
        print("\n=== 解析結果 ===")
        print(result.model_dump_json(indent=2))
    else:
        print("解析に失敗しました")


if __name__ == "__main__":
    main()

