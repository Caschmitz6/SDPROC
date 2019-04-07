__author__ = 'caschmitz'
'''
-    Copyright (c) UChicago Argonne, LLC. All rights reserved.
-
-    Copyright UChicago Argonne, LLC. This software was produced
-    under U.S. Government contract DE-AC02-06CH11357 for Argonne National
-    Laboratory (ANL), which is operated by UChicago Argonne, LLC for the
-    U.S. Department of Energy. The U.S. Government has rights to use,
-    reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR
-    UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR
-    ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is
-    modified to produce derivative works, such modified software should
-    be clearly marked, so as not to confuse it with the version available
-    from ANL.
-
-    Additionally, redistribution and use in source and binary forms, with
-    or without modification, are permitted provided that the following
-    conditions are met:
-
-        * Redistributions of source code must retain the above copyright
-          notice, this list of conditions and the following disclaimer.
-
-        * Redistributions in binary form must reproduce the above copyright
-          notice, this list of conditions and the following disclaimer in
-          the documentation and/or other materials provided with the
-          distribution.
-
-        * Neither the name of UChicago Argonne, LLC, Argonne National
-          Laboratory, ANL, the U.S. Government, nor the names of its
-          contributors may be used to endorse or promote products derived
-          from this software without specific prior written permission.
-
-    THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS
-    AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
-    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
-    FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago
-    Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
-    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
-    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
-    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
-    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
-    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
-    ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
-    POSSIBILITY OF SUCH DAMAGE.
'''
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
import re
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    pwhash = db.Column(db.String())
    email = db.Column(db.String(120), nullable=True)
    fullName = db.Column(db.String())
    institution = db.Column(db.String())
    reason = db.Column(db.String())
    commentChar = db.Column(db.String())
    current_session = db.Column(db.String())
    approved = db.Column(db.Integer())

    isAdmin = db.Column(db.Integer())

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

    def is_strong_pass(self, pw):
        length_error = len(pw) < 8
        digit_error = re.search(r"\d", pw) is None
        uppercase_error = re.search(r"[A-Z]", pw) is None
        lowercase_error = re.search(r"[a-z]", pw) is None
        symbol_error = re.search(r"\W", pw) is None
        password_ok = not(length_error or digit_error or uppercase_error or lowercase_error or symbol_error)
        return {
            'password_ok' : password_ok,
            'Length at least 8' : length_error,
            'At least one digit' : digit_error,
            'At least one uppercase' : uppercase_error,
            'At least one lowercase' : lowercase_error,
            'At least one symbol' : symbol_error,
        }

class notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    originUser = db.Column(db.String())
    type = db.Column(db.String())
    timestamp = db.Column(db.DateTime())


class logBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    path = db.Column(db.String())
    comment = db.Column(db.String(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('loggedUser', lazy='dynamic'))
    plot = db.Column(db.String())
    timestamp = db.Column(db.DateTime())
    session = db.Column(db.String())
    checked = db.Column(db.Boolean())

    against_E = db.Column(db.String())

    hrm = db.Column(db.String())

    energy = db.Column(db.Integer())
    xtal1A = db.Column(db.Integer())
    xtal2A = db.Column(db.Integer())
    xtal1T = db.Column(db.Integer())
    xtal2T = db.Column(db.Integer())
    signal = db.Column(db.Integer())
    norm = db.Column(db.Integer())
    extra = db.Column(db.Integer())

    ebool = db.Column(db.Boolean())
    ecbool = db.Column(db.Boolean())
    etcbool = db.Column(db.Boolean())
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
    comChar = db.Column(db.String())
    type = db.Column(db.String())


class currentMeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    path = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('currentUser', lazy='dynamic'))
    plot = db.Column(db.String())
    comment = db.Column(db.String())
    file_id = db.Column(db.Integer())
    session = db.Column(db.String())
    checked = db.Column(db.Boolean())

    fit_type = db.Column(db.String())
    fit_pos = db.Column(db.Float())
    fit_range = db.Column(db.Float())
    fit_localRange = db.Column(db.Float())
    fit_energy = db.Column(db.String())
    fit_signal = db.Column(db.String())

    hrm = db.Column(db.String())

    against_E = db.Column(db.String())

    energy = db.Column(db.Integer())
    xtal1A = db.Column(db.Integer())
    xtal2A = db.Column(db.Integer())
    xtal1T = db.Column(db.Integer())
    xtal2T = db.Column(db.Integer())
    signal = db.Column(db.Integer())
    norm = db.Column(db.Integer())
    extra = db.Column(db.Integer())

    ebool = db.Column(db.Boolean())
    ecbool = db.Column(db.Boolean())
    etcbool = db.Column(db.Boolean())
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


