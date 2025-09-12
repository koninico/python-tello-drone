import logging #ログ出力用
import contextlib #コンテキストマネージャ用
import os #OS関連
import socket #ソケット通信
import subprocess #サブプロセス実行用
import threading #スレッド関連
import time #時間関連

import cv2 as cv #OpenCVライブラリ
import numpy as np #数値計算ライブラリ

from droneapp.models.base import Singleton


logger = logging.getLogger(__name__) #loggerオブジェクトを取得、他のモジュールからも利用できるようにする

DEFAULT_DISTANCE = 0.30  # m (30cm)
DEFAULT_SPEED = 10  # cm/s
DEFAULT_DEGREE = 10  # 回転角度度数
DEFAULT_TIMEOUT = 5  # フリップ

# 映像ストリーミング関連の定数
FRAME_X = int(960/3)  # フレームの幅,1/3に縮小,顔認識のため
FRAME_Y = int(720/3)  # フレームの高さ
FRAME_AREA = FRAME_X * FRAME_Y  # フレームの面積
FRAME_SIZE = FRAME_AREA * 3  # フレームのサイズ,3はRGBなど3チャンネル分
FRAME_CENTER_X = FRAME_X / 2  # フレームの中心X座標
FRAME_CENTER_Y = FRAME_Y / 2  # フレームの中心Y座標

CMD_FFMPEG = (f'ffmpeg -hwaccel auto -hwaccel_device opencl -i pipe:0'
            f' -pix_fmt bgr24 -s {FRAME_X}x{FRAME_Y} -f rawvideo pipe:1')  # ffmpegコマンド

FACE_DETECT_XML_FILE = './droneapp/models/haarcascade_frontalface_default.xml'  # 顔検出用のXMLファイルパス

SNAPSHOT_IMAGE_FOLDER = './droneapp/static/img/snapshots'  # スナップショット画像の保存フォルダ

class ErrorNoFaceDetected(Exception): # 顔が検出されなかった場合の独自例外を作成
    """顔が検出されなかった場合の例外"""

class ErrorNoImageDir(Exception): # イメージ保存ディレクトリが存在しない場合の独自例外を作成
    """イメージ保存ディレクトリが存在しない場合の例外"""

