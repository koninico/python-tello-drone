#!/usr/bin/env python3
import socket
import time

def simple_flight_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    
    try:
        sock.bind(('0.0.0.0', 9997))
        tello_address = ('192.168.10.1', 8889)
        
        def send_and_check(command, description):
            print(f"\n{description}")
            print(f"送信: {command}")
            sock.sendto(command.encode('utf-8'), tello_address)
            
            try:
                response, addr = sock.recvfrom(1024)
                decoded = response.decode('utf-8')
                print(f"応答: {decoded}")
                
                if decoded == 'ok':
                    print("✅ 成功")
                    return True
                elif 'error' in decoded.lower():
                    print(f"❌ エラー: {decoded}")
                    return False
                else:
                    print(f"ℹ️  情報: {decoded}")
                    return True
                    
            except socket.timeout:
                print("❌ タイムアウト")
                return False
        
        # テスト実行
        print("=== Tello飛行テスト開始 ===")
        
        if not send_and_check('command', '1. SDKモード開始'):
            return
        time.sleep(2)
        
        send_and_check('battery?', '2. バッテリーチェック')
        time.sleep(1)
        
        if not send_and_check('takeoff', '3. 離陸'):
            return
        time.sleep(5)
        
        print("\n=== 移動テスト ===")
        movements = [
            ('forward 20', '前進 20cm'),
            ('right 20', '右移動 20cm'),
            ('back 20', '後退 20cm'),
            ('left 20', '左移動 20cm'),
            ('up 20', '上昇 20cm'),
            ('down 20', '下降 20cm'),
        ]
        
        for command, desc in movements:
            if send_and_check(command, desc):
                time.sleep(3)  # 各動作の完了を待つ
            else:
                print("移動コマンドでエラーが発生しました")
                break
        
        send_and_check('land', '着陸')
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    simple_flight_test()
