#!/usr/bin/env python3
"""
Telloドローンの接続テスト用スクリプト
"""
import socket
import time

def test_tello_connection():
    print("Telloドローンの接続をテストします...")
    
    # ソケットを作成
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    try:
        # ローカルの8889ポートにバインド
        sock.bind(('', 8889))
        print("✓ ローカルソケット8889に正常にバインドしました")
        
        # Telloにcommandを送信してSDKモードを開始
        tello_address = ('192.168.10.1', 8889)
        command = 'command'
        
        print(f"→ Telloに '{command}' を送信中...")
        sock.sendto(command.encode('utf-8'), tello_address)
        
        # レスポンス待機
        try:
            response, addr = sock.recvfrom(1024)
            response_str = response.decode('utf-8')
            print(f"✓ Telloからの応答: '{response_str}' from {addr}")
            
            if response_str.strip().lower() == 'ok':
                print("🎉 Telloとの接続に成功しました！")
                
                # バッテリー状態を確認
                print("\n→ バッテリー状態を確認中...")
                sock.sendto('battery?'.encode('utf-8'), tello_address)
                battery_response, _ = sock.recvfrom(1024)
                battery_level = battery_response.decode('utf-8').strip()
                print(f"🔋 バッテリー残量: {battery_level}%")
                
                return True
            else:
                print(f"⚠️  予期しない応答: {response_str}")
                return False
                
        except socket.timeout:
            print("❌ タイムアウト: Telloからの応答がありません")
            print("   - Telloの電源が入っていることを確認してください")
            print("   - TelloのWiFiネットワーク（TELLO-XXXXXX）に接続してください")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
        
    finally:
        sock.close()

if __name__ == '__main__':
    success = test_tello_connection()
    
    if not success:
        print("\n📝 トラブルシューティング:")
        print("1. Telloドローンの電源を確認")
        print("2. MacのWiFi設定でTELLO-XXXXXXネットワークに接続")
        print("3. 192.168.10.1にpingが通るか確認: ping 192.168.10.1")
        print("4. 再度このテストを実行")
