#!/usr/bin/env python3
import socket
import time

def test_tello_direct():
    """ドローンとの直接通信をテスト"""
    
    # 既存のアプリケーションが使用中なので、別のポートを使用
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10.0)
    
    try:
        # 別のローカルポートにバインド
        sock.bind(('0.0.0.0', 8890))
        print("ポート8890にバインド成功")
        
        drone_address = ('192.168.10.1', 8889)
        
        # 1. commandコマンドでSDKモードを有効化
        print("1. SDKモード有効化中...")
        sock.sendto(b'command', drone_address)
        
        try:
            response, addr = sock.recvfrom(1024)
            print(f"SDKモード応答: {response.decode()} from {addr}")
        except socket.timeout:
            print("⚠️  SDKモード: タイムアウト")
            
        time.sleep(2)
        
        # 2. バッテリー確認
        print("2. バッテリー確認中...")
        sock.sendto(b'battery?', drone_address)
        
        try:
            response, addr = sock.recvfrom(1024)
            print(f"バッテリー応答: {response.decode()} from {addr}")
        except socket.timeout:
            print("⚠️  バッテリー: タイムアウト")
            
        time.sleep(1)
        
        # 3. takeoffテスト
        print("3. takeoffテスト中...")
        sock.sendto(b'takeoff', drone_address)
        
        try:
            response, addr = sock.recvfrom(1024)
            print(f"takeoff応答: {response.decode()} from {addr}")
            print("✅ takeoff成功！")
        except socket.timeout:
            print("❌ takeoff: タイムアウト")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    print("=== Tello直接通信テスト ===")
    test_tello_direct()