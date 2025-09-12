#!/usr/bin/env python3
import socket
import time

def test_movement_commands():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    
    try:
        sock.bind(('0.0.0.0', 9998))
        tello_address = ('192.168.10.1', 8889)
        
        def send_and_wait(command):
            print(f"送信: {command}")
            sock.sendto(command.encode('utf-8'), tello_address)
            try:
                response, addr = sock.recvfrom(1024)
                decoded = response.decode('utf-8')
                print(f"応答: {decoded}")
                return decoded
            except socket.timeout:
                print("タイムアウト")
                return None
        
        # 基本コマンド
        send_and_wait('command')
        time.sleep(1)
        
        # バッテリーチェック
        battery = send_and_wait('battery?')
        if battery and int(battery) < 20:
            print(f"警告: バッテリー残量 {battery}%")
        
        # 離陸
        print("\n=== 離陸テスト ===")
        send_and_wait('takeoff')
        time.sleep(5)
        
        # 移動テスト（小さな距離で）
        movements = [
            ('forward 20', '前進 20cm'),
            ('back 20', '後退 20cm'),
            ('right 20', '右移動 20cm'),
            ('left 20', '左移動 20cm'),
            ('up 20', '上昇 20cm'),
            ('down 20', '下降 20cm'),
        ]
        
        print("\n=== 移動テスト ===")
        for command, description in movements:
            print(f"\n{description}")
            response = send_and_wait(command)
            if response == 'ok':
                print("✅ 成功")
            else:
                print(f"❌ 失敗: {response}")
            time.sleep(2)
        
        # 着陸
        print("\n=== 着陸 ===")
        send_and_wait('land')
        
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_movement_commands()
