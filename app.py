import os
from flask import Flask, jsonify, render_template
from config import Config
from extensions import database, jwt_manager, cors, cache_manager, mail_service

def create_app(config_class=Config):
    # Creation and configuration of the Flask application
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates"
    )
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["EXPORTS_DIR"], exist_ok=True)

    # Initialize Flask extensions
    database.init_app(app)
    jwt_manager.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    cache_manager.init_app(app)
    mail_service.init_app(app)

    from routes.auth_routes import authenticationBP
    from routes.admin_routes import adminBP
    from routes.staff_routes import staffBP
    from routes.user_routes import userBP

    app.register_blueprint(authenticationBP, url_prefix="/api/auth")
    app.register_blueprint(adminBP, url_prefix="/api/admin")
    app.register_blueprint(staffBP, url_prefix="/api/staff")
    app.register_blueprint(userBP, url_prefix="/api/user")

    # JWT authentication error handlers
    @jwt_manager.unauthorized_loader
    def _missing_token(reason):
        return jsonify(error="Authentication required.", detail=reason), 401

    @jwt_manager.invalid_token_loader
    def _invalid_token(reason):
        return jsonify(error="Invalid or expired session.", detail=reason), 401

    @jwt_manager.expired_token_loader
    def _expired_token(header, payload):
        return jsonify(error="Session expired, please log in again."), 401

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify(error="Resource not found."), 404
        return render_template("index.html")

    # Generic response for unexpected errors
    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Something went wrong on the server."), 500

    @app.route("/")
    @app.route("/<path:_unused_path>")
    def spa_shell(_unused_path=None):
        return render_template("index.html")

    with app.app_context():
        database.create_all()
        _seed_admin(app)

    return app

def _wants_json():
    from flask import request
    return request.path.startswith("/api/")

def _seed_admin(app):
    from models import User, roleOfAdmin, status_active_trekker

    if User.query.filter_by(role=roleOfAdmin).first():
        return

    admin = User(
        fullName=app.config["ADMIN_NAME"],
        email=app.config["ADMIN_EMAIL"],
        role=roleOfAdmin,
        status=status_active_trekker,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    database.session.add(admin)
    database.session.commit()

    print(f"[TrekManager] Admin account created -> {app.config['ADMIN_EMAIL']}")

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True, port=5000)