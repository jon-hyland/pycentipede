"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from threading import Thread
from time import sleep
from service import config
from service import di
from service import app
from service import routes


with open("version") as f:
    version = f.read().strip()
config.version = version
print(f" * Starting Centipede v{version}")


def http_server_thread():
    app.run(debug=False, port=config.dev_listen_port)


if __name__ == "__main__":
    print(" * Starting HTTP listener..")
    thread = Thread(target=http_server_thread)
    thread.start()


def initialize():
    if __name__ == "__main__":
        sleep(1.5)
    print(" * Initializing word splitter..")
    di.service_state.set_loading_data_state()
    di.dictionary.load_data(config.data_file)
    di.service_state.set_up_state()
    print(" * Service initialization complete!")


initialize()