class DroneManager(object, metaclass=Singleton):
    def __init__(self, host_ip='0.0.0.0', host_port=8889,
                drone_ip='192.168.10.1', drone_port=8889,
                is_imperial=False, speed=DEFAULT_SPEED):
        self.host_ip = host_ip #ホストのIPアドレス ,selfはクラスのインスタンス自身を指す
        self.host_port = host_port #ホストのポート番号
        self.drone_ip = drone_ip #ドローンのIPアドレス
        self.drone_port = drone_port #ドローンのポート番号
        self.drone_address = (self.drone_ip, self.drone_port) #ドローンのアドレス

        self.is_imperial = is_imperial #距離単位がフィートかどうかのフラグ
        self.speed = speed  # cm/s

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ポートの再利用を許可
        self.socket.settimeout(5.0)  # 5秒のタイムアウトを設定
        self.socket.bind((self.host_ip, self.host_port)) #ホストのIPアドレスとポート番号にバインド

        self.response =None #ドローンからの応答メッセージを格納する変数
        self.stop_event = threading.Event() #スレッドの停止イベントを管理するオブジェクト
        self._response_thread = threading.Thread(target=self.receive_response, args=(self.stop_event, )) #ドローンからの応答メッセージを受信するスレッドを作成
        self._response_thread.daemon = True  # デーモンスレッドに設定（メインプロセス終了時に自動終了）
        # receive_responseメソッドをセットしている
        self._response_thread.start() #スレッド（並列）を開始

        #パトロールモード関連の初期化
        self.patrol_event = None #パトロールイベントを管理するオブジェクト,onoffの切り替えのためNoneで初期化
        self.is_patrol = False #パトロールモードのフラグ、初期値はFalse
        self._patrol_semaphore = threading.Semaphore(1)  # パトロールモードのセマフォを初期化
        self._thread_patrol = None #パトロールモードのスレッドを管理する変数、Noneで初期化

        #顔追跡モード関連の初期化
        self.is_face_tracking = True  # 顔追跡モードのフラグ、初期値はTrue
        self._tracking_command_interval = 0.3  # 追跡コマンドの送信間隔（秒）- より短い間隔で素早い反応
        self._last_tracking_time = 0  # 最後に追跡コマンドを送信した時刻

        #映像ストリーミング関連の初期化
        self.proc = subprocess.Popen(CMD_FFMPEG.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE) #ffmpegのサブプロセスを起動
        self.proc_stdin = self.proc.stdin #ffmpegの標準入力パイプ
        self.proc_stdout = self.proc.stdout #ffmpegの標準出力パイプ

        self.video_port = 11111  # 映像ストリーミングのポート番号

        self._receive_video_thread = threading.Thread(
            target=self._receive_video,
            args=(self.stop_event, self.proc_stdin,
                self.host_ip,self.video_port)) #映像受信スレッドを作成
        
        self._receive_video_thread.start() #映像受信スレッドを開始

        # 顔検出用のカスケード分類器の初期化
        try:
            if not os.path.exists(FACE_DETECT_XML_FILE):
                raise ErrorNoFaceDetected(f"顔検出用のXMLファイルが見つかりません: {FACE_DETECT_XML_FILE}")
            
            self.face_cascade = cv.CascadeClassifier(FACE_DETECT_XML_FILE)  # 顔検出用のカスケード分類器を初期化
            
            # カスケードファイルが正しく読み込まれたかチェック
            if self.face_cascade.empty():
                raise ValueError(f"顔検出用のカスケードファイルの読み込みに失敗しました: {FACE_DETECT_XML_FILE}")
                
            logger.info(f"顔検出カスケードファイルを正常に読み込みました: {FACE_DETECT_XML_FILE}")
            
        except Exception as e:
            logger.error(f"顔検出の初期化に失敗しました: {e}")
            # フォールバック: 顔検出なしで続行
            self.face_cascade = None
            
        self._is_enable_face_detect = False  # 顔検出モードのフラグを初期化

        # スナップショット保存フォルダの確認と作成
        if not os.path.exists(SNAPSHOT_IMAGE_FOLDER):
            raise ErrorNoImageDir(f"スナップショット保存フォルダが存在しません: {SNAPSHOT_IMAGE_FOLDER}") 
        self.is_snapshot = False  # スナップショット撮影フラグを初期化  

        # コマンド送信関連の初期化,semaphoreを使って同時送信を防ぐ
        self._command_semaphore = threading.Semaphore(1)  # コマンド送信のセマフォを初期化
        self._command_thread = None  # コマンド送信スレッドを管理する変数、Noneで初期化

        # 初期化コマンドを送信（間隔を空ける）
        time.sleep(1)  # スレッドの開始を待つ
        self.send_command('command') #ドローンにSDKモード開始コマンドを送信
        time.sleep(2)  # commandの応答を待つ
        self.send_command('streamon') #ドローンに映像ストリーミング開始コマンドを送信
        self.set_speed(self.speed)  # ドローンの速度を設定

    def receive_response(self, stop_event): #ドローンからの応答メッセージを受信するメソッド
        while not stop_event.is_set(): #停止イベントがセットされていない間ループ
            try:
                self.response, ip = self.socket.recvfrom(3000) #ドローンからの応答メッセージを受信、最大3000バイト,3000はテロのサンプルコード
                try:
                    decoded_response = self.response.decode('utf-8')
                    logger.info({'action': 'receive_response', 'response': decoded_response, 'from': ip}) #ログに受信した応答メッセージを出力
                except UnicodeDecodeError:
                    # UTF-8でデコードできない場合は他のエンコーディングを試す
                    try:
                        decoded_response = self.response.decode('latin-1')
                        logger.info({'action': 'receive_response', 'response': decoded_response, 'from': ip, 'encoding': 'latin-1'})
                    except:
                        logger.info({'action': 'receive_response', 'raw_bytes': self.response.hex(), 'from': ip})
            except socket.timeout:
                continue  # タイムアウトの場合は続行
            except socket.error as e:
                logger.error({'action': 'receive_response', 'ex': e}) #ログにエラーメッセージを出力
                break #ループを抜ける

    def __del__(self): #デストラクタ、オブジェクトが破棄されるときに呼ばれる
        try:
            self.stop() #ドローンの停止
        except:
            pass  # デストラクタでは例外を無視

    def stop(self): #ドローンの停止
        if hasattr(self, 'stop_event'):
            self.stop_event.set() #停止イベントをセット
        
        # スレッドの終了を待機
        if hasattr(self, '_response_thread'):
            self._response_thread.join(timeout=2)  # 最大2秒待機
            
        if hasattr(self, 'socket'):
            self.socket.close() #ソケットを閉じる
        os.kill(self.proc.pid, 9)  # ffmpegプロセスを強制終了

    # 外部からのコマンドを受けて、内部の並列処理に送信するメソッド
    def send_command(self, command, blocking=True):
        self._command_thread = threading.Thread(
            target=self._send_command, 
            args=(command,blocking))
        self._command_thread.start()

    # コマンドの内部送信メソッド
    def _send_command(self, command, blocking=True): #ドローンにコマンドを送信,blocking=Trueなら応答を待つ
        is_acquired = self._command_semaphore.acquire(blocking=blocking)  # セマフォを取得、最大10秒待機
        if is_acquired:
            with contextlib.ExitStack() as stack:
                stack.callback(self._command_semaphore.release)
                logger.info({'action': 'send_command', 'command': command}) #ログにコマンド送信の情報を出力
                self.socket.sendto(command.encode('utf-8'), self.drone_address) #コマンドをドローンに送信
        else:  
            logger.warning({'action': 'send_command', 'command': command, 'status': 'not_acquired'}) #セマフォの取得に失敗した場合の警告ログ      

        # 応答を待つ（非同期、バックグラウンドスレッドが処理）
        time.sleep(1.5)  # 応答待機時間を延長
        if self.response:
            try:
                decoded = self.response.decode('utf-8').strip()
                logger.info({'action': 'command_response', 'response': decoded})
            except UnicodeDecodeError:
                try:
                    decoded = self.response.decode('latin-1').strip()
                    logger.info({'action': 'command_response', 'response': decoded, 'encoding': 'latin-1'})
                except:
                    logger.info({'action': 'command_response', 'raw_bytes': self.response.hex()})
        return self.response
    
    def takeoff(self):#ドローンの離陸
        # 事前にバッテリーをチェック
        self.send_command('battery?')
        time.sleep(1)
        if self.response:
            try:
                battery_level = int(self.response.decode('utf-8').strip())
                if battery_level < 20:
                    logger.warning(f"警告: バッテリー残量が少ないです ({battery_level}%)")
                    if battery_level < 10:
                        logger.error(f"エラー: バッテリー残量が危険レベルです ({battery_level}%)")
                        return False
                logger.info(f"バッテリー残量: {battery_level}%")
            except (UnicodeDecodeError, ValueError):
                logger.warning("バッテリー残量の確認に失敗しました")
        
        # 離陸コマンドを送信
        self.send_command('takeoff')
        return True

    def land(self): #ドローンの着陸
        self.send_command('land') #着陸コマンドを送信

    # ドローンの移動
    def move(self, direction, distance):
        distance = float(distance)
        if self.is_imperial:
            distance = int(round(distance * 30.48))  # フィートをcmに変換
        else:
            distance = int(round(distance * 100))  # メートルをcmに変換,小数点は四捨五入
        return self.send_command(f'{direction} {distance}') #上昇の時はdirectionに'up、distanceに 20'のように指定
        #f文字列リテラル、変数に文字列を埋め込むことができる

    def up(self, distance=DEFAULT_DISTANCE):
        return self.move('up', distance) #ドローンを上昇させる

    def down(self, distance=DEFAULT_DISTANCE):
        return self.move('down', distance) #ドローンを下降させる

    def left(self, distance=DEFAULT_DISTANCE):
        return self.move('left', distance) #ドローンを左に移動させる

    def right(self, distance=DEFAULT_DISTANCE):
        return self.move('right', distance) #ドローンを右に移動させる

    def forward(self, distance=DEFAULT_DISTANCE):
        return self.move('forward', distance) #ドローンを前進させる

    def back(self, distance=DEFAULT_DISTANCE):
        return self.move('back', distance) #ドローンを後退させる
    
    def enable_face_tracking(self):
        """顔追跡モードを有効にする"""
        self.is_face_tracking = True
        logger.info({'action': 'face_tracking', 'status': 'enabled'})
        return "Face tracking enabled"
    
    def disable_face_tracking(self):
        """顔追跡モードを無効にする"""
        self.is_face_tracking = False
        logger.info({'action': 'face_tracking', 'status': 'disabled'})
        return "Face tracking disabled"
    
    def toggle_face_tracking(self):
        """顔追跡モードを切り替える"""
        self.is_face_tracking = not self.is_face_tracking
        status = "enabled" if self.is_face_tracking else "disabled"
        logger.info({'action': 'face_tracking', 'status': status, 'toggled': True})
        return f"Face tracking {status}"
    
    def set_speed(self, speed):
        return self.send_command(f'speed {speed}') #ドローンの速度を設定

    def clockwise(self, degree=DEFAULT_DEGREE): #ドローンを時計回りに回転させる
        return self.send_command(f'cw {degree}')
    
    def counter_clockwise(self, degree=DEFAULT_DEGREE): #ドローンを反時計回りに回転させる
        return self.send_command(f'ccw {degree}')

    def flip(self, direction): #ドローンをフリップさせる
        if direction not in ['l', 'r', 'f', 'b']:
            logger.error("フリップの方向は 'l', 'r', 'f', 'b' のいずれかで指定してください")
            return None
        return self.send_command(f'flip {direction}')

    # パトロールモードを開始するメソッド
    def patrol(self):
        if not self.is_patrol:
            self.patrol_event = threading.Event() #パトロールイベントを新規作成
            self._thread_patrol = threading.Thread(target=self._patrol,args=(self._patrol_semaphore, self.patrol_event))
            self._thread_patrol.start() #パトロールモードのスレッドを開始
            self.is_patrol = True
            logger.info("パトロールモードを開始しました")
    
    # パトロールモードを停止するメソッド
    def stop_patrol(self):
        if self.is_patrol:
            self.patrol_event.set()
            retry = 0
            while self._thread_patrol.is_alive():
                time.sleep(0.3)
                if retry > 300:  # 最大90秒待機,0.3*300=90
                    break
                retry += 1
            self.is_patrol = False  # ここでFalseにするとwhileループに入らない
            logger.info("パトロールモードを停止しました")

    # パトロールモードの実行メソッド
    def _patrol(self, semaphore, stop_event):
            is_acquired = semaphore.acquire(blocking = False)  # セマフォを取得、最大1秒待機
            if is_acquired: #セマフォを取得できた場合
                logger.info({'action': 'patrol', 'status': 'acquired'})
                with contextlib.ExitStack() as stack: #コンテキストマネージャを使ってリソースを管理
                    stack.callback(semaphore.release) #セマフォの解放を登録
                    status = 0
                    while not stop_event.is_set():
                        status += 1
                        if status == 1:
                            self.up()
                        if status == 2:
                            self.clockwise()
                        if status == 3:
                            self.down()
                        if status == 4:
                            status = 0
                        time.sleep(5)  # 各動作の完了を待つ
            else:
                logger.warning({'action': 'patrol', 'status': 'not acquired'})

    # 映像受信スレッドの実行メソッド
    def _receive_video(self, stop_event, pip_in, host_ip, video_port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_video:
            sock_video.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ポートの再利用を許可
            sock_video.settimeout(0.5)  # タイムアウト0.5秒
            sock_video.bind((host_ip, video_port))
            data = bytearray(2048)  # 2048バイトのバッファを用意
            while not stop_event.is_set():
                try:
                    size, addr = sock_video.recvfrom_into(data)  # 映像データを受信
                    logger.info({'action': '_receive_video', 'data': data})
                except socket.timeout as ex:
                    logger.warning({'action': '_receive_video', 'ex': ex})
                    time.sleep(0.5)
                    continue
                except socket.error as ex:
                    logger.error({'action': '_receive_video', 'ex': ex})
                    break

                try:
                    pip_in.write(data[:size])  # ffmpegの標準入力に書き込む
                    pip_in.flush()  # バッファをフラッシュ
                except Exception as ex:
                    logger.error({'action': '_receive_video', 'ex': ex})
                    break

    # 映像をバイナリ形式で取得する
    def video_binary_generator(self):
        while True:
                try:
                    frame = self.proc_stdout.read(FRAME_SIZE)  # フレームサイズ分読み込む
                except Exception as ex:
                    logger.error({'action': 'video_binary_generator', 'ex': ex})
                    continue
                if not frame:
                    continue

                frame = np.frombuffer(frame, np.uint8).reshape(FRAME_Y, FRAME_X, 3)  # バイト列をNumPy配列に変換
                yield frame

    # 顔検出モードを有効にする/無効にするメソッド
    def enable_face_detect(self):
        """顔検出モードを有効にする"""
        if self.face_cascade is None or self.face_cascade.empty():
            logger.error("顔検出カスケードが利用できません。顔検出を有効にできません。")
            return False
        
        self._is_enable_face_detect = True
        logger.info("顔検出モードを有効にしました")
        return True

    def disable_face_detect(self):
        """顔検出モードを無効にする"""
        self._is_enable_face_detect = False
        logger.info("顔検出モードを無効にしました")

    # 映像をJPEG形式のバイナリで取得するジェネレータ,顔検出も行う,追跡機能付き
    def video_jpeg_generator(self):
        try:
            for frame in self.video_binary_generator():
                # フレームのコピーを作成して安全な処理を行う
                processed_frame = frame.copy()
                
                if self._is_enable_face_detect and self.face_cascade is not None and not self.face_cascade.empty():
                    try:
                        if self.is_patrol:
                            self.stop_patrol()

                        # 顔検出処理
                        gray = cv.cvtColor(processed_frame, cv.COLOR_BGR2GRAY)
                        faces = self.face_cascade.detectMultiScale(
                            gray, 
                            scaleFactor=1.1, 
                            minNeighbors=4, 
                            minSize=(30, 30),
                            flags=cv.CASCADE_SCALE_IMAGE
                        )
                        
                        # 検出された顔に矩形を描画
                        for (x, y, w, h) in faces:
                            cv.rectangle(processed_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 緑色の矩形で顔を囲む
                            # 顔の中心座標を計算（整数変換）
                            face_center_x = int(x + w/2)
                            face_center_y = int(y + h/2)
                            diff_x = FRAME_CENTER_X - face_center_x  # 顔の中心とフレームの中心の差分（X軸）
                            diff_y = FRAME_CENTER_Y - face_center_y  # 顔の中心とフレームの中心の差分（Y軸）
                            face_area = w * h # 顔の面積
                            percent_face = face_area / FRAME_AREA # 顔の面積の割合
                            drone_x, drone_y, drone_z, speed = 0, 0, 0, self.speed # ドローンの移動量と速度を初期化

                            # Telloドローンの座標系：
                            # X軸: 前進=+, 後退=-
                            # Y軸: 左=+, 右=-  
                            # Z軸: 上昇=+, 下降=-
                            
                            # 追跡の感度閾値を設定（素早く反応するように調整）
                            horizontal_threshold = 40   # 水平方向の反応閾値（ピクセル）- より敏感に
                            vertical_threshold = 30     # 垂直方向の反応閾値（ピクセル）- より敏感に
                            
                            # 水平方向の追跡（左右）- レスポンシブで正確な動き
                            if diff_x > horizontal_threshold:  # 顔が中心より左にある場合
                                drone_y = min(int(diff_x * 0.5), 40)  # 左に移動（Y軸プラス）- 係数と上限を上げて反応改善
                            elif diff_x < -horizontal_threshold:  # 顔が中心より右にある場合
                                drone_y = max(int(diff_x * 0.5), -40)  # 右に移動（Y軸マイナス）- 係数と上限を上げて反応改善
                            
                            # 垂直方向の追跡（上下）- レスポンシブで正確な動き（論理を修正）
                            if diff_y > vertical_threshold:  # 顔が中心より下にある場合
                                drone_z = min(int(abs(diff_y) * 0.4), 30)  # 上昇（Z軸プラス）- 顔を追って上昇
                            elif diff_y < -vertical_threshold:  # 顔が中心より上にある場合
                                drone_z = -min(int(abs(diff_y) * 0.4), 30)  # 下降（Z軸マイナス）- 顔を追って下降
                            
                            # 距離の調整（前後）- より控えめな調整
                            if percent_face > 0.3:  # 顔がフレームの30%以上を占めている場合
                                drone_x = -15  # ドローンを後退（X軸マイナス）- 移動量削減
                            elif percent_face < 0.1:  # 顔がフレームの10%未満を占めている場合
                                drone_x = 15   # ドローンを前進（X軸プラス）- 移動量削減

                            # ドローンの移動コマンドを送信（追跡モードが有効で、移動量がある場合のみ）
                            current_time = time.time()
                            if (self.is_face_tracking and 
                                (drone_x != 0 or drone_y != 0 or drone_z != 0) and
                                (current_time - self._last_tracking_time) > self._tracking_command_interval):
                                
                                # より高速で反応の良い移動のため速度を調整
                                smooth_speed = min(speed, 50)  # 最大速度を50cm/sに上げて反応を改善
                                self.send_command(f'go {drone_x} {drone_y} {drone_z} {smooth_speed}',
                                                    blocking=False) # 非同期でコマンド送信
                                self._last_tracking_time = current_time
                                
                                # デバッグ情報をログ出力
                                logger.info(f'Face tracking: center=({face_center_x},{face_center_y}), '
                                        f'diff=({diff_x},{diff_y}), '
                                        f'face%={percent_face:.3f}, '
                                        f'move=({drone_x},{drone_y},{drone_z})')
                            
                            # # 顔の中心に赤い点を描画
                            # cv.circle(processed_frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)  # 赤い点
                            
                            # フレーム中心の十字線を描画（デバッグ用）
                            center_x, center_y = int(FRAME_CENTER_X), int(FRAME_CENTER_Y)
                            cv.line(processed_frame, (center_x-10, center_y), (center_x+10, center_y), (255, 255, 0), 1)  # 水平線
                            cv.line(processed_frame, (center_x, center_y-10), (center_x, center_y+10), (255, 255, 0), 1)  # 垂直線
                            
                            break  # 最初の顔だけを処理
                            
                    except Exception as face_detect_error:
                        logger.error(f'Face detection error: {face_detect_error}')
                        # 顔検出エラーが発生してもストリーミングは継続

                # フレームをJPEGにエンコード
                _, jpeg = cv.imencode('.jpg', processed_frame)  # フレームをJPEGにエンコード
                jpeg_binary = jpeg.tobytes()  # バイト列に変換

                # スナップショットの保存
                if self.is_snapshot:
                    backup_file = time.strftime("%Y%m%d-%H%M%S") + '.jpg' # タイムスタンプ付きのファイル名
                    snapshot_file = 'snapshot.jpg'
                    for filename in (backup_file, snapshot_file):
                        filepath = os.path.join(SNAPSHOT_IMAGE_FOLDER, filename)
                        with open(filepath, 'wb') as f:
                            f.write(jpeg_binary)  # JPEGバイナリを書き込む
                        logger.info(f'Snapshot saved: {filepath}')
                    self.is_snapshot = False  # フラグをリセット
                yield jpeg_binary
                
        except Exception as e:
            logger.error(f'Video JPEG generator error: {e}')
            return
        
    # スナップショット撮影をリクエストするメソッド
    def snapshot(self):
        """スナップショット撮影をリクエストする"""
        self.is_snapshot = True
        retry = 0
        while retry < 3:
            if not self.is_snapshot:
                return True
            time.sleep(0.1)
            retry += 1
        return False

    
    # 映像フレームジェネレータ（server.pyで使用される）
    def video_frame_generator(self):
        """映像フレームのジェネレータ - server.pyからアクセスされる"""
        try:
            for jpeg_binary in self.video_jpeg_generator():
                yield jpeg_binary
        except Exception as ex:
            logger.error({'action': 'video_frame_generator', 'ex': ex})
            return
