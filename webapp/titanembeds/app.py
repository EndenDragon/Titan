from config import config
from database import db
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from flask_sslify import SSLify
from titanembeds.utils import rate_limiter, discord_api, bot_alive
import blueprints.api
import blueprints.user
import blueprints.admin
import blueprints.embed
import os


os.chdir(config['app-location'])
app = Flask(__name__, static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = config['database-uri'] + "?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning/no need this on for now.
app.config['RATELIMIT_HEADERS_ENABLED'] = True
app.config['SQLALCHEMY_POOL_RECYCLE'] = 250
app.config['RATELIMIT_STORAGE_URL'] = 'keyvalprops://'
app.secret_key = config['app-secret']

db.init_app(app)
rate_limiter.init_app(app)
sslify = SSLify(app, permanent=True)

app.register_blueprint(blueprints.api.api, url_prefix="/api", template_folder="/templates")
app.register_blueprint(blueprints.admin.admin, url_prefix="/admin", template_folder="/templates")
app.register_blueprint(blueprints.user.user, url_prefix="/user", template_folder="/templates")
app.register_blueprint(blueprints.embed.embed, url_prefix="/embed", template_folder="/templates")

@app.route("/")
def index():
    return render_template("index.html.j2")

@app.route("/about")
def about():
    return render_template("about.html.j2")

@app.before_request
def before_request():
    db.create_all()
    discord_api.init_discordrest()

@app.context_processor
def context_processor():
    bot_status = bot_alive()
    return {"bot_status": bot_status}