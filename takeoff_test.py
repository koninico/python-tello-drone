#!/usr/bin/env python3
import socket
import time

def tello_takeoff_test():
    """Tello takeoffテスト"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10.0)  # takeoffは時間がかかるので長めに設定
    
    try:
        sock.bind(('', 8892))
        drone_ip = '192.168.10.1'
        drone_port = 8889
        
        print("=== Tello takeoffテスト ===")
        
        # 1. SDKモード有効化
        print("1. SDKモード有効化中...")
        sock.sendto('command'.encode(), (drone_ip, drone_port))
        data, server = sock.recvfrom(1024)
        print(f"   応答: {data.decode()}")
        time.sleep(2)
        
        # 2. バッテリー確認
        print("2. バッテリー確認中...")
        sock.sendto('battery?'.encode(), (drone_ip, drone_port))
        data, server = sock.recvfrom(1024)
        battery = data.decode()
        print(f"   バッテリー: {battery}%")
        time.sleep(1)
        
        # 3. takeoffテスト
        print("3. takeoff実行中...")
        print("   ⚠️  ドローンを手に持ってください！")
        time.sleep(3)  # 準備時間
        
        sock.sendto('takeoff'.encode(), (drone_ip, drone_port))
        data, server = sock.recvfrom(1024)
        response = data.decode()
        print(f"   takeoff応答: {response}")
        
        if response.strip() == 'ok':
            print("✅ takeoff成功！プロペラが回転しているはずです")
            
            # 安全のため即座に着陸
            time.sleep(3)
            print("4. 安全のため着陸中...")
            sock.sendto('land'.encode(), (drone_ip, drone_port))
            data, server = sock.recvfrom(1024)
            print(f"   land応答: {data.decode()}")
            print("✅ 着陸完了")
        else:
            print(f"⚠️  予期しない応答: {response}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    tello_takeoff_test()