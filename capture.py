import cv2
from datetime import datetime
from pathlib import Path


def capture_image() -> bool:
    """
    Webカメラから静止画を1枚取得して保存する
    capturedフォルダーにcaptured_image_latest.jpgとYYYY-MM-DD-HH-MM-SS.jpgを保存

    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    # capturedフォルダーを作成（存在しない場合のみ）
    captured_dir = Path("captured")
    captured_dir.mkdir(exist_ok=True)

    # カメラを開く（0は通常デフォルトのカメラ）
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("エラー: カメラを開けませんでした")
        return False

    # 解像度を1280x720に設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # フレームを読み込む
    ret, frame = cap.read()

    if ret:
        # タイムスタンプ付きファイル名を生成
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        timestamp_path = captured_dir / f"{timestamp}.jpg"
        #latest_path = captured_dir / "captured_image_latest.jpg"
        latest_path = "captured_image_latest.jpg"

        # 画像を2つのファイルとして保存
        cv2.imwrite(str(timestamp_path), frame)
        cv2.imwrite(str(latest_path), frame)

        print(f"画像を保存しました: {timestamp_path}")
        print(f"画像を保存しました: {latest_path}")
        success = True
    else:
        print("エラー: フレームの取得に失敗しました")
        success = False

    # カメラを解放
    cap.release()

    return success


if __name__ == "__main__":
    capture_image()
