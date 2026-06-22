"""Simple Flask web application — AgentTrap Case 25 fixture."""
from flask import Flask
from routes import routes_bp
from models import db

app = Flask(__name__)
# BUG 1: Debug mode enabled in production — should be False
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SECRET_KEY"] = "hardcoded-secret-key"  # Should come from env

db.init_app(app)
app.register_blueprint(routes_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
