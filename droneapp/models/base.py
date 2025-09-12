class Singleton(type):
    
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:  # 一番初めにインスタンス化されたときだけ
            print('call')
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs) # インスタンスを生成して上に保存
        return cls._instances[cls]