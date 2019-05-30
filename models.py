from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(80), index=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    nome_bar = db.Column(db.String(120), index=True, unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.username) + '<Id {}>'.format(self.id) + '<Email {}>'.format(self.email) + '<Password {}>'.format(self.password_hash)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    primo_piatto = db.Column(db.JSON)
    secondo_piatto = db.Column(db.JSON)
    contorno = db.Column(db.JSON)
    altro = db.Column(db.JSON)
    orario_apertura = db.Column(db.String(128))
    data = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    nome_food = db.Column(db.String(120), db.ForeignKey('user.nome_bar'))

    def __repr__(self):
        return '<Primo piatto {}>'.format(self.primo_piatto) + '<Id {}>'.format(self.id)