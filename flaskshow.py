"""Shows login-ed websites in a flask server."""

from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask, send_file, redirect, url_for, request)

from logins import ps_login, ms_login, psl_login
from webutils import set_up_session, load_text
from exceptions import WrongUsernameOrPassword


# Very crappy, loads of bugs, highly unoptimized,
# non-deterministic, abstraction needed,
# non-platform-independent, single-threaded,
# but works at least ;)  (for a 0.01% chance)

# won't be in final project. just doing for demo/fun

port = 11111
app = Flask(__file__)

session = set_up_session()
username, password = None, None

all_methods = (
    'GET', 'HEAD', 'POST', 'PUT',
    'DELETE', 'CONNECT', 'OPTIONS',
    'TRACE', 'PATCH'
)


def render_response(resp, replace=True):
    """Renders outer response.

    resp: requests.models.Response
    replace: tuple (old, new)
    """
    html = load_text(resp)
    if replace:
        url = resp.url
        if not url.endswith('/'):
            url += '/'
        html.replace('"/', '"' + url)
    return html, resp.status_code, [] # resp.headers.items()


# Decorator for pages that require login
def require_username_password(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        global username, password
        if username is None or password is None:
            return redirect(url_for('user_login') +
                '?redirect=' + url_for(view.__name__))
        try:
            return view(*args, **kwargs)
        except WrongUsernameOrPassword:
            return redirect(url_for('user_login') +
                '?redirect=' + url_for('outlook') +
                '&wrong=1')
    return wrapped_view


@app.route('/')
@require_username_password
def main_page():
    return send_file('./html/index.html')


@app.route('/login', methods=('GET', 'POST'))
def user_login():
    global username, password
    if request.method == 'GET':
        return send_file('./html/login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        redirect_url = request.args['redirect']
        return redirect(redirect_url)


@app.route('/outlook')
@require_username_password
def outlook():
    global session, username, password
    return render_response(
        ms_login(session, username, password)
    )


@app.route('/powerschool_learning')
@require_username_password
def powerschool_learning():
    global session, username, password
    return render_response(
        psl_login(session, username, password)
    )


# Should not happen after initial version
# Well after further investigation it might happen
# Yeah agree with line 2 and line 1 is false
@app.route('/<string:path>', methods=all_methods)
@app.route('/<path:path>', methods=all_methods)
def return_from_page(path):
    global session
    if url_for('powerschool_learning') in request.referrer:
        return render_response(
            session.request(
                request.method,
                'https://ykpaoschool.learning.powerschool.com/'
                + path
            )
        )
    elif url_for('outlook') in request.referrer:
        return ('', 404, [])


app.run('localhost', port=port)