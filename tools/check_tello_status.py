#!/usr/bin/env python3
import socket
import time

def check_tello_status():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    
    try:
        sock.bind(('0.0.0.0', 0))
        tello_address = ('192.168.10.1', 8889)
        
        # 基本的な状態チェック
        commands = [
            'command',      # SDKモード開始
            'battery?',     # バッテリー残量
            'speed?',       # 現在の速度
            'time?',        # 飛行時間
            'height?',      # 現在の高度
            'temp?',        # 温度
            'attitude?',    # 姿勢情報
        ]
        
        for cmd in commands:
            print(f"送信: {cmd}")
            sock.sendto(cmd.encode('utf-8'), tello_address)
            
            try:
                response, addr = sock.recvfrom(1024)
                decoded = response.decode('utf-8')
                print(f"応答: {decoded}")
                
                # 特定の応答をチェック
                if cmd == 'battery?' and decoded.isdigit():
                    battery = int(decoded)
                    if battery < 10:
                        print(f"⚠️  警告: バッテリー残量が少ない ({battery}%)")
                    elif battery < 20:
                        print(f"⚠️  注意: バッテリー残量 ({battery}%)")
                    else:
                        print(f"✅ バッテリー残量: {battery}%")
                        
                elif cmd == 'height?' and decoded.isdigit():
                    height = int(decoded)
                    if height == 0:
                        print("✅ ドローンは地上にいます")
                    else:
                        print(f"⚠️  ドローンは高度 {height}cm で浮遊中")
                        
            except socket.timeout:
                print(f"タイムアウト: {cmd} への応答なし")
            except Exception as e:
                print(f"エラー: {e}")
                
            time.sleep(1)
            
    finally:
        sock.close()

if __name__ == "__main__":
    check_tello_status()
