import logging
import sys

import config #LOG_FILEを取得するために必要

import droneapp.controllers.server

logging.basicConfig(
    level=logging.INFO, 
    stream=sys.stdout
    #filename=config.LOG_FILE ・・ログをファイルに出力する場合はコメントアウトを外す
) #ログの基本設定、コンソールにログを出力

if __name__ == '__main__':
    logging.info("Webサーバーを起動します")
    droneapp.controllers.server.run()  # Webサーバーを起動