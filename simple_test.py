#!/usr/bin/env python3
import socket
import time

def simple_tello_test():
    """最もシンプルなTelloテスト"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    try:
        # ローカルポートにバインド
        sock.bind(('', 8891))  # 空文字列は0.0.0.0と同じ
        
        drone_ip = '192.168.10.1'
        drone_port = 8889
        
        print(f"ドローン {drone_ip}:{drone_port} に接続テスト中...")
        
        # 最初にcommandを送信
        message = 'command'
        print(f"送信: {message}")
        sock.sendto(message.encode(), (drone_ip, drone_port))
        
        # 応答を待機
        try:
            data, server = sock.recvfrom(1024)
            response = data.decode()
            print(f"受信: '{response}' from {server}")
            
            if response.strip() == 'ok':
                print("✅ ドローンはSDKモードに入りました!")
                return True
            else:
                print(f"⚠️  予期しない応答: {response}")
                return False
                
        except socket.timeout:
            print("❌ タイムアウト - ドローンからの応答がありません")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    print("=== 最もシンプルなTelloテスト ===")
    success = simple_tello_test()
    if not success:
        print("\n🔍 確認事項:")
        print("1. ドローンの電源が入っているか")
        print("2. MacがドローンのWi-Fi (TELLO-xxxxxx) に接続されているか")
        print("3. ドローンのIPアドレスが 192.168.10.1 か")