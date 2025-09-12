#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from drone_manager import DroneManager
import time

def test_patrol():
    print("パトロールテスト開始...")
    drone_manager = DroneManager()
    time.sleep(3)
    
    print("離陸開始...")
    drone_manager.takeoff()
    time.sleep(5)
    
    print("パトロールモード開始（10秒）...")
    drone_manager.patrol()
    time.sleep(10)  # 10秒間のみパトロール
    
    print("パトロールモード停止...")
    drone_manager.stop_patrol()
    time.sleep(2)
    
    print("着陸開始...")
    drone_manager.land()
    time.sleep(3)
    
    print("プログラム終了処理中...")
    drone_manager.stop()
    print("テスト完了")

if __name__ == '__main__':
    test_patrol()
