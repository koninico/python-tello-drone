#!/usr/bin/env python3
import socket
import time

def test_with_different_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    
    try:
        # 異なるローカルポートを使用
        sock.bind(('0.0.0.0', 9999))  # ポート9999を使用
        tello_address = ('192.168.10.1', 8889)
        
        print("異なるポートでテスト中...")
        sock.sendto('command'.encode('utf-8'), tello_address)
        
        response, addr = sock.recvfrom(1024)
        print(f"成功! 応答: {response.decode('utf-8')} from {addr}")
        
        # バッテリーチェック
        sock.sendto('battery?'.encode('utf-8'), tello_address)
        response, addr = sock.recvfrom(1024)
        print(f"バッテリー: {response.decode('utf-8')}%")
        
    except socket.timeout:
        print("タイムアウト: ドローンからの応答なし")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_with_different_port()
