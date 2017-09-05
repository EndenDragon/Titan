from flask import Blueprint, request, redirect, jsonify, abort, session, url_for, render_template
from flask import current_app as app
from config import config
from titanembeds.decorators import discord_users_only
from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, Cosmetics, UserCSS, set_titan_token, get_titan_token
from titanembeds.oauth import authorize_url, token_url, make_authenticated_session, get_current_authenticated_user, get_user_managed_servers, check_user_can_administrate_guild, check_user_permission, generate_avatar_url, generate_guild_icon_url, generate_bot_invite_url
import time
import datetime
import paypalrestsdk

user = Blueprint("user", __name__)

@user.route("/login_authenticated", methods=["GET"])
def login_authenticated():
    session["redirect"] = request.args.get("redirect")
    scope = ['identify', 'guilds', 'guilds.join']
    discord = make_authenticated_session(scope=scope)
    authorization_url, state = discord.authorization_url(
        authorize_url,
        access_type="offline"
    )
    session['oauth2_state'] = state
    return redirect(authorization_url)

@user.route('/callback', methods=["GET"])
def callback():
    state = session.get('oauth2_state')
    if not state or request.values.get('error'):
        return redirect(url_for('user.logout'))
    discord = make_authenticated_session(state=state)
    discord_token = discord.fetch_token(
        token_url,
        client_secret=config['client-secret'],
        authorization_response=request.url)
    if not discord_token:
        return redirect(url_for('user.logout'))
    session['user_keys'] = discord_token
    session['unauthenticated'] = False
    user = get_current_authenticated_user()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['discriminator'] = user['discriminator']
    session['avatar'] = generate_avatar_url(user['id'], user['avatar'])
    session["tokens"] = get_titan_token(session["user_id"])
    if session["tokens"] == -1:
        session["tokens"] = 0
    if session["redirect"]:
        redir = session["redirect"]
        session['redirect'] = None
        return redirect(redir)
    return redirect(url_for("user.dashboard"))

@user.route('/logout', methods=["GET"])
def logout():
    redir = session.get("redirect", None)
    session.clear()
    if redir:
        session['redirect'] = redir
        return redirect(session['redirect'])
    return redirect(url_for("index"))

@user.route("/dashboard")
@discord_users_only()
def dashboard():
    guilds = get_user_managed_servers()
    if not guilds:
        session["redirect"] = url_for("user.dashboard")
        return redirect(url_for("user.logout"))
    error = request.args.get("error")
    if session["redirect"] and not (error and error == "access_denied"):
        redir = session['redirect']
        session['redirect'] = None
        return redirect(redir)
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    css_list = None
    if cosmetics and cosmetics.css:
        css_list = db.session.query(UserCSS).filter(UserCSS.user_id == session['user_id']).all()
    return render_template("dashboard.html.j2", servers=guilds, icon_generate=generate_guild_icon_url, cosmetics=cosmetics, css_list=css_list)

@user.route("/custom_css/new", methods=["GET"])
@discord_users_only()
def new_custom_css_get():
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    return render_template("usercss.html.j2", new=True)

@user.route("/custom_css/new", methods=["POST"])
@discord_users_only()
def new_custom_css_post():
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    
    name = request.form.get("name", None)
    user_id = session["user_id"]
    css = request.form.get("css","")
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    css = UserCSS(name, user_id, css)
    db.session.add(css)
    db.session.commit()
    return jsonify({"id": css.id})

