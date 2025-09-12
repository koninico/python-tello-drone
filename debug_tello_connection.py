#!/usr/bin/env python3
"""
文字化け問題に対応したTello接続テスト
"""
import socket
import time

def test_tello_with_encoding_fix():
    print("Telloドローンの接続をテストします（文字化け対応版）...")
    
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
            print(f"📦 受信した生データ: {response}")
            print(f"📦 16進数表示: {response.hex()}")
            
            # 複数の方法でデコードを試す
            decoded = None
            encoding_used = None
            
            # UTF-8でデコード
            try:
                decoded = response.decode('utf-8')
                encoding_used = 'utf-8'
                print(f"✓ UTF-8デコード成功: '{decoded}' from {addr}")
            except UnicodeDecodeError:
                print("❌ UTF-8デコードに失敗")
                
                # latin-1でデコード
                try:
                    decoded = response.decode('latin-1')
                    encoding_used = 'latin-1'
                    print(f"✓ latin-1デコード成功: '{decoded}' from {addr}")
                except UnicodeDecodeError:
                    print("❌ latin-1デコードに失敗")
                    
                    # ascii でデコード
                    try:
                        decoded = response.decode('ascii', errors='ignore')
                        encoding_used = 'ascii (errors ignored)'
                        print(f"⚠️  ASCIIデコード（エラー無視）: '{decoded}' from {addr}")
                    except:
                        print("❌ すべてのデコード方法が失敗")
                        # バイト単位で確認
                        print("🔍 バイト詳細:")
                        for i, byte in enumerate(response):
                            print(f"  位置{i}: {byte} ({chr(byte) if 32 <= byte <= 126 else '非表示文字'})")
            
            if decoded and decoded.strip().lower() == 'ok':
                print("🎉 Telloとの接続に成功しました！")
                
                # バッテリー状態を確認
                print("\n→ バッテリー状態を確認中...")
                sock.sendto('battery?'.encode('utf-8'), tello_address)
                battery_response, _ = sock.recvfrom(1024)
                print(f"📦 バッテリー応答データ: {battery_response}")
                print(f"📦 バッテリー応答16進数: {battery_response.hex()}")
                
                try:
                    battery_level = battery_response.decode('utf-8').strip()
                    print(f"🔋 バッテリー残量: {battery_level}%")
                except UnicodeDecodeError:
                    try:
                        battery_level = battery_response.decode('latin-1').strip()
                        print(f"🔋 バッテリー残量（latin-1）: {battery_level}%")
                    except:
                        print(f"❌ バッテリー情報のデコードに失敗: {battery_response}")
                
                return True
            else:
                print(f"⚠️  予期しない応答: {decoded} (エンコーディング: {encoding_used})")
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
    success = test_tello_with_encoding_fix()
    
    if not success:
        print("\n📝 トラブルシューティング:")
        print("1. Telloドローンの電源を一度オフにして再起動")
        print("2. MacのWiFi設定でTELLO-XXXXXXネットワークを削除して再接続") 
        print("3. Telloを初期化（電源ボタンを10秒長押し）")
        print("4. 再度このテストを実行")
