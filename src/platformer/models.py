from datetime import datetime
from sqlalchemy.orm import validates

from database import db


class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode, nullable=False)
    value = db.Column(db.Unicode, nullable=False)
    reliability = db.relationship('ReliabilityMetadata', uselist=False, backref='memo')


class ReliabilityMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Unicode, unique=True, nullable=False)
    score = db.Column(db.Integer, primary_key=True)
    memo_id = db.Column(db.Integer, db.ForeignKey('memo.id'))


class Peer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode, unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    health = db.Column(db.Float, nullable=False, default=1.0)
    last_checked = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    @validates('health')
    def validate_health(self, key, health):
        assert 0.0 <= health <= 1.0
