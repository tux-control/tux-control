"""
This is flask-jwt-extended version 4 implementation of custom resolver
"""


from functools import wraps
from flask import request, current_app
from werkzeug.exceptions import BadRequest
from flask_jwt_extended.config import config
from flask_jwt_extended.view_decorators import _load_user, _decode_jwt_from_cookies, _decode_jwt_from_query_string, _decode_jwt_from_headers, _verify_token_is_fresh, _decode_jwt_from_json
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended.utils import decode_token, get_unverified_jwt_headers
from flask_jwt_extended.internal_utils import verify_token_type, verify_token_not_blocklisted, custom_verification_for_token
from flask import _request_ctx_stack


def _decode_jwt_from_event(refresh):
    if not request.event:
        raise NoAuthorizationError('Invalid content-type. Must have event.')

    if refresh:
        token_key = config.refresh_json_key
    else:
        token_key = config.json_key

    try:
        encoded_token = request.event.get('args')[0].get(token_key, None)
        if not encoded_token:
            raise BadRequest()
    except BadRequest:
        raise NoAuthorizationError('Missing "{}" key in json data.'.format(token_key))

    return encoded_token, None


def _decode_jwt_from_request(locations, fresh, refresh=False):
    # Figure out what locations to look for the JWT in this request
    if isinstance(locations, str):
        locations = [locations]

    if not locations:
        locations = config.token_location

    # Get the decode functions in the order specified by locations.
    # Each entry in this list is a tuple (<location>, <encoded-token-function>)
    get_encoded_token_functions = [("json", lambda: _decode_jwt_from_event(refresh))]
    for location in locations:
        if location == "cookies":
            get_encoded_token_functions.append(
                (location, lambda: _decode_jwt_from_cookies(refresh))
            )
        elif location == "query_string":
            get_encoded_token_functions.append(
                (location, _decode_jwt_from_query_string)
            )
        elif location == "headers":
            get_encoded_token_functions.append((location, _decode_jwt_from_headers))
        elif location == "json":
            get_encoded_token_functions.append(
                (location, lambda: _decode_jwt_from_json(refresh))
            )
        else:
            raise RuntimeError(f"'{location}' is not a valid location")

    # Try to find the token from one of these locations. It only needs to exist
    # in one place to be valid (not every location).
    errors = []
    decoded_token = None
    jwt_header = None
    jwt_location = None
    for location, get_encoded_token_function in get_encoded_token_functions:
        try:
            encoded_token, csrf_token = get_encoded_token_function()
            decoded_token = decode_token(encoded_token, csrf_token)
            jwt_location = location
            jwt_header = get_unverified_jwt_headers(encoded_token)
            break
        except NoAuthorizationError as e:
            errors.append(str(e))

    # Do some work to make a helpful and human readable error message if no
    # token was found in any of the expected locations.
    if not decoded_token:
        if len(locations) > 1:
            err_msg = "Missing JWT in {start_locs} or {end_locs} ({details})".format(
                start_locs=", ".join(locations[:-1]),
                end_locs=locations[-1],
                details="; ".join(errors),
            )
            raise NoAuthorizationError(err_msg)
        else:
            raise NoAuthorizationError(errors[0])

    # Additional verifications provided by this extension
    verify_token_type(decoded_token, refresh)
    if fresh:
        _verify_token_is_fresh(jwt_header, decoded_token)
    verify_token_not_blocklisted(jwt_header, decoded_token)
    custom_verification_for_token(jwt_header, decoded_token)

    return decoded_token, jwt_header, jwt_location


def verify_jwt_in_request(optional=False, fresh=False, refresh=False, locations=None):
    """
    Verify that a valid JWT is present in the request, unless ``optional=True`` in
    which case no JWT is also considered valid.

    :param optional:
        If ``True``, do not raise an error if no JWT is present in the request.
        Defaults to ``False``.

    :param fresh:
        If ``True``, require a JWT marked as ``fresh`` in order to be verified.
        Defaults to ``False``.

    :param refresh:
        If ``True``, require a refresh JWT to be verified.

    :param locations:
        A location or list of locations to look for the JWT in this request, for
        example ``'headers'`` or ``['headers', 'cookies']``. Defaults to ``None``
        which indicates that JWTs will be looked for in the locations defined by the
        ``JWT_TOKEN_LOCATION`` configuration option.
    """
    if request.method in config.exempt_methods:
        return

    try:
        if refresh:
            jwt_data, jwt_header, jwt_location = _decode_jwt_from_request(
                locations, fresh, refresh=True
            )
        else:
            jwt_data, jwt_header, jwt_location = _decode_jwt_from_request(
                locations, fresh
            )
    except NoAuthorizationError:
        if not optional:
            raise
        _request_ctx_stack.top.jwt = {}
        _request_ctx_stack.top.jwt_header = {}
        _request_ctx_stack.top.jwt_user = {"loaded_user": None}
        _request_ctx_stack.top.jwt_location = None
        return

    # Save these at the very end so that they are only saved in the requet
    # context if the token is valid and all callbacks succeed
    _request_ctx_stack.top.jwt_user = _load_user(jwt_header, jwt_data)
    _request_ctx_stack.top.jwt_header = jwt_header
    _request_ctx_stack.top.jwt = jwt_data
    _request_ctx_stack.top.jwt_location = jwt_location

    return jwt_header, jwt_data


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
            verify_jwt_in_request(optional, fresh, refresh, locations)

            # Compatibility with flask < 2.0
            if hasattr(current_app, "ensure_sync") and callable(
                getattr(current_app, "ensure_sync", None)
            ):
                return current_app.ensure_sync(fn)(*args, **kwargs)

            return fn(*args, **kwargs)  # pragma: no cover

        return decorator

    return wrapper

