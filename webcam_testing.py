import cv2


def show_webcam():
    """
    Webカメラの映像をウィンドウに表示し続ける
    'q'キーまたはESCキーで終了
    """
    # カメラを開く（0は通常デフォルトのカメラ）
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("エラー: カメラを開けませんでした")
        return

    # 解像度を1280x720に設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("カメラを起動しました")
    print("終了するには 'q' キーまたは ESC キーを押してください")

    while True:
        # フレームを読み込む
        ret, frame = cap.read()

        if not ret:
            print("エラー: フレームの取得に失敗しました")
            break

        # ウィンドウに表示
        cv2.imshow("Webcam", frame)

        # キー入力を待つ（1ms）
        key = cv2.waitKey(1) & 0xFF

        # 'q'キーまたはESCキー（27）で終了
        if key == ord("q") or key == 27:
            break

    # リソースを解放
    cap.release()
    cv2.destroyAllWindows()
    print("カメラを終了しました")


if __name__ == "__main__":
    show_webcam()
