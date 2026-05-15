from datetime import datetime
import bcrypt
from extensions import db


class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'

    id          = db.Column(db.Integer, primary_key=True)
    nickname    = db.Column(db.String(30), nullable=False)
    email       = db.Column(db.String(120), nullable=False)
    pin_hash    = db.Column(db.String(255), nullable=False)
    status      = db.Column(db.String(20), default='pending')  # pending / done
    admin_reply = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_pin(self, raw_pin):
        hashed = bcrypt.hashpw(raw_pin.encode('utf-8'), bcrypt.gensalt(rounds=12))
        self.pin_hash = hashed.decode('utf-8')

    def check_pin(self, raw_pin):
        return bcrypt.checkpw(raw_pin.encode('utf-8'), self.pin_hash.encode('utf-8'))
