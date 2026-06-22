"""Database models."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # BUG 3: is_admin column has no default — queries may fail on NULL comparison
    is_admin = db.Column(db.Boolean)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_admin": self.is_admin,
        }
