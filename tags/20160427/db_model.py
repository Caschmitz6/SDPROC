__author__ = 'caschmitz'
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import app


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    pwhash = db.Column(db.String())
    email = db.Column(db.String(120), nullable=True)
    notify = db.Column(db.Boolean())

    def __repr__(self):
        return '<User %r>' % (self.username)

    def check_password(self, pw):
        return check_password_hash(self.pwhash, pw)

    def set_password(self, pw):
        self.pwhash = generate_password_hash(pw)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class metaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    path = db.Column(db.String())
    comment = db.Column(db.String(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('metaData', lazy='dynamic'))
    plot = db.Column(db.String())

    against_E = db.Column(db.Boolean())

    energy = db.Column(db.String())
    xtal1A = db.Column(db.String())
    xtal2A = db.Column(db.String())
    xtal1T = db.Column(db.String())
    xtal2T = db.Column(db.String())
    signal = db.Column(db.String())
    norm = db.Column(db.String())
    extra = db.Column(db.String())

    ebool = db.Column(db.Boolean())
    ecbool = db.Column(db.Boolean())
    a1bool = db.Column(db.Boolean())
    a2bool = db.Column(db.Boolean())
    t1bool = db.Column(db.Boolean())
    t2bool = db.Column(db.Boolean())
    tcbool = db.Column(db.Boolean())
    sbool = db.Column(db.Boolean())
    snbool = db.Column(db.Boolean())
    nbool = db.Column(db.Boolean())
    nfbool = db.Column(db.Boolean())
    xbool = db.Column(db.Boolean())

class dataFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    path = db.Column(db.String())
    comment = db.Column(db.String())
    authed = db.Column(db.String())


class fileFormat(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    path = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('tempStorage', lazy='dynamic'))
    plot = db.Column(db.String())
    comment = db.Column(db.String())

    against_E = db.Column(db.Boolean())

    energy = db.Column(db.String())
    xtal1A = db.Column(db.String())
    xtal2A = db.Column(db.String())
    xtal1T = db.Column(db.String())
    xtal2T = db.Column(db.String())
    signal = db.Column(db.String())
    norm = db.Column(db.String())
    extra = db.Column(db.String())

    ebool = db.Column(db.Boolean())
    ecbool = db.Column(db.Boolean())
    a1bool = db.Column(db.Boolean())
    a2bool = db.Column(db.Boolean())
    t1bool = db.Column(db.Boolean())
    t2bool = db.Column(db.Boolean())
    tcbool = db.Column(db.Boolean())
    sbool = db.Column(db.Boolean())
    snbool = db.Column(db.Boolean())
    nbool = db.Column(db.Boolean())
    nfbool = db.Column(db.Boolean())
    xbool = db.Column(db.Boolean())


