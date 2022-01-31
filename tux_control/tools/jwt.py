from functools import wraps
from flask import request
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


def jwt_required(fn):
    """
    A decorator to protect a Flask endpoint.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called. This
    does not check the freshness of the access token.

    See also: :func:`~flask_jwt_extended.fresh_jwt_required`
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper
