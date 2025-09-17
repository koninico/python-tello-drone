#!/usr/bin/env python3
import socket
import time

def test_tello_connection():
    # ドローンとの通信をテスト
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    try:
        # ローカルポートにバインド
        sock.bind(('0.0.0.0', 8889))
        print("ポート8889にバインド成功")
        
        # ドローンにcommandを送信
        drone_address = ('192.168.10.1', 8889)
        message = b'command'
        
        print(f"ドローン {drone_address} に '{message.decode()}' を送信中...")
        sock.sendto(message, drone_address)
        
        # 応答を待機
        print("応答を待機中...")
        try:
            response, address = sock.recvfrom(1024)
            print(f"応答受信: {response.decode()} from {address}")
            return True
        except socket.timeout:
            print("タイムアウト: ドローンからの応答がありません")
            return False
            
    except Exception as e:
        print(f"エラー: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    print("=== Tello接続テスト ===")
    success = test_tello_connection()
    if success:
        print("✅ ドローンとの通信成功")
    else:
        print("❌ ドローンとの通信失敗")