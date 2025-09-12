import logging #ログ出力用
import contextlib #コンテキストマネージャ用
import socket #ソケット通信
import sys #システム関連
import threading #スレッド関連
import time #時間関連



logging.basicConfig(level=logging.INFO, stream=sys.stdout) #ログの基本設定、コンソールにログを出力
logger = logging.getLogger(__name__) #loggerオブジェクトを取得、他のモジュールからも利用できるようにする

DEFAULT_DISTANCE = 0.30  # m (30cm)
DEFAULT_SPEED = 10  # cm/s
DEFAULT_DEGREE = 10  # 回転角度度数
DEFAULT_TIMEOUT = 5  # フリップ

class DroneManager(object):
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

    def send_command(self, command): #ドローンにコマンドを送信
        logger.info({'action': 'send_command', 'command': command}) #ログにコマンド送信の情報を出力
        self.socket.sendto(command.encode('utf-8'), self.drone_address) #コマンドをドローンに送信
        
        # 応答を待つ（タイムアウト1秒）
        time.sleep(1)
        if self.response:
            try:
                decoded = self.response.decode('utf-8')
                logger.info({'action': 'command_response', 'response': decoded})
            except UnicodeDecodeError:
                try:
                    decoded = self.response.decode('latin-1')
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
                battery_level = int(self.response.decode('utf-8'))
                if battery_level < 20:
                    logger.warning(f"警告: バッテリー残量が少ないです ({battery_level}%)")
                    if battery_level < 10:
                        logger.error(f"エラー: バッテリー残量が危険レベルです ({battery_level}%)")
                        return False
                logger.info(f"バッテリー残量: {battery_level}%")
            except (UnicodeDecodeError, ValueError):
                logger.warning("バッテリー残量の確認に失敗しました")
        
        self.send_command('takeoff')  #離陸コマンドを送信
        return True

    def land(self): #ドローンの着陸
        self.send_command('land') #着陸コマンドを送信

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

if __name__ == '__main__': #このファイルが直接実行された場合にのみ以下のコードを実行
    drone_manager = DroneManager() #DroneManagerのインスタンスを作成
    time.sleep(3)  # 初期化完了を待つ

    print("離陸開始...")
    drone_manager.takeoff() #ドローンの離陸
    time.sleep(10)  # 離陸完了を待つ

    print("パトロールモード開始...")
    drone_manager.patrol()  # パトロールモード開始
    time.sleep(45)  # 45秒間パトロールモードを実行

    drone_manager.stop_patrol()  # パトロールモード停止
    time.sleep(5)  # パトロールモード停止完了を待

    # print("フリップ開始...")
    # drone_manager.flip('f')  # 前方にフリップ
    # time.sleep(5)  # フリップ完了を待つ
    # drone_manager.flip('b')  # 後方にフリップ
    # time.sleep(5)  # フリップ完了を待つ

    # print("ドローンを時計回りに回転させる...")
    # drone_manager.clockwise(90)  # ドローンを時計回りに回転させる
    # time.sleep(5)  # 回転完了を待つ

    # print("ドローンを反時計回りに回転させる...")
    # drone_manager.counter_clockwise(90)  # ドローンを反時計回りに回転させる
    # time.sleep(5)  # 回転完了を待つ

    # print("前進開始...")
    # drone_manager.forward() #ドローンを前進させる
    # time.sleep(5)  # 前進完了を待つ

    # print("右移動開始...")
    # drone_manager.right() #ドローンを右に移動させる
    # time.sleep(5)  # 右移動完了を待つ

    # print("後退開始...")
    # drone_manager.back() #ドローンを後退させる
    # time.sleep(5)  # 後退完了を待つ

    # print("左移動開始...")
    # drone_manager.left() #ドローンを左に移動させる
    # time.sleep(5)  # 左移動完了を待つ

    # print("速度を10cm/sに設定...")
    # drone_manager.set_speed(10)  # ドローンの速度を10cm/sに設定
    # time.sleep(2)  # 設定完了を待つ

    # print("上昇開始...")
    # drone_manager.up() #ドローンを上昇させる
    # time.sleep(5)  # 上昇完了を待つ 

    # print("下降開始...")
    # drone_manager.down() #ドローンを下降させる
    # time.sleep(5)  # 下降完了を待つ 

    print("着陸開始...")
    drone_manager.land() #ドローンの着陸
    time.sleep(3)  # 着陸完了を待つ
    
    print("プログラム終了処理中...")
    drone_manager.stop() #ドローンの停止
    time.sleep(1)  # 終了処理の完了を待つ
    print("プログラム終了")
