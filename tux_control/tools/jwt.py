try:
    from granad.tools.jwt_3 import jwt_required as jwt_required_3
    version_3_loaded = True
except ImportError:
    version_3_loaded = False

try:
    from granad.tools.jwt_4 import jwt_required as jwt_required_4
    version_4_loaded = True
except ImportError:
    version_4_loaded = False

from flask_jwt_extended import __version__


def jwt_required(*args, **kwargs):
    if __version__.startswith('3.') and version_3_loaded:
        # This is version 3
        return jwt_required_3(*args, **kwargs)
    elif __version__.startswith('4.') and version_4_loaded:
        # This is version 4 or better (hope)
        return jwt_required_4(*args, **kwargs)
    else:
        raise Exception('Unsupported version of flask_jwt_extended=={}'.format(__version__))

