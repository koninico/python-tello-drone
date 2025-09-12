class Singleton(type):
    
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:  # 一番初めにインスタンス化されたときだけ
            print('call')
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs) # インスタンスを生成して上に保存
        return cls._instances[cls]
    
class T(metaclass=Singleton): 
    #シングルトンを入れることで、上のコードが実行される。何度呼び出しても一番初めに作ったものが呼び出される
#class T(object):
    def __init__(self):
        print('init')

test = T()
test = T() #一番初めに作ったものが呼び出される
test = T()
test = T()
test = T()
