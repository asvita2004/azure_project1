"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid
from flask import current_app


imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER']  + '/'

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            current_app.logger.warning(
                f"LOCAL LOGIN FAILED: username={form.username.data}, IP={request.remote_addr}"
            )
            return redirect(url_for('login'))

        # Login success
        login_user(user, remember=form.remember_me.data)
        current_app.logger.info(
            f"LOCAL LOGIN SUCCESS: username={user.username}, IP={request.remote_addr}"
        )

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)

    # If GET or form not valid, show login page
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)


@app.route(Config.REDIRECT_PATH)  # This should be /getAToken
def authorized():
    # Check state to prevent CSRF
    if request.args.get("state") != session.get("state"):
        current_app.logger.warning("LOGIN FAILED: State mismatch (possible CSRF)")
        return redirect(url_for("home"))

    # Handle authentication/authorization errors
    if "error" in request.args:
        current_app.logger.error(
            f"LOGIN FAILED: Azure AD error - {request.args.get('error_description')}"
        )
        return render_template("auth_error.html", result=request.args)

    # If we have an authorization code from MS
    if "code" in request.args:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=Config.SCOPE,
            redirect_uri=url_for("authorized", _external=True)
        )

        # Check if token was successfully acquired
        if "id_token_claims" in result:
            session["user"] = result["id_token_claims"]
            # Here, we log in the admin user; you can customize for dynamic users
            user = User.query.filter_by(username="admin").first()
            login_user(user)
            current_app.logger.info(
                f"LOGIN SUCCESS: Microsoft user {result['id_token_claims'].get('preferred_username')}"
            )
            _save_cache(cache)
        else:
            current_app.logger.error(
                f"LOGIN FAILED: Token acquisition failed - {result}"
            )
            return render_template("auth_error.html", result=result)

    return redirect(url_for("home"))


@app.route('/logout')
def logout():
    logout_user()
    if session.get("user"): # Used MS Login
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True,_scheme="https"))

    return redirect(url_for('login'))

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
        
def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        client_id=Config.CLIENT_ID,
        client_credential=Config.CLIENT_SECRET,
        authority=authority or Config.AUTHORITY,
        token_cache=cache
    )
    
def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=url_for("authorized", _external=True,_scheme="https")
    )