class currentDAT(db.Model):
    __tablename__ = 'currentDAT'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_id = db.Column(db.Integer, db.ForeignKey('data_file.id'))
    user = db.relationship('User', backref=db.backref('cUserDAT', lazy='dynamic'))
    DATname = db.Column(db.String())
    DAT = db.Column(db.String())
    originDAT = db.Column(db.String())


class sessionMeta(db.Model):
    __tablename__ = 'sessionMeta'
    id = db.Column(db.Integer, primary_key=True)

    fileName = db.Column(db.String())
    path = db.Column(db.String())
    comment = db.Column(db.String())
    file_id = db.Column(db.Integer())
    session = db.Column(db.String())
    checked = db.Column(db.Boolean())

    fit_type = db.Column(db.String())
    fit_pos = db.Column(db.Float())
    fit_range = db.Column(db.Float())
    fit_localRange = db.Column(db.Float())
    fit_energy = db.Column(db.String())
    fit_signal = db.Column(db.String())

    against_E = db.Column(db.String())

    hrm = db.Column(db.String())

    energy = db.Column(db.Integer())
    xtal1A = db.Column(db.Integer())
    xtal2A = db.Column(db.Integer())
    xtal1T = db.Column(db.Integer())
    xtal2T = db.Column(db.Integer())
    signal = db.Column(db.Integer())
    norm = db.Column(db.Integer())
    extra = db.Column(db.Integer())

    ebool = db.Column(db.Boolean())
    ecbool = db.Column(db.Boolean())
    etcbool = db.Column(db.Boolean())
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


class sessionFiles(db.Model):
    __tablename__ = 'sessionFiles'
    id = db.Column(db.Integer, primary_key=True)
    #sessionMeta_id = db.Column(db.ForeignKey('sessionMeta.id'))
    #sessionMeta = relationship("sessionMeta")

    name = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('oldUser', lazy='dynamic'))
    comment = db.Column(db.String())
    authed = db.Column(db.String())
    last_used = db.Column(db.DateTime())
    #sessionMeta_ids = db.Column(db.String())


class sessionFilesMeta(db.Model):
    __tablename__ = 'sessionFilesMeta'

    sessionFilesMeta_id = db.Column(db.Integer, primary_key=True)
    sessionFiles_id = db.Column(db.ForeignKey('sessionFiles.id'))
    sessionMeta_id = db.Column(db.ForeignKey('sessionMeta.id'))


class userFiles(db.Model):
    userFiles_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('user.id'))
    file_id = db.Column(db.ForeignKey('data_file.id'))


class loginAttempts(db.Model):
    id = db.Column(db.Integer, primary_key=True)


class HRM(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String())
    hrm_e0 = db.Column(db.Float())
    hrm_bragg1 = db.Column(db.Float())
    hrm_bragg2 = db.Column(db.Float())
    hrm_geo = db.Column(db.String())
    hrm_alpha1 = db.Column(db.Float())
    hrm_alpha2 = db.Column(db.Float())
    hrm_theta1_sign = db.Column(db.Integer())
    hrm_theta2_sign = db.Column(db.Integer())

