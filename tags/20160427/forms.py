__author__ = 'caschmitz'
from wtforms import Form, FloatField, validators, StringField, PasswordField, BooleanField
from db_model import db, User
import flask.ext.wtf.html5 as html5

class InputForm(Form):
    #####How to split these up to iterate through them seperatly?  Cannot
    # Fields
    energy = FloatField(label='Energy: ', default=1, validators=[validators.InputRequired()])
    energyCalc = FloatField(label='Energy Calculated')
    xtal1A = FloatField(label='Xtal 1 Angle: ', default=2, validators=[validators.InputRequired()])
    xtal2A = FloatField(label='Xtal 2 Angle: ', default=3, validators=[validators.InputRequired()])
    xtal1T = FloatField(label='Xtal 1 Temp: ', default=12, validators=[validators.InputRequired()])
    xtal2T = FloatField(label='Xtal 2 Temp: ', default=15, validators=[validators.InputRequired()])
    tempCorr = FloatField(label='Temp. corr')
    signal = FloatField(label='Signal: ', default=11, validators=[validators.InputRequired()])
    signalNorm = FloatField(label='Signal Normalized')
    norm = FloatField(label='Norm.: ', default=7, validators=[validators.InputRequired()])
    normFac = FloatField(label='Norm. Factors')
    extra = FloatField(label='Extra: ', default=1, validators=[validators.InputRequired()])

    #columns = [energy, energyCalc, xtal1A, xtal2A, xtal1T, xtal2T, tempCorr, signal, signalNorm, norm, normFac, extra]

    # Assign labels so that an equality check can still be used between columns and bools
    ebool = BooleanField(label='energy', default=True)
    ecbool = BooleanField(label='energyCalc', default=False)
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
    comment = StringField('Comment', [validators.Length(min=0, max=10000)])

class register_form(Form):
    username = StringField(label='Username', validators=[validators.InputRequired()])
    password = PasswordField(label='Password', validators=[validators.InputRequired(), validators.equal_to('confirm', message='Passwords must match')])
    confirm = PasswordField(label='Confirm Password', validators=[validators.InputRequired()])
    email = html5.EmailField(label='Email')
    notify = BooleanField(label='Email notifications')

    def validate(self):
        if not Form.validate(self):
            return False

        if self.notify.data and not self.email.data:
            self.notify.errors.append('Cannot send notifications without a valid email address')
            return False

        if db.session.query(User).filter_by(username=self.username.data).count() > 0:
            self.username.errors.append('User already exists')
            return False

        return True

class login_form(Form):
    username = StringField(label='Username', validators=[validators.InputRequired()])
    password = PasswordField(label='Password', validators=[validators.InputRequired()])

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