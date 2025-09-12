#!/usr/bin/env python3
import logging
import socket
import sys
import threading
import time

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

class TestDroneManager(object):
    def __init__(self):
        print("初期化開始")
        self.stop_event = threading.Event()
        self._response_thread = threading.Thread(target=self.receive_response, args=(self.stop_event, ))
        self._response_thread.daemon = True
        self._response_thread.start()
        print("初期化完了")
        
    def receive_response(self, stop_event):
        while not stop_event.is_set():
            print("スレッド動作中...")
            time.sleep(1)
        print("スレッド終了")
        
    def stop(self):
        print("停止処理開始")
        if hasattr(self, 'stop_event'):
            self.stop_event.set()
        
        if hasattr(self, '_response_thread'):
            print("スレッドの終了を待機中...")
            self._response_thread.join(timeout=2)
            if self._response_thread.is_alive():
                print("スレッドの終了タイムアウト")
            else:
                print("スレッドが正常に終了")
        print("停止処理完了")

if __name__ == '__main__':
    print("=== プログラム開始 ===")
    manager = TestDroneManager()
    
    print("=== 3秒待機 ===")
    time.sleep(3)
    
    print("=== 停止処理開始 ===")
    manager.stop()
    
    print("=== プログラム終了 ===")
