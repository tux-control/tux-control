"""
This is flask-jwt-extended version 3 implementation of custom resolver
"""


from functools import wraps
from flask import request, current_app
from werkzeug.exceptions import BadRequest
from flask_jwt_extended.config import config
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended.view_decorators import _load_user, _decode_jwt_from_cookies, _decode_jwt_from_query_string, _decode_jwt_from_headers
from flask_jwt_extended.utils import (
    decode_token, verify_token_claims,
    verify_token_not_blacklisted, verify_token_type
)

try:
    from flask import _app_ctx_stack as ctx_stack
except ImportError:  # pragma: no cover
    from flask import _request_ctx_stack as ctx_stack


def _decode_jwt_from_json(request_type):
    if not request.event:
        raise NoAuthorizationError('Invalid content-type. Must have event.')

    if request_type == 'access':
        token_key = config.json_key
    else:
        token_key = config.refresh_json_key

    try:
        encoded_token = request.event.get('args')[0].get(token_key, None)
        if not encoded_token:
            raise BadRequest()
    except BadRequest:
        raise NoAuthorizationError('Missing "{}" key in json data.'.format(token_key))

    return encoded_token, None


def _decode_jwt_from_request(request_type):
    # All the places we can get a JWT from in this request
    get_encoded_token_functions = []
    if config.jwt_in_cookies:
        get_encoded_token_functions.append(lambda: _decode_jwt_from_cookies(request_type))
    if config.jwt_in_query_string:
        get_encoded_token_functions.append(_decode_jwt_from_query_string)
    if config.jwt_in_headers:
        get_encoded_token_functions.append(_decode_jwt_from_headers)
    if config.jwt_in_json:
        get_encoded_token_functions.append(lambda: _decode_jwt_from_json(request_type))

    # Try to find the token from one of these locations. It only needs to exist
    # in one place to be valid (not every location).
    errors = []
    decoded_token = None
    for get_encoded_token_function in get_encoded_token_functions:
        try:
            encoded_token, csrf_token = get_encoded_token_function()
            decoded_token = decode_token(encoded_token, csrf_token)
            break
        except NoAuthorizationError as e:
            errors.append(str(e))

    # Do some work to make a helpful and human readable error message if no
    # token was found in any of the expected locations.
    if not decoded_token:
        token_locations = config.token_location
        multiple_jwt_locations = len(token_locations) != 1

        if multiple_jwt_locations:
            err_msg = "Missing JWT in {start_locs} or {end_locs} ({details})".format(
                start_locs=", ".join(token_locations[:-1]),
                end_locs=token_locations[-1],
                details="; ".join(errors)
            )
            raise NoAuthorizationError(err_msg)
        else:
            raise NoAuthorizationError(errors[0])

    verify_token_type(decoded_token, expected_type=request_type)
    verify_token_not_blacklisted(decoded_token, request_type)
    return decoded_token


def verify_jwt_in_request():
    """
    Ensure that the requester has a valid access token. This does not check the
    freshness of the access token. Raises an appropiate exception there is
    no token or if the token is invalid.
    """
    if request.method not in config.exempt_methods:
        jwt_data = _decode_jwt_from_request(request_type='access')
        ctx_stack.top.jwt = jwt_data
        verify_token_claims(jwt_data)
        _load_user(jwt_data[config.identity_claim_key])



def jwt_required(optional=False, fresh=False, refresh=False, locations=None):
    """
    A decorator to protect a Flask endpoint with JSON Web Tokens.

    Any route decorated with this will require a valid JWT to be present in the
    request (unless optional=True, in which case no JWT is also valid) before the
    endpoint can be called.

    :param optional:
        If ``True``, allow the decorated endpoint to be accessed if no JWT is present in
        the request. Defaults to ``False``.

    :param fresh:
        If ``True``, require a JWT marked with ``fresh`` to be able to access this
        endpoint. Defaults to ``False``.

    :param refresh:
        If ``True``, requires a refresh JWT to access this endpoint. If ``False``,
        requires an access JWT to access this endpoint. Defaults to ``False``.

    :param locations:
        A location or list of locations to look for the JWT in this request, for
        example ``'headers'`` or ``['headers', 'cookies']``. Defaults to ``None``
        which indicates that JWTs will be looked for in the locations defined by the
        ``JWT_TOKEN_LOCATION`` configuration option.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            # Compatibility with flask < 2.0
            if hasattr(current_app, "ensure_sync") and callable(
                getattr(current_app, "ensure_sync", None)
            ):
                return current_app.ensure_sync(fn)(*args, **kwargs)

            return fn(*args, **kwargs)  # pragma: no cover

        return decorator

    return wrapper
