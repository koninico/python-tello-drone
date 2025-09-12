#!/usr/bin/env python3
import socket
import time

def test_tello_connection():
    # ソケットを作成
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(30)
    
    try:
        # 任意のポートにバインド
        sock.bind(('0.0.0.0', 0))
        print(f"ローカルアドレス: {sock.getsockname()}")
        
        # Telloにcommandを送信
        tello_address = ('192.168.10.1', 8889)
        message = 'command'
        print(f"Telloに送信: {message}")
        sock.sendto(message.encode('utf-8'), tello_address)
        
        # 応答を待機
        print("応答を待機中...")
        response, addr = sock.recvfrom(1024)
        print(f"Telloからの応答: {response} from {addr}")
        try:
            decoded_response = response.decode('utf-8')
            print(f"デコード済み応答: {decoded_response}")
        except UnicodeDecodeError:
            print(f"バイナリ応答: {response.hex()}")
            # 他のエンコーディングを試す
            for encoding in ['ascii', 'latin-1']:
                try:
                    decoded = response.decode(encoding)
                    print(f"{encoding}でデコード: {decoded}")
                    break
                except:
                    continue
        
        # バッテリー情報を取得
        message = 'battery?'
        print(f"Telloに送信: {message}")
        sock.sendto(message.encode('utf-8'), tello_address)
        response, addr = sock.recvfrom(1024)
        print(f"バッテリー残量: {response.decode('utf-8')}%")
        
    except socket.timeout:
        print("タイムアウト: Telloからの応答がありません")
        print("確認事項:")
        print("1. Telloの電源が入っているか")
        print("2. WiFiでTello-XXXXXXに接続されているか")
        print("3. IPアドレス192.168.10.1が正しいか")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_tello_connection()
