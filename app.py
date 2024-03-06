from threading import Lock
from wsgiref.util import shift_path_info
import waitress
import importlib
import os

class PathDispatcher(object):
    def __init__(self, default_app, create_app):
        self.default_app = default_app
        self.create_app = create_app
        self.lock = Lock()
        self.instances = {}

    def get_application(self, prefix):
        with self.lock:
            app = self.instances.get(prefix)
            if app is None:
                app = self.create_app(prefix)
                if app is not None:
                    self.instances[prefix] = app
            return app

    def __call__(self, environ, start_response):
        prefix = shift_path_info(environ)
        app = self.get_application(prefix)
        if app is None:
            app = self.default_app
        return app(environ, start_response)

def make_app(prefix):
    try:
        module = importlib.import_module(prefix)
        if not hasattr(module, "app"):
            return None
        app = module.app
        app.URLBASE = "/" + prefix
        return app
    except ModuleNotFoundError as e:
        return None
    except Exception as e:
        raise e    

def NotFound(environ, start_response):
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"not found"]

app = PathDispatcher(NotFound, make_app)
if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=5000)

