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
from wtforms import Form, FloatField, validators, StringField, PasswordField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import RecaptchaField
from db_model import db, User
import flask.ext.wtf.html5 as html5

class InputForm(Form):
    # Fields
    energy = IntegerField(label='Energy: ', default=1, validators=[validators.InputRequired()])
    energyCalc = IntegerField(label='Energy calculated')
    energyTempCalc = IntegerField(label='Energy calculated w/T')
    xtal1A = IntegerField(label='Xtal 1 angle: ', default=2, validators=[validators.InputRequired()])
    xtal2A = IntegerField(label='Xtal 2 angle: ', default=3, validators=[validators.InputRequired()])
    xtal1T = IntegerField(label='Xtal 1 temp: ', default=12, validators=[validators.InputRequired()])
    xtal2T = IntegerField(label='Xtal 2 temp: ', default=15, validators=[validators.InputRequired()])
    tempCorr = IntegerField(label='Temp. corr')
    signal = IntegerField(label='Signal: ', default=11, validators=[validators.InputRequired()])
    signalNorm = IntegerField(label='Signal normalized')
    norm = IntegerField(label='Norm.: ', default=7, validators=[validators.InputRequired()])
    normFac = IntegerField(label='Norm. factors')
    extra = IntegerField(label='Extra: ', default=1, validators=[validators.InputRequired()])

    #columns = [energy, energyCalc, xtal1A, xtal2A, xtal1T, xtal2T, tempCorr, signal, signalNorm, norm, normFac, extra]

    # Assign labels so that an equality check can still be used between columns and bools
    ebool = BooleanField(label='energy', default=False)
    ecbool = BooleanField(label='energyCalc', default=False)
    etcbool = BooleanField(label='energyTempCalc', default=False)
    a1bool = BooleanField(label='xtal1A', default=False)
    a2bool = BooleanField(label='xtal2A', default=False)
    t1bool = BooleanField(label='xtal1T', default=False)
    t2bool = BooleanField(label='xtal2T', default=False)
    tcbool = BooleanField(label='tempCorr', default=False)
    sbool = BooleanField(label='signal', default=True)
    snbool = BooleanField(label='signalNorm', default=False)
    nbool = BooleanField(label='norm', default=False)
    nfbool = BooleanField(label='normFac', default=False)
    xbool = BooleanField(label='extra', default=False)

    #bools = [ebool, ecbool, a1bool, a2bool, t1bool, t2bool, tcbool, sbool, snbool, nbool, nfbool, xbool]


class CommentForm(Form):
    # Fields
    comment = TextAreaField('Comment', validators=[DataRequired()])
    recaptcha = RecaptchaField()

class register_form(Form):
    username = StringField(label='Username', validators=[validators.InputRequired()])
    fullName = StringField(label='Full Name', validators=[validators.InputRequired()])
    reason = StringField(label='Reason for Account Creation')

    password = PasswordField(label='Password', validators=[validators.InputRequired(), validators.equal_to('confirm', message='Passwords must match')])
    email = html5.EmailField(label='Email', validators=[validators.InputRequired()])
    confirm = PasswordField(label='Confirm Password', validators=[validators.InputRequired()])

    institution = StringField(label='Institution')

    def validate(self):
        if not Form.validate(self):
            return False

        if db.session.query(User).filter_by(username=self.username.data).count() > 0:
            self.username.errors.append('User already exists')
            return False

        return True

class login_form(Form):
    username = StringField(label='Username', validators=[validators.InputRequired()])
    password = PasswordField(label='Password', validators=[validators.InputRequired()])
    #recaptcha = RecaptchaField()

    def validate(self):
        if not Form.validate(self):
            return False

        user = self.get_user()

        if user is None:
            self.username.errors.append('Login Failed')
            #self.username.errors.append('Unknown username')
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append('Login Failed')
            #self.password.errors.append('Invalid password')
            return False

        return True

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()