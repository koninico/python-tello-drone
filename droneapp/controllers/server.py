import logging

from flask import jsonify
from flask import render_template
from flask import request
from flask import Response
from flask import redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

import droneapp.models.course
from droneapp.models.drone_manager import DroneManager # ドローン管理クラスをインポート
from droneapp.models.user import get_user, authenticate_user

import config

logger = logging.getLogger(__name__) #loggerオブジェクトを取得、他のモジュールからも利用できるようにする  
app = config.app  # Flaskアプリケーションのインスタンスを取得

# Flask-Loginの初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ドローンを操作するにはログインが必要です。'

@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)

# グローバルなドローンインスタンス（アプリ起動時に初期化）
drone_instance = DroneManager()

def get_drone():
    return drone_instance

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン機能"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """ログアウト機能"""
    logout_user()
    flash('ログアウトしました')
    return redirect(url_for('index'))

@app.route('/controller/')
@login_required
def controller():
    return render_template('controller.html')

# 顔追跡制御用の個別APIエンドポイント
@app.route('/face_tracking/enable', methods=['POST'])
@login_required
def enable_face_tracking():
    drone = get_drone()
    result = drone.enable_face_tracking()
    return jsonify(status='success', message=result), 200

@app.route('/face_tracking/disable', methods=['POST'])
@login_required
def disable_face_tracking():
    drone = get_drone()
    result = drone.disable_face_tracking()
    return jsonify(status='success', message=result), 200

@app.route('/face_tracking/toggle', methods=['POST'])
@login_required
def toggle_face_tracking():
    drone = get_drone()
    result = drone.toggle_face_tracking()
    return jsonify(status='success', message=result), 200

@app.route('/face_tracking/status', methods=['GET'])
@login_required
def face_tracking_status():
    drone = get_drone()
    status = "enabled" if drone.is_face_tracking else "disabled"
    return jsonify(status=status, is_tracking=drone.is_face_tracking), 200

# 基本操作用の個別APIエンドポイント（追跡中でも利用可能）
@app.route('/takeoff', methods=['POST'])
@login_required
def takeoff():
    drone = get_drone()
    drone.takeoff()
    return jsonify(status='success', message='Takeoff command sent'), 200

@app.route('/land', methods=['POST'])
@login_required
def land():
    drone = get_drone()
    drone.land()
    return jsonify(status='success', message='Land command sent'), 200

@app.route('/up', methods=['POST'])
@login_required
def up():
    drone = get_drone()
    drone.up()
    return jsonify(status='success', message='Up command sent'), 200

@app.route('/down', methods=['POST'])
@login_required
def down():
    drone = get_drone()
    drone.down()
    return jsonify(status='success', message='Down command sent'), 200

@app.route('/left', methods=['POST'])
@login_required
def left():
    drone = get_drone()
    drone.left()
    return jsonify(status='success', message='Left command sent'), 200

@app.route('/right', methods=['POST'])
@login_required
def right():
    drone = get_drone()
    drone.right()
    return jsonify(status='success', message='Right command sent'), 200

@app.route('/forward', methods=['POST'])
@login_required
def forward():
    drone = get_drone()
    drone.forward()
    return jsonify(status='success', message='Forward command sent'), 200

@app.route('/back', methods=['POST'])
@login_required
def back():
    drone = get_drone()
    drone.back()
    return jsonify(status='success', message='Back command sent'), 200

# コマンドを受け取るAPIエンドポイント
@app.route('/api/command/', methods=['POST'])
@login_required
def command():
    cmd = request.form.get('command')
    logger.info({'action': 'command', 'cmd': cmd})
    drone = get_drone()
    if cmd == 'takeoff':
        drone.takeoff()
    if cmd == 'land':
        drone.land()
    if cmd == 'speed':
        speed = request.form.get('speed')
        logger.info({'action': 'command', 'cmd': cmd, 'speed': speed})
        if speed:
            drone.set_speed(int(speed))
    if cmd == 'up':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.up() # up
    if cmd == 'down':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.down()  # down
    if cmd == 'left':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.left() # left
    if cmd == 'right':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.right()   # right
    if cmd == 'forward':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.forward() # forward
    if cmd == 'back':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.back() # back
    if cmd == 'clockwise':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.clockwise() # clockwise
    if cmd == 'counter_clockwise':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.counter_clockwise() # counter clockwise
    if cmd == 'flipFront':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.flip('f')  # forward flip
    if cmd == 'flipBack':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.flip('b')  # back flip
    if cmd == 'flipLeft':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.flip('l')  # left flip
    if cmd == 'flipRight':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.flip('r')  # right flip
    if cmd == 'patrol':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.patrol()  # パトロールモード開始
    if cmd == 'stopPatrol':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.stop_patrol()  # パトロールモード停止
    if cmd == 'faceDetectAndTrack':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.enable_face_detect()  # 顔検出モード有効化
    if cmd == 'stopFaceDetectAndTrack':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.disable_face_detect()  # 顔検出モード無効化
    if cmd == 'enableFaceTracking':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.enable_face_tracking()  # 顔追跡モード有効化
    if cmd == 'disableFaceTracking':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.disable_face_tracking()  # 顔追跡モード無効化
    if cmd == 'toggleFaceTracking':
        logger.info({'action': 'command', 'cmd': cmd})
        drone.toggle_face_tracking()  # 顔追跡モード切り替え
    if cmd == 'snapshot':
        if drone.snapshot():
            return jsonify(status='success'), 200
        else:
            return jsonify(status='fail'), 400

    return jsonify(status='success'), 200

# 映像ストリーミング用画像を生成するジェネレーター関数
def video_generator():
    drone = get_drone()
    for jpeg in drone.video_frame_generator():
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n\r\n')

# 映像ストリーミングのためのエンドポイント
@app.route('/video/streaming')
def video_feed():
    return Response(video_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run():
    app.run(host=config.WEB_ADDRESS, port=config.WEB_PORT, threaded=True)

def get_courses(course_id=None):
    drone = get_drone()
    courses = droneapp.models.course.get_courses(drone)
    if course_id:
        return courses.get(course_id)
    return courses

@app.route('/games/shake/')
@login_required
def game_shake():
    courses = get_courses()
    return render_template('games/shake.html', courses=courses)

@app.route('/games/shake/start', methods=['GET', 'POST'])
@login_required
def shake_start():
    # course_id = request.args.get('id')
    course_id = request.form.get('id')
    course = get_courses(int(course_id))
    course.start()
    return jsonify(result='started'), 200

@app.route('/games/shake/run', methods=['GET', 'POST'])
@login_required
def shake_run():
    # course_id = request.args.get('id')
    course_id = request.form.get('id')
    course = get_courses(int(course_id))
    course.run()
    return jsonify(
        elapsed=course.elapsed,
        status=course.status,
        running=course.is_running
    ), 200