@user.route("/custom_css/edit/<css_id>", methods=["GET"])
@discord_users_only()
def edit_custom_css_get(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    css = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not css:
        abort(404)
    if css.user_id != session['user_id']:
        abort(403)
    return render_template("usercss.html.j2", new=False, css=css)

@user.route("/custom_css/edit/<css_id>", methods=["POST"])
@discord_users_only()
def edit_custom_css_post(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    if dbcss.user_id != session['user_id']:
        abort(403)
    name = request.form.get("name", None)
    css = request.form.get("css", "")
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    dbcss.name = name
    dbcss.css = css
    db.session.commit()
    return jsonify({"id": dbcss.id})

@user.route("/custom_css/edit/<css_id>", methods=["DELETE"])
@discord_users_only()
def edit_custom_css_delete(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    if dbcss.user_id != session['user_id']:
        abort(403)
    db.session.delete(dbcss)
    db.session.commit()
    return jsonify({})

@user.route("/administrate_guild/<guild_id>", methods=["GET"])
@discord_users_only()
def administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        return redirect(url_for("user.dashboard"))
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        session["redirect"] = url_for("user.administrate_guild", guild_id=guild_id, _external=True)
        return redirect(url_for("user.add_bot", guild_id=guild_id))
    session["redirect"] = None
    permissions=[]
    if check_user_permission(guild_id, 5):
        permissions.append("Manage Embed Settings")
    if check_user_permission(guild_id, 2):
        permissions.append("Ban Members")
    if check_user_permission(guild_id, 1):
        permissions.append("Kick Members")
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).order_by(UnauthenticatedUsers.last_timestamp).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    dbguild_dict = {
        "id": db_guild.guild_id,
        "name": db_guild.name,
        "unauth_users": db_guild.unauth_users,
        "visitor_view": db_guild.visitor_view,
        "webhook_messages": db_guild.webhook_messages,
        "chat_links": db_guild.chat_links,
        "bracket_links": db_guild.bracket_links,
        "mentions_limit": db_guild.mentions_limit,
        "icon": db_guild.icon,
        "discordio": db_guild.discordio if db_guild.discordio != None else ""
    }
    return render_template("administrate_guild.html.j2", guild=dbguild_dict, members=users, permissions=permissions)

@user.route("/administrate_guild/<guild_id>", methods=["POST"])
@discord_users_only()
def update_administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        abort(403)
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        abort(400)
    db_guild.unauth_users = request.form.get("unauth_users", db_guild.unauth_users) in ["true", True]
    db_guild.visitor_view = request.form.get("visitor_view", db_guild.visitor_view) in ["true", True]
    db_guild.webhook_messages = request.form.get("webhook_messages", db_guild.webhook_messages) in ["true", True]
    db_guild.chat_links = request.form.get("chat_links", db_guild.chat_links) in ["true", True]
    db_guild.bracket_links = request.form.get("bracket_links", db_guild.bracket_links) in ["true", True]
    db_guild.mentions_limit = request.form.get("mentions_limit", db_guild.mentions_limit)
    
    discordio = request.form.get("discordio", db_guild.discordio)
    if discordio and discordio.strip() == "":
        discordio = None
    db_guild.discordio = discordio
    db.session.commit()
    return jsonify(
        id=db_guild.id,
        guild_id=db_guild.guild_id,
        unauth_users=db_guild.unauth_users,
        visitor_view=db_guild.visitor_view,
        webhook_messages=db_guild.webhook_messages,
        chat_links=db_guild.chat_links,
        bracket_links=db_guild.bracket_links,
        mentions_limit=db_guild.mentions_limit,
        discordio=db_guild.discordio,
    )

@user.route("/add-bot/<guild_id>")
@discord_users_only()
def add_bot(guild_id):
    session["redirect"] = None
    return render_template("add_bot.html.j2", guild_id=guild_id, guild_invite_url=generate_bot_invite_url(guild_id))

def prepare_guild_members_list(members, bans):
    all_users = []
    ip_pool = []
    members = sorted(members, key=lambda k: datetime.datetime.strptime(str(k.last_timestamp.replace(tzinfo=None)), "%Y-%m-%d %H:%M:%S"), reverse=True)
    for member in members:
        user = {
            "id": member.id,
            "username": member.username,
            "discrim": member.discriminator,
            "ip": member.ip_address,
            "last_visit": member.last_timestamp,
            "kicked": member.revoked,
            "banned": False,
            "banned_timestamp": None,
            "banned_by": None,
            "banned_reason": None,
            "ban_lifted_by": None,
            "aliases": [],
        }
        for banned in bans:
            if banned.ip_address == member.ip_address:
                if banned.lifter_id is None:
                    user['banned'] = True
                user["banned_timestamp"] = banned.timestamp
                user['banned_by'] = banned.placer_id
                user['banned_reason'] = banned.reason
                user['ban_lifted_by'] = banned.lifter_id
            continue
        if user["ip"] not in ip_pool:
            all_users.append(user)
            ip_pool.append(user["ip"])
        else:
            for usr in all_users:
                if user["ip"] == usr["ip"]:
                    alias = user["username"]+"#"+str(user["discrim"])
                    if len(usr["aliases"]) < 5 and alias not in usr["aliases"]:
                        usr["aliases"].append(alias)
                    continue
    return all_users

@user.route("/ban", methods=["POST"])
@discord_users_only(api=True)
def ban_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    reason = request.form.get("reason", None)
    if reason is not None:
        reason = reason.strip()
        if reason == "":
            reason = None
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is not None:
        if db_ban.lifter_id is None:
            abort(409)
        db.session.delete(db_ban)
    db_ban = UnauthenticatedBans(guild_id, db_user.ip_address, db_user.username, db_user.discriminator, reason, session["user_id"])
    db.session.add(db_ban)
    db.session.commit()
    return ('', 204)

@user.route("/ban", methods=["DELETE"])
@discord_users_only(api=True)
def unban_unauthenticated_user():
    guild_id = request.args.get("guild_id", None)
    user_id = request.args.get("user_id", None)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is None:
        abort(404)
    if db_ban.lifter_id is not None:
        abort(409)
    db_ban.liftBan(session["user_id"])
    return ('', 204)

@user.route("/revoke", methods=["POST"])
@discord_users_only(api=True)
def revoke_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 1):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    if db_user.isRevoked():
        abort(409)
    db_user.revokeUser()
    return ('', 204)

@user.route('/donate', methods=["GET"])
@discord_users_only()
def donate_get():
    return render_template('donate.html.j2')

def get_paypal_api():
    return paypalrestsdk.Api({
        'mode': 'sandbox' if app.config["DEBUG"] else 'live',
        'client_id': config["paypal-client-id"],
        'client_secret': config["paypal-client-secret"]})

@user.route('/donate', methods=['POST'])
@discord_users_only()
def donate_post():
    donation_amount = request.form.get('amount')
    if not donation_amount:
        abort(402)

    donation_amount = "{0:.2f}".format(float(donation_amount))
    payer = {"payment_method": "paypal"}
    items = [{"name": "TitanEmbeds Donation",
              "price": donation_amount,
              "currency": "USD",
              "quantity": "1"}]
    amount = {"total": donation_amount,
              "currency": "USD"}
    description = "Donate and support TitanEmbeds development."
    redirect_urls = {"return_url": url_for('user.donate_confirm', success="true", _external=True),
                     "cancel_url": url_for('index', _external=True)}
    payment = paypalrestsdk.Payment({"intent": "sale",
                                     "payer": payer,
                                     "redirect_urls": redirect_urls,
                                     "transactions": [{"item_list": {"items":
                                                                     items},
                                                       "amount": amount,
                                                       "description":
                                                       description}]}, api=get_paypal_api())
    if payment.create():
        for link in payment.links:
            if link['method'] == "REDIRECT":
                return redirect(link["href"])
    return redirect(url_for('index'))
    
@user.route("/donate/confirm")
@discord_users_only()
def donate_confirm():
    if not request.args.get('success'):
        return redirect(url_for('index'))
    payment = paypalrestsdk.Payment.find(request.args.get('paymentId'), api=get_paypal_api())
    if payment.execute({"payer_id": request.args.get('PayerID')}):
        trans_id = str(payment.transactions[0]["related_resources"][0]["sale"]["id"])
        amount = float(payment.transactions[0]["amount"]["total"])
        tokens = int(amount * 100)
        action = "PAYPAL {}".format(trans_id)
        set_titan_token(session["user_id"], tokens, action)
        session["tokens"] = get_titan_token(session["user_id"])
        return redirect(url_for('user.donate_thanks', transaction=trans_id))
    else:
        return redirect(url_for('index'))

@user.route("/donate/thanks")
@discord_users_only()
def donate_thanks():
    tokens = get_titan_token(session["user_id"])
    transaction = request.args.get("transaction")
    return render_template("donate_thanks.html.j2", tokens=tokens, transaction=transaction)