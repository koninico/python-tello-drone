from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin):
    """認証用のユーザークラス"""
    
    def __init__(self, id, username, password_hash=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        """パスワードの確認"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def generate_password_hash(password):
        """パスワードハッシュの生成"""
        return generate_password_hash(password)

# ユーザーデータベース（本番環境では実際のデータベースを使用することを推奨）
# 注意: 本番環境では環境変数やセキュアな設定ファイルからパスワードを読み込むこと
USERS = {
    '1': User('1', 'admin', User.generate_password_hash('DroneSecure2024!'))
}

def get_user(user_id):
    """ユーザーIDからユーザーオブジェクトを取得"""
    return USERS.get(user_id)

def authenticate_user(username, password):
    """ユーザー認証"""
    for user in USERS.values():
        if user.username == username and user.check_password(password):
            return user
    return None