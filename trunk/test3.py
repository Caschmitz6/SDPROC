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
'''
For debugging server use:
    try:
        *line you want to test*
    except Exception,e:
        print(str(e))
'''

#TODO: Ask Nicholas for information on xtrepid UUID and giving permissions to Michael
#TODO: Subdirectories to file structure and make them searchable within the program
#TODO: Split comments from fileComments and sessionComments on Scans Tab
#TODO: Have fileComments searchable on manageFiles and sessionComments searchable on selectSession
#TODO: Make script to restart server

from flask import Flask, render_template, request, session, redirect, url_for, escape, redirect, make_response, flash, \
    send_from_directory, request
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpld3
import os
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from app import app
from db_model import db, User, logBook, dataFile, currentMeta, sessionMeta, sessionFiles, sessionFilesMeta, \
    notification, currentDAT, userFiles, HRM
from forms import InputForm, CommentForm
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import math
import numpy
import uuid
from sqlalchemy import desc, or_, and_
import mda
import mdaAscii
import copy
from scipy import stats
import time
import globus_sdk
from globusonline.transfer.api_client.goauth import get_access_token
from globusonline.transfer.api_client import Transfer
from globusonline.transfer.api_client import TransferAPIClient

login_manager = LoginManager()
login_manager.init_app(app)
ALLOWED_EXTENSIONS = {'txt', 'mda', 'dat'}
CLIENT_ID = '0c5f2ef9-7898-4d24-bdbf-57c3f1a2b4ea'
globusClient = None
usedArgs = []


#### REMOVE THIS ON SERVER #####
@app.before_request
def fixURL():
    url = request.path
    if 'SDproc' in url:
        fixedUrl = url[7:]
        return redirect(fixedUrl, 307)
    return


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/', methods=['GET', 'POST'])
def toLogin():
    '''Ensures users will be redirected to login page even without /login'''
    return redirect(url_for('login'))


@app.route('/reg', methods=['GET', 'POST'])
def register():
    '''
    Template generator method for the register page.

     Accepts register form, creates baseline user, sends notification to admin requesting account approval.
     :return:
    '''
    from forms import register_form
    form = register_form(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)
        strength = user.is_strong_pass(form.password.data)
        if strength['password_ok']:
            user.set_password(form.password.data)
            user.approved = 0
            user.isAdmin = 0

            db.session.add(user)

            notif = notification()
            notif.originUser = user.username
            notif.type = 'Create Account'
            notif.timestamp = getTime()

            db.session.add(notif)

            db.session.commit()

            return redirect(url_for('login'))
        else:
            for key, value in strength.iteritems():
                if value:
                    flash(key)
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Template generator method for the login page

    Accepts login form and ensure that the user has permission to login.

    This is done by using Flask's builtin login_user after checking that the user is approved in the database
    :return:
    '''
    from forms import login_form
    form = login_form(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        # user.approved = 1
        # user.isAdmin = 1
        if user.approved == 1:
            login_user(user)
            clear_cmeta()
            clear_rowa_wrapper()
            current_user.current_session = "None"
            db.session.commit()
            return redirect(url_for('index'))
        if user.approved == 2:
            refusePrompt = "Your account has been frozen"
            return render_template('login_form.html', form=form, session=session, refusePrompt=refusePrompt)
        if user.approved == 0:
            refusePrompt = "Wait for an admin to approve your account"
            return render_template('login_form.html', form=form, session=session, refusePrompt=refusePrompt)
    return render_template('login_form.html', form=form, session=session)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    '''
    Template generator method for the profile page.

    Sends information on the current user and their notifications as template.

    This is done by querying respective databases.
    :return:
    '''
    notifData = []
    thisProfile = []

    thisProfile.insert(0, {'username': current_user.username, 'email': current_user.email,
                           'fullName': current_user.fullName, 'institution': current_user.institution, 'password': '',
                           'commentChar': current_user.commentChar})

    # notifications = notification.query.order_by('id')
    # for instance in notifications:
    #    userInfo = db.session.query(User).filter_by(username=instance.originUser).first()
    #    if userInfo != None:
    #        notifData.insert(0, {'id': instance.id, 'name': instance.originUser, 'time': instance.timestamp,
    #                             'type': instance.type, 'username': userInfo.username, 'email': userInfo.email,
    #                             'fullName': userInfo.fullName, 'institution': userInfo.institution,
    #                             'reason': userInfo.reason})
    return render_template('profile.html', user=current_user, notifications=notifData, userProf=thisProfile)


@app.route('/updateProf', methods=['GET', 'POST'])
@login_required
def updateProf():
    '''
    Updates the current user's profile in the database with any new information they may have added.

    This is done by accepting request information (AJAX generally) and updating the User database accordingly
    :return:
    '''
    user_instance = db.session.query(User).filter_by(username=current_user.username).first()
    comChar = request.form.get('comChar', type=str)
    password = request.form.get('pass', type=str)
    email = request.form.get('email', type=str)

    if comChar != '0':
        user_instance.commentChar = comChar
    if password != '0':
        user_instance.set_password(password)
    if email != '0':
        user_instance.email = email
    db.session.commit()
    return 'Updated'


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    '''
    Template generator method for the admin page.

    Gets all sessions, files, users, and notifications.

    This is done by querying each respective sqlite database.
    Information is sent with the template to be parsed as needed by the user.
    :return:
    '''
    if current_user.isAdmin != 1:
        return redirect(url_for('index'))
    names = db.session.query(User)
    sesData = []
    fileData = []
    notifData = []
    hrmData = []
    sessions = sessionFiles.query.all()
    for instance in sessions:
        lastMod = instance.last_used
        sesData.insert(0, {'name': instance.name, 'id': instance.id, 'comment': instance.comment,
                           'authed': instance.authed,
                           'modified': lastMod})
    files = dataFile.query.order_by('id')
    for instance in files:
        fsize = size(instance.path)
        lastMod = modified(instance.path)
        temp = lastMod.strftime("%d/%m/%Y %H:%M:%S")
        modname = [instance.name + temp]
        fileData.insert(0,
                        {'name': instance.name, 'path': instance.path, 'id': instance.id, 'comment': instance.comment,
                         'authed': instance.authed, 'size': fsize, 'modified': lastMod, 'modname': modname})

    notifications = notification.query.order_by('id')
    for instance in notifications:
        userInfo = db.session.query(User).filter_by(username=instance.originUser).first()
        if userInfo != None:
            notifData.insert(0, {'id': instance.id, 'name': instance.originUser, 'time': instance.timestamp,
                                 'type': instance.type, 'username': userInfo.username, 'email': userInfo.email,
                                 'fullName': userInfo.fullName, 'institution': userInfo.institution,
                                 'reason': userInfo.reason})

    hrms = HRM.query.order_by('id')
    for instance in hrms:
        hrmData.insert(0, {'name': instance.name, 'hrm_e0': instance.hrm_e0, 'hrm_bragg1': instance.hrm_bragg1,
                           'hrm_bragg2': instance.hrm_bragg2, 'hrm_geo': instance.hrm_geo,
                           'hrm_alpha1': instance.hrm_alpha1, 'hrm_alpha2': instance.hrm_alpha2,
                           'hrm_theta1_sign': instance.hrm_theta1_sign, 'hrm_theta2_sign': instance.hrm_theta2_sign})

    return render_template('admin.html', user=current_user, fileData=fileData, sesData=sesData,
                           names=names, notifications=notifData, hrms=hrms)


@app.route('/freeze', methods=['GET', 'POST'])
@login_required
def freeze():
    '''
    Freezes the designated user's account so that they may no longer login

    This is done by setting 'aUser'.approved to be 2.

    Only accessable by admins.
    :return:
    '''
    user = request.form.get('user', type=str)
    freeze = request.form.get('freeze', type=int)
    user_instance = db.session.query(User).filter_by(username=user).first()
    if freeze == 1:
        user_instance.approved = 2
    else:
        user_instance.approved = 1
    db.session.commit()
    return 'Updated'


@app.route('/notifInfo', methods=['GET', 'POST'])
@login_required
def notifInfo():
    '''
    Supplementary template generator method for admin.

    Provides additional information about a notification.

    This is done by querying the sqlite database 'notification' based on the ID given.
    :return:
    '''
    notifID = request.form.get('id', type=int)
    notifInfo = db.session.query(notification).filter_by(id=notifID).first()
    userInfo = db.session.query(User).filter_by(username=notifInfo.originUser).first()
    userData = {'username': userInfo.username, 'email': userInfo.email,
                'fullName': userInfo.fullName, 'institution': userInfo.institution,
                'reason': userInfo.reason}
    return render_template('admin.html', user=current_user, userProf=userData)


@app.route('/hrmInfo', methods=['GET', 'POST'])
@login_required
def hrmInfo():
    '''
    Supplementary template generator method for admin.

    Provides additional information about a HRM.

    This is done by querying the sqlite database 'HRM' based on the ID given.
    :return:
    '''
    hrmID = request.form.get('id', type=int)
    hrmInfo = db.session.query(HRM).filter_by(id=hrmID).first()
    hrmData = {'name': hrmInfo.name, 'hrm_e0': hrmInfo.hrm_e0, 'hrm_bragg1': hrmInfo.hrm_bragg1,
               'hrm_bragg2': hrmInfo.hrm_bragg2, 'hrm_geo': hrmInfo.hrm_geo,
               'hrm_alpha1': hrmInfo.hrm_alpha1, 'hrm_alpha2': hrmInfo.hrm_alpha2,
               'hrm_theta1_sign': hrmInfo.hrm_theta1_sign, 'hrm_theta2_sign': hrmInfo.hrm_theta2_sign}
    return render_template('admin.html', user=current_user, hrmData=hrmData)


@app.route('/addHRM', methods=['GET', 'POST'])
@login_required
def addHRM():
    '''
    Supplementary template updater method for admin.

    Adds a HRM with the details provided by the user.

    This is done by adding a new entry in the sqlite database 'HRM'.
    :return:
    '''
    id = request.form.get('id', type=int)
    hrm = db.session.query(HRM).filter_by(id=id).first()
    if hrm is None:
        hrm = HRM()
        hrm.id = request.form.get('id', type=int)
        hrm.name = request.form.get('name', type=str)
        hrm.hrm_e0 = request.form.get('hrm_e0', type=float)
        hrm.hrm_bragg1 = request.form.get('hrm_bragg1', type=float)
        hrm.hrm_bragg2 = request.form.get('hrm_bragg2', type=float)
        hrm.hrm_geo = request.form.get('hrm_geo', type=str)
        hrm.hrm_alpha1 = request.form.get('hrm_alpha1', type=float)
        hrm.hrm_alpha2 = request.form.get('hrm_alpha2', type=float)
        hrm.hrm_theta1_sign = request.form.get('hrm_theta1_sign', type=int)
        hrm.hrm_theta2_sign = request.form.get('hrm_theta2_sign', type=int)
        db.session.add(hrm)
        db.session.commit()
    else:
        hrm.id = request.form.get('id', type=int)
        hrm.name = request.form.get('name', type=str)
        hrm.hrm_e0 = request.form.get('hrm_e0', type=float)
        hrm.hrm_bragg1 = request.form.get('hrm_bragg1', type=float)
        hrm.hrm_bragg2 = request.form.get('hrm_bragg2', type=float)
        hrm.hrm_geo = request.form.get('hrm_geo', type=str)
        hrm.hrm_alpha1 = request.form.get('hrm_alpha1', type=float)
        hrm.hrm_alpha2 = request.form.get('hrm_alpha2', type=float)
        hrm.hrm_theta1_sign = request.form.get('hrm_theta1_sign', type=int)
        hrm.hrm_theta2_sign = request.form.get('hrm_theta2_sign', type=int)
        db.session.commit()
        return 'Updated'
    return 'Added'


@app.route('/solveNotif', methods=['GET', 'POST'])
@login_required
def solveNotif():
    '''
    Resolves a notification based on the action taken.

    This is done by updating the User based on if they were accepted or not.

    Only currently setup to handle account creation requests.
    :return:
    '''
    id = request.form.get('id', type=int)
    action = request.form.get('action', type=int)
    notif = db.session.query(notification).filter_by(id=id).first()
    if action == 1:
        user = db.session.query(User).filter_by(username=notif.originUser).first()
        user.approved = 1
        db.session.delete(notif)
    else:
        db.session.delete(notif)
        user = db.session.query(User).filter_by(username=notif.originUser).first()
        db.session.delete(user)
        sessions = db.session.query(sessionFiles).filter(sessionFiles.user == user).all()
        for session in sessions:
            auths = session.authed.split(',')
            auths.remove(str(user.id))
            if len(auths) == 0:
                db.session.delete(session)
                instances = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=session.id).all()
                for instance in instances:
                    meta = db.session.query(sessionMeta).filter_by(id=instance.sessionMeta_id).first()
                    db.session.delete(meta)
                    db.session.deleta(instance)
            else:
                session.authed = ','.join(auths)
        fileIDs = db.session.query(userFiles).filter(userFiles.user_id == user.id).all()
        for id in fileIDs:
            file = db.session.query(dataFile).filter(dataFile.id == id.file_id).first()
            auths = file.authed.split(',')
            auths.remove(str(user.id))
            userFile = db.session.query(userFiles).filter(
                and_(userFiles.user_id == user.id, userFiles.file_id == file.id)).first()
            db.session.delete(userFile)
            if len(auths) == 0:
                db.session.delete(file)
            else:
                file.authed = ','.join(auths)
    db.session.commit()
    return 'Solved'


@app.route('/getInfo', methods=['GET', 'POST'])
@login_required
def getInfo():
    '''
    Supplementary template generator for the admin page.

    Provides additional information about a file/session/user

    This is done through queries on their corresponding databases.
    :return:
    '''
    table = request.form.get('table', type=str)
    id = request.form.get('id', type=int)
    user = request.form.get('user', type=str)
    fileUsers = []
    userFiles = []
    userSessions = []
    sessionUsers = []
    freeze = 0
    if table == 'File':
        file_instance = db.session.query(dataFile).filter_by(id=id).first()
        if file_instance != None:
            names = file_instance.authed.split(',')
            for name in names:
                user = db.session.query(User).filter_by(id=name).first()
                fileUsers.insert(0, {'fUser': user})
    if table == 'User':
        user = db.session.query(User).filter_by(username=user).first()
        freeze = user.approved
        files = dataFile.query.all()
        for instance in files:
            fsize = size(instance.path)
            lastMod = modified(instance.path)
            temp = lastMod.strftime("%d/%m/%Y %H:%M:%S")
            modname = [instance.name + temp]
            userFiles.insert(0,
                             {'name': instance.name, 'path': instance.path, 'id': instance.id,
                              'comment': instance.comment,
                              'authed': instance.authed, 'size': fsize, 'modified': lastMod, 'modname': modname})

        sessions = sessionFiles.query.all()
        for instance in sessions:
            lastMod = instance.last_used
            userSessions.insert(0,
                                {'name': instance.name, 'id': instance.id, 'comment': instance.comment,
                                 'authed': instance.authed, 'modified': lastMod})
    if table == 'Session':
        session_instance = db.session.query(sessionFiles).filter_by(id=id).first()
        if session_instance != None:
            names = session_instance.authed.split(',')
            for name in names:
                user = db.session.query(User).filter_by(id=name).first()
                sessionUsers.insert(0, {'sUser': user})
    return render_template('admin.html', user=user, fileUsers=fileUsers, userFiles=userFiles,
                           userSessions=userSessions, sessionUsers=sessionUsers, freeze=freeze)


@app.route('/addThing', methods=['GET', 'POST'])
@login_required
def addThing():
    '''
    Helper method for the /admin page used to add something to the user/file/session database.

    This is done by taking the ID of something that already exists in the database and updating the authentication list.
    :return:
    '''
    if request.method == 'POST':
        thing = request.form.get('id', type=str)
        location = request.form.get('from', type=str)
        table = request.form.get('table', type=str)
        user = request.form.get('user', type=str)
        if thing != None:
            user = db.session.query(User).filter_by(username=location).first()
            if table == '#userFileTable':
                instance = db.session.query(dataFile).filter_by(id=thing).first()
                auths = instance.authed.split(',')
                if user.id in auths:
                    return 'Already Shared'
                else:
                    instance.authed = instance.authed + ',' + str(user.id)
                    userFile = userFiles()
                    userFile.user_id = user.id
                    userFile.file_id = instance.id
                    db.session.add(userFile)
                    db.session.commit()
            if table == '#userSessionTable':
                instance = db.session.query(sessionFiles).filter_by(id=thing).first()
                auths = instance.authed.split(',')
                if user.id in auths:
                    return 'Already Shared'
                else:
                    instance.authed = instance.authed + ',' + str(user.id)
        else:
            user = db.session.query(User).filter_by(username=user).first()
            if table == '#fileNameTable':
                instance = db.session.query(dataFile).filter_by(id=location).first()
                auths = instance.authed.split(',')
                if user.id in auths:
                    return 'Already Shared'
                else:
                    instance.authed = instance.authed + ',' + str(user.id)
                    userFile = userFiles()
                    userFile.user_id = user.id
                    userFile.file_id = instance.id
                    db.session.add(userFile)
                    db.session.commit()
            if table == '#sessionUserTable':
                instance = db.session.query(sessionFiles).filter_by(id=location).first()
                auths = instance.authed.split(',')
                if user.id in auths:
                    return 'Already Shared'
                else:
                    instance.authed = instance.authed + ',' + str(user.id)
        db.session.commit()
        user = user.username
    return user


@app.route('/removeThing', methods=['GET', 'POST'])
@login_required
def removeThing():
    '''
    Updates the user/file/session database with a deletion as requested by the admin page

    This is done by getting information from a request and deleting the appropriate thing from the authentication list.
    If this changes leaves the authentication list empty then the thing is deleted from the database.
    :return:
    '''
    if request.method == 'POST':
        thing = request.form.get('id', type=str)
        location = request.form.get('from', type=str)
        table = request.form.get('table', type=str)
        user = request.form.get('user', type=str)
        if thing != None:
            user = db.session.query(User).filter_by(username=location).first()
            if table == '#userFileTable':
                instance = db.session.query(dataFile).filter_by(id=thing).first()
                auths = instance.authed.split(',')
                auths.remove(str(user.id))
                userFile = db.session.query(userFiles).filter(
                    and_(userFiles.user_id == user.id, userFiles.file_id == instance.id)).first()
                db.session.delete(userFile)
                db.session.commit()
                if len(auths) == 0:
                    db.session.delete(instance)
                else:
                    instance.authed = ','.join(auths)
            if table == '#userSessionTable':
                instance = db.session.query(sessionFiles).filter_by(id=thing).first()
                auths = instance.authed.split(',')
                auths.remove(str(user.id))
                if len(auths) == 0:
                    db.session.delete(instance)
                    instances = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=thing).all()
                    for instance in instances:
                        meta = db.session.query(sessionMeta).filter_by(id=instance.sessionMeta_id).first()
                        db.session.delete(meta)
                        db.session.delete(instance)
                else:
                    instance.authed = ','.join(auths)
            if table == 'HRM':
                user = db.session.query(User).filter_by(id=current_user.get_id()).first()
                instance = db.session.query(HRM).filter_by(id=thing).first()
                if instance.name == 'Fe-inline-1meV':
                    return "Request to delete base HRM denied"
                db.session.delete(instance)
        else:
            user = db.session.query(User).filter_by(username=user).first()
            if table == '#fileNameTable':
                file_instance = db.session.query(dataFile).filter_by(id=location).first()
                auths = file_instance.authed.split(',')
                auths.remove(str(user.id))
                userFile = db.session.query(userFiles).filter(
                    and_(userFiles.user_id == user.id, userFiles.file_id == file_instance.id)).first()
                db.session.delete(userFile)
                db.session.commit()
                if len(auths) == 0:
                    db.session.delete(file_instance)
                else:
                    file_instance.authed = ','.join(auths)
            if table == '#sessionUserTable':
                session_instance = db.session.query(sessionFiles).filter_by(id=location).first()
                auths = session_instance.authed.split(',')
                auths.remove(str(user.id))
                if len(auths) == 0:
                    db.session.delete(session_instance)
                    instances = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=thing).all()
                    for instance in instances:
                        meta = db.session.query(sessionMeta).filter_by(id=instance.sessionMeta_id).first()
                        db.session.delete(meta)
                        db.session.delete(instance)
                else:
                    session_instance.authed = ','.join(auths)
        db.session.commit()
        user = user.username
    return user


@app.route('/select', methods=['GET', 'POST'])
@login_required
def index():
    '''
    Template generator method for the select page.

    Sends all sessions and DAT files in a template for the user to use so long as they are authenticated.

    This is done with a database query and authenticated in view_output.html.
    :return:
    '''
    user = current_user
    data = []
    sessions = sessionFiles.query.all()
    names = db.session.query(User)
    for instance in sessions:
        lastMod = instance.last_used
        data.insert(0,
                    {'name': instance.name, 'id': instance.id, 'comment': instance.comment, 'authed': instance.authed,
                     'modified': lastMod, 'type': 'ses'})
    DATsessions = db.session.query(dataFile).filter_by(type='dat')
    for Dinstance in DATsessions:
        lastMod = modified(Dinstance.path)
        data.insert(0,
                    {'name': Dinstance.name + '.dat', 'id': Dinstance.id, 'comment': Dinstance.comment,
                     'authed': Dinstance.authed,
                     'modified': lastMod, 'type': 'dat'})
    if request.method == 'POST':
        return redirect(url_for('dataFormat'))
    return render_template('view_output.html', data=data, user=user, names=names)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    '''
    Template generator method for the upload page.

    Sends all files in a template for the user to use so long as they are authenticated.

    this is done with a database query and authenticated in upload.html.
    :return:
    '''
    user = current_user
    data = []
    files = dataFile.query.order_by('id')
    names = db.session.query(User)
    for instance in files:
        fsize = size(instance.path)
        lastMod = modified(instance.path)
        temp = lastMod.strftime("%d/%m/%Y %H:%M:%S")
        modname = [instance.name + temp]
        if instance.type == 'dat' and instance.name[-4:] != '.dat':
            instance.name = instance.name + '.dat'
        data.insert(0, {'name': instance.name, 'path': instance.path, 'id': instance.id, 'comment': instance.comment,
                        'authed': instance.authed, 'size': fsize, 'modified': lastMod, 'modname': modname})
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('upload.html', data=data, user=user, names=names)


@app.route('/logout')
@login_required
def logout():
    '''Logs out a user by clearing session information'''
    session.clear()
    return redirect(url_for('login'))


@app.route('/data', methods=['GET', 'POST'])
@login_required
def dataFormat():
    '''
    Template generator for the data page.

    Has a multitude of options that allow the user to display file information in the form of a plot.
    Options are saved to a live-updated session for each respective file that persists through temporarily leaving the page.
    Defaults are assigned to all files within this method.
    :return:
    '''
    user = current_user
    thisSession = current_user.current_session
    findPlot = request.form.get('plot', type=int)
    unit = request.form.get('unit', type=str)
    fdata = []
    hrmData = []
    nameID = str(uuid.uuid4())
    files = dataFile.query.all()
    for instance in files:
        fsize = size(instance.path)
        lastMod = modified(instance.path)
        temp = lastMod.strftime("%d/%m/%Y %H:%M:%S")
        modname = [instance.name + temp]
        if instance.type != 'dat':
            fdata.insert(0,
                         {'name': instance.name, 'path': instance.path, 'id': instance.id, 'comment': instance.comment,
                          'authed': instance.authed, 'size': fsize, 'modified': lastMod, 'modname': modname})

    hrms = HRM.query.order_by('id')
    for instance in hrms:
        hrmData.insert(0, {'name': instance.name, 'hrm_e0': instance.hrm_e0, 'hrm_bragg1': instance.hrm_bragg1,
                           'hrm_bragg2': instance.hrm_bragg2, 'hrm_geo': instance.hrm_geo,
                           'hrm_alpha1': instance.hrm_alpha1, 'hrm_alpha2': instance.hrm_alpha2,
                           'hrm_theta1_sign': instance.hrm_theta1_sign, 'hrm_theta2_sign': instance.hrm_theta2_sign})

    if findPlot != 1:
        form = InputForm(request.form)
        plt.figure(figsize=(10, 7))
        fig, ax = plt.subplots()
        mpld3.plugins.connect(fig, InteractiveLegend([], [], 0, nameID, None))
        code = mpld3.fig_to_html(fig)
        plt.clf()
        againstE = 'Point #'
    else:
        idthis = request.form.get('idnext', type=int)
        file_instance = db.session.query(dataFile).filter(dataFile.id == idthis).first()
        try:
            fpath = file_instance.path
        except AttributeError:
            flash('Please select a file')
            return redirect(url_for('dataFormat'))
        format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                    currentMeta.file_id == file_instance.id,
                                                                    currentMeta.session == current_user.current_session)).first()
        if format_instance is not None:
            againstE = format_instance.against_E
            form = populate_from_instance(format_instance)
            columns, bools = splitForm(form)
            basedColumns = zeroBaseColumns(columns)
            used = []
            additional = []
            addLabels = []
            normLabels = []
            labels = []
            if str(file_instance.type) == 'mda':
                data, name, unusedpath = readMda(file_instance.path)
            else:
                data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
            for i in range(len(bools)):
                if bools[i].data:
                    if columns[i].data == None:
                        if i == 1:
                            energy = energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                                 unicode_to_int(basedColumns[4].data), format_instance.hrm)
                            additional.append(energy)
                            addLabels.append('Energy xtal')
                            energy = numpy.divide(energy, 1000000)
                        elif i == 2:
                            energy = energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                                      unicode_to_int(basedColumns[4].data),
                                                      unicode_to_int(basedColumns[5].data),
                                                      unicode_to_int(basedColumns[6].data), format_instance.hrm)
                            additional.append(energy)
                            addLabels.append('Energy xtal w/T')
                            energy = numpy.divide(energy, 1000000)
                        elif i == 7:
                            energy = temp_corr(data, unicode_to_int(basedColumns[5].data),
                                               unicode_to_int(basedColumns[6].data), format_instance.hrm)
                            additional.append(energy)
                            addLabels.append('Temp. corr')
                        elif i == 9:
                            signal = signal_normalized(data, unicode_to_int(basedColumns[8].data),
                                                       unicode_to_int(basedColumns[10].data))
                            additional.append(signal)
                            addLabels.append('Signal Normalized')
                        else:
                            norm = norm_factors(data, unicode_to_int(basedColumns[10].data))
                            additional.append(norm)
                            addLabels.append('Normalized')
                        continue
                    else:
                        used.append(unicode_to_int(basedColumns[i].data))
                        normLabels.append(str(basedColumns[i].label.text)[:-2])
            if againstE == 'Energy':
                etype = data[unicode_to_int(basedColumns[0].data)]
            elif againstE == 'Energy xtal':
                etype = numpy.divide(energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                                 unicode_to_int(basedColumns[4].data), format_instance.hrm), 1000000)
            elif againstE == 'Energy xtal w/T':
                etype = numpy.divide(energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                                      unicode_to_int(basedColumns[4].data),
                                                      unicode_to_int(basedColumns[5].data),
                                                      unicode_to_int(basedColumns[6].data), format_instance.hrm),
                                     1000000)
            elif againstE == 'Energy Fitted':
                code, ycords, form = peakFit(idthis, format_instance.fit_energy, format_instance.fit_signal, unit,
                                             format_instance.fit_type, format_instance.fit_range,
                                             format_instance.fit_pos, format_instance.fit_localRange)
                etype = ycords[0]
            else:
                etype = 0
            labels.append(normLabels)
            labels.append(addLabels)
            code = plotData(data, used, againstE, additional, labels, etype, unit)
            format_instance.plot = code
            db.session.commit()
        else:
            if str(file_instance.type) == 'mda':
                data, name, unusedpath = readMda(file_instance.path)
            else:
                data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
            etype = data[1]
            used = []
            againstE = 'Point #'
            format = currentMeta()
            format.name = file_instance.name
            format.path = file_instance.path
            # format.ebool = True
            format.sbool = True
            format.energy = 1
            format.signal = 11
            format.xtal1A = 2
            format.xtal2A = 3
            format.xtal1T = 12
            format.xtal2T = 15
            format.norm = 7
            format.extra = 1
            format.against_E = 'Point #'
            format.fit_type = 'Unfit'
            format.fit_pos = 0
            format.fit_range = 3
            format.fit_energy = 'Energy'
            format.fit_signal = 'Signal'
            format.fit_localRange = None
            format.file_id = idthis
            format.checked = True
            hrmInstance = db.session.query(HRM).filter_by(name='Fe-inline-1meV').first()
            hrm = {'name': hrmInstance.name, 'hrm_e0': hrmInstance.hrm_e0, 'hrm_bragg1': hrmInstance.hrm_bragg1,
                   'hrm_bragg2': hrmInstance.hrm_bragg2, 'hrm_geo': hrmInstance.hrm_geo,
                   'hrm_alpha1': hrmInstance.hrm_alpha1,
                   'hrm_alpha2': hrmInstance.hrm_alpha2, 'hrm_theta1_sign': hrmInstance.hrm_theta1_sign,
                   'hrm_theta2_sign': hrmInstance.hrm_theta2_sign}
            hrm = json.dumps(hrm)
            format.hrm = hrm
            format.session = current_user.current_session
            format.user = current_user

            # used.append(1)
            used.append(10)
            labels = [['Signal']]
            code = plotData(data, used, 'Point', None, labels, etype, unit)
            format.plot = code
            db.session.add(format)
            db.session.commit()

            code = format.plot
            form = populate_from_instance(format)
    return render_template("data_format.html", user=user, code=code, form=form, againstE=againstE, data=fdata,
                           ses=thisSession, hrm=hrmData)


@app.route('/save_graph', methods=['GET', 'POST'])
@login_required
def save_graph():
    '''
    Updates the current session with information that the user has supplied on the data page.

    This session is stored temporarily for each file and is updated whenever a change is made on the data page.
    The data is passed in the InputForm that is defined in forms.py and saved in the currentMeta database table.
    :return:
    '''
    form = InputForm(request.form)
    idthis = request.form.get("idnum", type=int)
    if idthis is not None:
        againstE = request.form.get("agaE", type=str)
        file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                    currentMeta.file_id == file_instance.id,
                                                                    currentMeta.session == current_user.current_session)).first()

        format_instance.energy = form.energy.data
        format_instance.xtal1A = form.xtal1A.data
        format_instance.xtal2A = form.xtal2A.data
        format_instance.xtal1T = form.xtal1T.data
        format_instance.xtal2T = form.xtal2T.data
        format_instance.signal = form.signal.data
        format_instance.norm = form.norm.data
        format_instance.extra = form.extra.data

        format_instance.ebool = form.ebool.data
        format_instance.ecbool = form.ecbool.data
        format_instance.etcbool = form.etcbool.data
        format_instance.a1bool = form.a1bool.data
        format_instance.a2bool = form.a2bool.data
        format_instance.t1bool = form.t1bool.data
        format_instance.t2bool = form.t2bool.data
        format_instance.tcbool = form.tcbool.data
        format_instance.xtal1A = form.xtal1A.data
        format_instance.sbool = form.sbool.data
        format_instance.snbool = form.snbool.data
        format_instance.nbool = form.nbool.data
        format_instance.nfbool = form.nfbool.data
        format_instance.xbool = form.xbool.data
        format_instance.user = current_user
        format_instance.against_E = againstE

        db.session.commit()
    return 'Saved'


@app.route('/save_ses', methods=['GET', 'POST'])
@login_required
def saveSession():
    '''
    This saves the current session so that the user may resume from the select page whenever they want.

    The currentMeta table is parsed and saved into the sessionFiles and sessionFilesMeta tables for more permanence.
    A check is done to ensure that the user cannot save the session under a name that has already been created.
    :return:
    '''
    checked = request.form.get("checked", type=int)
    namechk = request.form.get("name", type=str)
    if checked == 0:
        instance = db.session.query(sessionFiles).filter(
            and_(sessionFiles.user_id == current_user.get_id(), sessionFiles.name == namechk)).first()
        if instance:
            data = str(instance.id)
            return data

    session_file = sessionFiles()
    session_file.user = current_user
    session_file.user_id == current_user.get_id()
    session_file.authed = current_user.get_id()
    session_file.name = request.form.get("name", type=str)
    session_file.comment = request.form.get("comment", type=str)
    session_file.last_used = getTime()
    db.session.add(session_file)
    db.session.commit()

    for instance in db.session.query(currentMeta).filter(currentMeta.user_id == current_user.get_id()).all():
        form = populate_from_instance(instance)
        session_instance = sessionMeta()
        form.populate_obj(session_instance)

        session_instance.file_id = instance.file_id
        session_instance.path = instance.path
        session_instance.comment = instance.comment
        session_instance.checked = instance.checked
        session_instance.against_E = instance.against_E
        session_instance.fit_type = instance.fit_type
        session_instance.fit_pos = instance.fit_pos
        session_instance.fit_range = instance.fit_range
        session_instance.hrm = instance.hrm
        session_instance.session = session_file.name
        db.session.add(session_instance)
        db.session.commit()

        session_file_instance = sessionFilesMeta()
        session_file_instance.sessionFiles_id = session_file.id
        session_file_instance.sessionMeta_id = session_instance.id

        instance.session = session_file.name

        db.session.add(session_file_instance)
        db.session.commit()
    current_user.current_session = session_file.name
    db.session.commit()
    if checked == 1:
        return current_user.current_session
    data = ({'status': 'Saved', 'name': current_user.current_session})
    sending = json.dumps(data)
    return sending


@app.route('/generateOutput', methods=['GET', 'POST'])
@login_required
def generateOutput():
    '''
    This pulls data from a request to determine which type of file needs to be generated and redirects the file to output.

    The outType that is sent from the request data determines which type of output to compile the given data into.
    If the output is being saved to the server a copy is made in app.config['UPLOAD_DIR'].  Otherwise the file is sent to /sendOut where it is downloaded to the user's computer.
    :return:
    '''
    form = InputForm(request.form)
    id = request.form.get('idnum', type=str)
    outType = request.form.get('outType', type=int)
    cordData = request.form.get('cordData', type=str)
    sesID = request.form.get('session', type=int)
    datFName = request.form.get('datFName', type=str)
    DBSave = request.form.get('DBSave', type=int)
    output = []
    colNames = []
    if outType == 1:
        file_instance = db.session.query(dataFile).filter_by(id=int(id)).first()
        format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                    currentMeta.file_id == int(id),
                                                                    currentMeta.session == current_user.current_session)).first()
        if str(file_instance.type) == 'mda':
            data, name, unusedpath = readMda(file_instance.path)
        else:
            data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
        columns, bools = splitForm(form)
        basedColumns = zeroBaseColumns(columns)
        for i in range(len(bools)):
            if bools[i].data:
                if columns[i].data == None:
                    if i == 1:
                        energy = energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                             unicode_to_int(basedColumns[4].data), format_instance.hrm)
                        output.append(energy)
                        colNames.append('Energy xtal')
                    elif i == 2:
                        energy = energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                                  unicode_to_int(basedColumns[4].data),
                                                  unicode_to_int(basedColumns[5].data),
                                                  unicode_to_int(basedColumns[6].data), format_instance.hrm)
                        output.append(energy)
                        colNames.append('Energy xtal temp')
                    elif i == 7:
                        energy = temp_corr(data, unicode_to_int(basedColumns[5].data),
                                           unicode_to_int(basedColumns[6].data), format_instance.hrm)
                        output.append(energy)
                        colNames.append('Temp Corr')
                    elif i == 9:
                        signal = signal_normalized(data, unicode_to_int(basedColumns[8].data),
                                                   unicode_to_int(basedColumns[10].data))
                        output.append(signal)
                        colNames.append('Signal Normalized')
                    else:
                        norm = norm_factors(data, unicode_to_int(basedColumns[10].data))
                        output.append(norm)
                        colNames.append('Norm Factors')
                    continue
                else:
                    for idx, column in enumerate(data):
                        if idx == basedColumns[i].data:
                            output.append(data[idx])
                            colNames.append(bools[i].label)
        filename = writeOutput(output, colNames, file_instance.name, '')
    elif outType == 2:
        file_instance = db.session.query(dataFile).filter_by(id=int(id)).first()
        cords = json.loads(cordData)
        output = []
        output.append(cords[0])
        output.append(cords[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        if datFName is not None:
            filename = writeOutput(output, colNames, datFName, '')
        else:
            filename = writeOutput(output, colNames, file_instance.name, '')
    elif outType == 3:
        jidlist = json.loads(id)
        cords = json.loads(cordData)
        output = []
        output.append(cords[0])
        output.append(cords[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        filename = writeOutput(output, colNames, jidlist, datFName)
    elif outType == 4:
        file_instance = db.session.query(dataFile).filter_by(id=int(id)).first()
        cords = json.loads(cordData)
        output = []
        output.append(cords[0])
        output.append(cords[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        filename = writeOutput(output, colNames, datFName, '')
        if DBSave != 0:
            dfile = dataFile()
            dfile.name = datFName
            dfile.path = app.config['UPLOAD_DIR'] + '/outData/' + filename
            dfile.comment = ''
            dfile.authed = current_user.get_id()
            user_instance = db.session.query(User).filter_by(id=current_user.get_id()).first()
            dfile.comChar = user_instance.commentChar
            dfile.type = 'dat'
            db.session.add(dfile)
            userFile = userFiles()
            userFile.file_id = dfile.id
            userFile.user_id = current_user.get_id()
            db.session.add(userFile)
            db.session.commit()
        with open(app.config['UPLOAD_DIR'] + '/outData/' + filename, 'r') as DATfile:
            data = DATfile.read()
        return data
    elif outType == 5:
        jidlist = json.loads(id)
        cords = json.loads(cordData)
        output = []
        output.append(cords[0])
        output.append(cords[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        filename = writeOutput(output, colNames, jidlist, datFName)
        if DBSave != 0:
            dfile = dataFile()
            dfile.name = datFName
            dfile.path = app.config['UPLOAD_DIR'] + '/outData/' + filename
            dfile.comment = ''
            dfile.authed = current_user.get_id()
            user_instance = db.session.query(User).filter_by(id=current_user.get_id()).first()
            dfile.comChar = user_instance.commentChar
            dfile.type = 'dat'
            db.session.add(dfile)
            userFile = userFiles()
            userFile.file_id = dfile.id
            userFile.user_id = current_user.get_id()
            db.session.add(userFile)
            db.session.commit()
        with open(app.config['UPLOAD_DIR'] + '/outData/' + filename, 'r') as DATfile:
            data = DATfile.read()
        return data
    elif outType == 6:
        DAT = db.session.query(currentDAT).filter(currentDAT.user_id == current_user.get_id()).first()
        output = []
        data = json.loads(DAT.DAT)
        output.append(data[0])
        output.append(data[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        filename = writeOutput(output, colNames, datFName, '')
    elif outType == 7:
        DAT = db.session.query(currentDAT).filter(currentDAT.user_id == current_user.get_id()).first()
        output = []
        data = json.loads(DAT.DAT)
        output.append(data[0])
        output.append(data[1])
        colNames = []
        colNames.append("Energy")
        colNames.append("Signal")
        filename = writeOutput(output, colNames, datFName, '')
        dfile = dataFile()
        dfile.name = datFName
        dfile.path = app.config['UPLOAD_DIR'] + '/outData/' + filename
        dfile.comment = ''
        dfile.authed = current_user.get_id()
        user_instance = db.session.query(User).filter_by(id=current_user.get_id()).first()
        dfile.comChar = user_instance.commentChar
        dfile.type = 'dat'
        db.session.add(dfile)
        userFile = userFiles()
        userFile.file_id = dfile.id
        userFile.user_id = current_user.get_id()
        db.session.add(userFile)
        db.session.commit()
        return datFName
    if datFName is not None:
        return redirect(url_for('sendOut', filename=filename, displayName=datFName))
    else:
        return redirect(url_for('sendOut', filename=filename, displayName='None'))


@app.route('/outData/<path:filename>/<displayName>', methods=['GET', 'POST'])
@login_required
def sendOut(filename, displayName):
    '''
    Sends the file to the user for doanloading using flask's send_from_directory
    :param filename:
    The absolute name of the file that is saved in the database.
    :param displayName:
    The simplistic name of the file that the user chose.
    :return:
    '''
    if displayName != 'None' and displayName is not None:
        return send_from_directory(directory=app.config['UPLOAD_DIR'] + '/outData', filename=filename,
                                   as_attachment=True, attachment_filename=displayName + '.dat')
    else:
        return send_from_directory(directory=app.config['UPLOAD_DIR'] + '/outData', filename=filename,
                                   as_attachment=True)


@app.route('/db')
@login_required
def sesData():
    '''
    Template generator for the logbook page.

    Queries the database of the loggedUser to get all instances of plots they have logged.
    :return:
    '''
    data = []
    user = current_user
    if user.is_authenticated():
        procEntry = db.session.query(logBook).filter_by(name="Process Entry").first()
        if procEntry != None:
            db.session.delete(procEntry)
            db.session.commit()
        instances = user.loggedUser.order_by(desc('id'))
        for instance in instances:
            form = populate_from_instance(instance)
            columns, bools = splitForm(form)
            plot = instance.plot
            if instance.comment:
                comment = instance.comment
            else:
                comment = ''
            try:
                json.loads(instance.name)
                data.append({'plot': plot, 'comment': comment, 'name': instance.name, 'time': instance.timestamp,
                             'ses': instance.session, 'id': instance.id})
            except ValueError:
                data.append({'form': form, 'plot': plot, 'id': instance.id, 'comment': comment, 'columns': columns,
                             'bools': bools, 'name': instance.name, 'time': instance.timestamp,
                             'ses': instance.session})
    return render_template("session.html", data=data)


@app.route('/addf', methods=['POST'])
@login_required
def addFile():
    '''
    Adds a file to the manage file page based on a file that the user selects from their local machine.

    Files are restricted to the extensions defined in ALLOWED_EXTENSIONS.  Usage of the for loop allows the user to
        shift/control click multiple files to upload simultaneously.
    After upload the files are stored in UPLOAD_DIR/rawData so that the server has its own copy to reference.
    :return:
    '''
    if request.method == 'POST':
        temp1 = request.files.listvalues()
        for file in temp1:
            file = file[0]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                pathfilename = filename + str(datetime.now())
                file.save(os.path.join((app.config['UPLOAD_DIR'] + '/rawData'), pathfilename))
                dfile = dataFile()
                dfile.name = filename
                if dfile.name[-4:] == '.dat':
                    dfile.name = dfile.name[:-4]
                sideVals = request.form.listvalues()
                dfile.comChar = sideVals[0][0]
                dfile.type = sideVals[1][0]
                dfile.path = app.config['UPLOAD_DIR'] + '/rawData/' + pathfilename
                dfile.comment = ''
                dfile.authed = current_user.get_id()
                db.session.add(dfile)
                db.session.commit()
                userFile = userFiles()
                userFile.file_id = dfile.id
                userFile.user_id = current_user.get_id()
                db.session.add(userFile)
                db.session.commit()
    return 'Added'


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_file():
    '''
    General delete function that is used for deleting entries from the database.

    Files, metadata, sessions, and users are all deleted in this function.
    The authentication list is updated if there are still users that need to have access to the session/file after a deletion is made.
    :return:
    '''
    if request.method == 'POST':
        idnum = request.form.get('id', type=int)
        delUser = request.form.get('delUser', type=str)
        table = request.form.get('table', type=str)
        user = current_user
        if table == 'File':
            instance = db.session.query(dataFile).filter_by(id=idnum).first()
            auths = instance.authed.split(',')
            auths.remove(str(user.id))
            temp = db.session.query(userFiles).all()
            userFile = db.session.query(userFiles).filter(
                and_(userFiles.user_id == user.id, userFiles.file_id == instance.id)).first()
            db.session.delete(userFile)
            db.session.commit()
            if len(auths) == 0:
                db.session.delete(instance)
            else:
                instance.authed = ','.join(auths)
        if table == 'Meta':
            instance = user.logBook.filter_by(id=idnum).first()
            db.session.delete(instance)
        if table == 'Session':
            instance = db.session.query(sessionFiles).filter_by(id=idnum).first()
            auths = instance.authed.split(',')
            auths.remove(str(user.id))
            if len(auths) == 0:
                db.session.delete(instance)
                instances = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=idnum).all()
                for instance in instances:
                    meta = db.session.query(sessionMeta).filter_by(id=instance.sessionMeta_id).first()
                    db.session.delete(meta)
                    db.session.delete(instance)
            else:
                instance.authed = ','.join(auths)
        if table == 'User':
            user_instance = db.session.query(User).filter_by(username=delUser).first()
            sessions = db.session.query(sessionFiles).filter(sessionFiles.user_id == user_instance.id).all()
            for session in sessions:
                auths = session.authed.split(',')
                auths.remove(str(user_instance.id))
                if len(auths) == 0:
                    db.session.delete(session)
                    instances = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=session.id).all()
                    for instance in instances:
                        meta = db.session.query(sessionMeta).filter_by(id=instance.sessionMeta_id).first()
                        db.session.delete(meta)
                        db.session.delete(instance)
                else:
                    session.authed = ','.join(auths)
            fileIDs = db.session.query(userFiles).filter(userFiles.user_id == user_instance.id).all()
            for id in fileIDs:
                file = db.session.query(dataFile).filter(dataFile.id == id.file_id).first()
                auths = file.authed.split(',')
                auths.remove(str(user_instance.id))
                userFile = db.session.query(userFiles).filter(
                    and_(userFiles.user_id == user_instance.id, userFiles.file_id == file.id)).first()
                db.session.delete(userFile)
                if len(auths) == 0:
                    db.session.delete(file)
                else:
                    file.authed = ','.join(auths)
            db.session.delete(user_instance)
        db.session.commit()
    return 'Deleted'


@app.route('/save_comment', methods=['GET', 'POST'])
@login_required
def save_comment():
    '''
    General function that is called when saving any type of comment.

    Session comments, file comments, and DAT comments are all saved here.  Generally this function is called upon navigating away from the comment box.

    ***There is currently the issue that if a user is commenting a shared file/session while a different user also
    commenting the same shared file/session the comment that is saved belongs to the user that navigated away last.
    Not sure hot to fix this issue without an immense amount of work.***
    :return:
    '''
    if request.method == 'POST':
        comment = request.form.get('comment', type=str)
        idprev = request.form.get('idprev', type=int)
        formatting = request.form.get('format', type=int)
        if idprev is not None and formatting is None:
            instance = db.session.query(dataFile).filter_by(id=idprev).first()
            instance.comment = comment
            db.session.commit()
        elif idprev is not None and formatting == 1:
            instance = db.session.query(dataFile).filter_by(id=idprev).first()
            format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                        currentMeta.file_id == instance.id,
                                                                        currentMeta.session == current_user.current_session)).first()
            if format_instance is None:
                instance.comment = comment
            else:
                format_instance.comment = comment
            db.session.commit()
        elif idprev is not None and formatting == 2:
            instance = db.session.query(sessionFiles).filter_by(id=idprev).first()
            instance.comment = comment
            db.session.commit()
        elif formatting == 3:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            instance = db.session.query(dataFile).filter_by(id=DAT.file_id).first()
            if instance is not None:
                instance.comment = comment
                db.session.commit()
    return 'Saved'


@app.route('/show_comment', methods=['GET', 'POST'])
@login_required
def show_comment():
    '''
    General function that is called when showing any comment.

    This function is usually called when a user selects something that has a comment associated with it.
    Similar to save_comment this function is used for all types of comments.
    :return:
    '''
    if request.method == 'POST':
        send_comment = ''
        idnext = request.form.get('idnext', type=int)
        formatting = request.form.get('format', type=int)
        usingSes = request.form.get('ses', type=int)
        if idnext is not None and formatting is None:
            instance = db.session.query(dataFile).filter_by(id=idnext).first()
            if instance is not None:
                send_comment = instance.comment
        if idnext is not None and formatting == 1:
            if usingSes != 1:
                setBaseComment(idnext)
            instance = db.session.query(dataFile).filter_by(id=idnext).first()
            format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                        currentMeta.file_id == instance.id,
                                                                        currentMeta.session == current_user.current_session)).first()
            if format_instance is None:
                send_comment = instance.comment
            elif format_instance.comment is not None:
                send_comment = format_instance.comment
            else:
                setBaseComment(idnext)
                instance = db.session.query(dataFile).filter_by(id=idnext).first()
                format_instance = db.session.query(currentMeta).filter(
                    and_(currentMeta.user_id == current_user.get_id(),
                         currentMeta.file_id == instance.id,
                         currentMeta.session == current_user.current_session)).first()
                send_comment = format_instance.comment
        if idnext is not None and formatting == 2:
            instance = db.session.query(sessionFiles).filter_by(id=idnext).first()
            if instance is not None:
                send_comment = instance.comment
        if formatting == 3:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            instance = db.session.query(dataFile).filter_by(id=DAT.file_id).first()
            if instance is not None:
                send_comment = instance.comment
        return send_comment
    return 'Holder'


@app.route('/make_name', methods=['GET', 'POST'])
@login_required
def make_name():
    '''
    This function takes a file by id and returns the name assigned to it.

    This is needed as otherwise the entire filename would be displayed to users with the extensive datetime at the end.
    :return:
    '''
    if request.method == 'POST':
        idthis = request.form.get('id', type=int)
        idlist = json.loads(request.form.get('ids', type=str))
        if idthis:
            instance = db.session.query(dataFile).filter_by(id=idthis).first()

            format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                        currentMeta.file_id == instance.id,
                                                                        currentMeta.session == current_user.current_session)).first()
            return json.dumps([instance.name, format_instance.checked])
        else:
            names = []
            for id in idlist:
                instance = db.session.query(dataFile).filter_by(id=id).first()
                temp = db.session.query(currentMeta).all()
                format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                            currentMeta.file_id == instance.id,
                                                                            currentMeta.session == current_user.current_session)).first()
                names.append([instance.name, format_instance.checked, id])
            return json.dumps(names)
    return 'Made'


@app.route('/del_entry', methods=['GET', 'POST'])
@login_required
def delete_entry():
    '''
    Simple delete function for the logbook.

    This function handles both mass deletion and singular deletion from the logbook.

    *Should probably be moved to within /delete*
    :return:
    '''
    user = current_user
    if request.method == 'POST':
        idthis = request.form.get('id', type=int)
        if idthis == -1:
            userBook = db.session.query(logBook).filter_by(user=user)
            for instance in userBook:
                db.session.delete(instance)
        else:
            instance = db.session.query(logBook).filter_by(id=idthis).first()
            db.session.delete(instance)
        db.session.commit()
    return 'Deleted'


@app.route('/add_entry', methods=['GET', 'POST'])
@login_required
def add_entry():
    '''
    Adds an entry to the logbook.

    This function handles standard logging from the format page and the logs from the sum page.
    Data is pulled from the user's currentMeta to log relevant information to the table.
    :return:
    '''
    user = current_user
    if request.method == 'POST':
        process = request.form.get('process', type=int)
        if process != None:
            meta = logBook()
            meta.user = user
            meta.plot = db.session.query(logBook).filter_by(name="Process Entry").first().plot
            files = []
            for instance in db.session.query(currentMeta).filter(currentMeta.user == current_user).all():
                fintance = db.session.query(dataFile).filter_by(id=instance.file_id).first()
                files.append(fintance.name)
            files = json.dumps(files)
            meta.name = files
            meta.timestamp = getTime()
            meta.session = current_user.current_session
            db.session.add(meta)
            db.session.commit()
            return 'Added'
        idthis = request.form.get('id', type=int)
        file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                    currentMeta.file_id == file_instance.id,
                                                                    currentMeta.session == current_user.current_session)).first()
        if format_instance != None:
            form = populate_from_instance(format_instance)
            meta = logBook()
            form.populate_obj(meta)
            meta.user = user
            meta.plot = format_instance.plot
            meta.comment = format_instance.comment
            meta.name = file_instance.name
            meta.timestamp = getTime()
            meta.session = current_user.current_session
            db.session.add(meta)
            db.session.commit()
    return 'Added'


@app.route('/clear_rowa', methods=['GET', 'POST'])
@login_required
def clear_rowa_wrapper():
    '''Simple function to clear the run_once_with_args decorator for loading the base comments of files.'''
    setBaseComment(-1)
    return 'Cleared'


@app.route('/clear_cmeta', methods=['GET', 'POST'])
@login_required
def clear_cmeta():
    '''
    Function that clears the current user's currentMeta Table.

    This is usually called when starting a new session or resuming an old one so that prexisting data does not cause conflicts.
    :return:
    '''
    current_user.current_session = 'None'
    deleting = db.session.query(currentMeta).filter(currentMeta.user_id == current_user.get_id()).all()
    for i in deleting:
        db.session.delete(i)
    deleting = db.session.query(currentDAT).filter(currentDAT.user_id == current_user.get_id()).all()
    for i in deleting:
        db.session.delete(i)
    db.session.commit()
    return 'Cleared'


@app.route('/clearPart_cmeta', methods=['GET', 'POST'])
@login_required
def clearPart_cmeta():
    '''
    Function that deletes a single file from the current users currentMeta table.

    This is called when removing a file on the format page.
    :return:
    '''
    idthis = request.form.get('id', type=int)
    if idthis in usedArgs:
        usedArgs.remove(idthis)
    deleting = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                         currentMeta.file_id == idthis,
                                                         currentMeta.session == current_user.current_session)).first()
    db.session.delete(deleting)
    db.session.commit()
    temp = db.session.query(currentMeta).all()
    return 'Cleared'


@app.route('/set_ses', methods=['GET', 'POST'])
@login_required
def set_ses():
    '''
    Function that updates currentMeta/currentDAT based on which type of session is selected by the user.

    By setting these tables the user is then able to view/alter the information on the corresponding tabs.
    :return:
    '''
    if request.method == 'POST':
        files = []
        sesID = request.form.get('id', type=int)
        type = request.form.get('type', type=str)
        if type == 'dat':
            dat = db.session.query(dataFile).filter_by(id=sesID).first()
            with open(dat.path, 'r') as DATfile:
                data = DATfile.read()
                cDAT = currentDAT()
                cDAT.user = current_user
                cDAT.file_id = dat.id
                xs = []
                ys = []
                user = db.session.query(User).filter_by(username=current_user.username).first()
                data = data.split("\n")
                try:
                    data = [x for x in data if not x.startswith(user.commentChar)]
                except TypeError:
                    data = [x for x in data if not x.startswith('#')]
                    flash('No comment preference set, defaulting to #')
                for i in data:
                    if not i:
                        continue
                    line = i.split()
                    xs.append(float(line[0]))
                    ys.append(float(line[1]))
                DAT = [xs, ys]
                DAT = json.dumps(DAT)
                cDAT.DAT = DAT
                cDAT.originDAT = DAT
                if dat.name is not None:
                    cDAT.DATname = dat.name
                db.session.add(cDAT)
                db.session.commit()
            return 'Saved'
        allSes = db.session.query(sessionFiles).filter_by(id=sesID).first()
        metas = db.session.query(sessionFilesMeta).filter_by(sessionFiles_id=sesID).all()
        for meta in metas:
            actualMeta = db.session.query(sessionMeta).filter_by(id=meta.sessionMeta_id).first()
            form = populate_from_instance(actualMeta)
            newCurrent = currentMeta()
            form.populate_obj(newCurrent)
            newCurrent.path = actualMeta.path
            newCurrent.comment = actualMeta.comment
            newCurrent.checked = actualMeta.checked
            newCurrent.against_E = actualMeta.against_E
            newCurrent.file_id = actualMeta.file_id
            newCurrent.fit_type = actualMeta.fit_type
            newCurrent.fit_pos = actualMeta.fit_pos
            newCurrent.fit_range = actualMeta.fit_range
            newCurrent.hrm = actualMeta.hrm
            newCurrent.user = current_user
            newCurrent.session = allSes.name
            db.session.add(newCurrent)
            db.session.commit()

            files.append(newCurrent.file_id)
        current_user.current_session = allSes.name
        db.session.commit()
        data = json.dumps(files)
        return data
    return 'Set'


@app.route('/close_plots', methods=['GET', 'POST'])
@login_required
def close_plots():
    '''
    Closes all existing plots.

    As the program is generating a large number of plots quite regularly this is a function to easily allow them to be closed.
    :return:
    '''
    if request.method == 'POST':
        plt.close("all")
    return 'Closed'


@app.route('/process', methods=['GET', 'POST'])
@login_required
def process():
    '''
    Large function that uses the peakfit settings saved to each file to peak fit and sum all of the files the user has in their currentMeta.

    Summing can be done with a binning or interpolation method.  Maxes are extracted the same either way.
    :return:
    '''
    user = current_user
    idthis = request.form.get('idnext', type=int)
    idlist = request.form.get('idList', type=str)
    pltLeg = request.form.get('pltLeg', type=int)
    binWidth = request.form.get('binWidth', type=float)
    output = request.form.get('output', type=int)
    endmax = 'No File Selected'
    senddata = []
    allFileNames = []
    outputs = ''
    if idthis is not None or idlist is not None:
        if idlist is None:
            file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
            try:
                fid = file_instance.id
            except AttributeError:
                flash('Please select a file')
                return redirect(url_for('waitProc'))
            format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                        currentMeta.file_id == file_instance.id,
                                                                        currentMeta.session == current_user.current_session)).first()
            againstE = format_instance.against_E
            form = populate_from_instance(format_instance)
            columns, bools = splitForm(form)
            basedColumns = zeroBaseColumns(columns)
            used = []
            additional = []
            legendNames = []
            endmax = []
            allFileNames = []
            if str(file_instance.type) == 'mda':
                data, name, unusedpath = readMda(file_instance.path)
            else:
                data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
            fitType = format_instance.fit_type
            if fitType == 'Unfit':
                used.append(unicode_to_int(basedColumns[0].data))
                legendNames.append(basedColumns[0].id)
                used.append(unicode_to_int(basedColumns[8].data))
                legendNames.append(basedColumns[8].id)
            else:
                if bools[1].data:
                    energy = energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                         unicode_to_int(basedColumns[4].data),
                                         format_instance.hrm)
                    additional.append(energy)
                    legendNames.append(basedColumns[1].id)
                elif bools[2].data:
                    energy = energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                              unicode_to_int(basedColumns[4].data),
                                              unicode_to_int(basedColumns[5].data),
                                              unicode_to_int(basedColumns[6].data), format_instance.hrm)
                    additional.append(energy)
                    legendNames.append(basedColumns[2].id)
                else:
                    used.append(unicode_to_int(basedColumns[0].data))
                    legendNames.append(basedColumns[0].id)
                if bools[9].data:
                    signal = signal_normalized(data, unicode_to_int(basedColumns[8].data),
                                               unicode_to_int(basedColumns[10].data))
                    additional.append(signal)
                    legendNames.append(basedColumns[9].id)
                else:
                    used.append(unicode_to_int(basedColumns[8].data))
                    legendNames.append(basedColumns[8].id)
            max, xmax, ycords = convert_Numpy(used, data, additional)
            inputCord = format_instance.fit_pos
            fitRange = format_instance.fit_range
            if fitType == 'AtMax' or fitType == 'Unfit':
                temp = xmax[1]
                xmax[1] = (ycords[0][xmax[1]] * 1000000)
                npXcords = numpy.array(ycords[0])
                npXcords = numpy.multiply(npXcords, 1000000)
                center = atMax(ycords, npXcords, xmax, fitRange)
                xmax[1] = temp
                ycords[0] = numpy.multiply(ycords[0], 1000000)
                moveXcords(ycords, center)
                format_instance.fit_type = 'AtMax'
                format_instance.fit_pos = center
                format_instance.fit_range = fitRange
                db.session.commit()
            else:
                ycords[0] = numpy.multiply(ycords[0], 1000000)
                moveXcords(ycords, inputCord)
            endmax.append([format(max[0], '.6f'), format(max[1], '.6f')])
            allFileNames.append(file_instance.name)
            if output == 1:
                outputData = []
                outputData.append(ycords[0].tolist())
                outputData.append(ycords[1])
                outputs = json.dumps(outputData)
            code = simplePlot(ycords, xmax, file_instance.name, legendNames, pltLeg, 1)
        if idthis is None:
            jidlist = json.loads(idlist)
            alldata = []
            allxmax = []
            allycords = []
            allagainstE = []
            allLegendNames = []
            allFileNames = []
            endmax = []

            for anID in jidlist:
                file_instance = db.session.query(dataFile).filter_by(id=anID).first()
                used = []
                try:
                    fid = file_instance.id
                except AttributeError:
                    flash('Unable to find file')
                    return redirect(url_for('waitProc'))
                format_instance = db.session.query(currentMeta).filter(
                    and_(currentMeta.user_id == current_user.get_id(),
                         currentMeta.file_id == file_instance.id,
                         currentMeta.session == current_user.current_session)).first()
                againstE = format_instance.against_E
                form = populate_from_instance(format_instance)
                columns, bools = splitForm(form)
                basedColumns = zeroBaseColumns(columns)
                if str(file_instance.type) == 'mda':
                    data, name, unusedpath = readMda(file_instance.path)
                else:
                    data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
                if bools[1].data:
                    energy = energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                         unicode_to_int(basedColumns[4].data),
                                         format_instance.hrm)
                    used.append(energy)
                elif bools[2].data:
                    energy = energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                              unicode_to_int(basedColumns[4].data),
                                              unicode_to_int(basedColumns[5].data),
                                              unicode_to_int(basedColumns[6].data), format_instance.hrm)
                    used.append(energy)
                else:
                    used.append(unicode_to_int(basedColumns[0].data))
                if bools[9].data:
                    signal = signal_normalized(data, unicode_to_int(basedColumns[8].data),
                                               unicode_to_int(basedColumns[10].data))
                    used.append(signal)
                    allLegendNames.append(basedColumns[9].id)
                else:
                    used.append(unicode_to_int(basedColumns[8].data))
                    allLegendNames.append(basedColumns[8].id)
                max, xmax, ycords = convert_Numpy(used, data, None)
                fitType = format_instance.fit_type
                inputCord = format_instance.fit_pos
                fitRange = format_instance.fit_range
                if fitType == 'AtMax' or fitType == 'Unfit':
                    xmaxHold = xmax[1]
                    xmax[1] = (ycords[0][xmax[1]] * 1000000)
                    npXcords = numpy.array(ycords[0])
                    npXcords = numpy.multiply(npXcords, 1000000)
                    center = atMax(ycords, npXcords, xmax, fitRange)
                    xmax[1] = xmaxHold
                    ycords[0] = npXcords
                    moveXcords(ycords, center)
                    format_instance.fit_type = 'AtMax'
                    format_instance.fit_pos = center
                    format_instance.fit_range = fitRange
                    db.session.commit()
                else:
                    npXcords = numpy.array(ycords[0])
                    npXcords = numpy.multiply(npXcords, 1000000)
                    ycords[0] = npXcords
                    moveXcords(ycords, inputCord)
                max[0] = ((max[0] * 1000000) - format_instance.fit_pos)
                endmax.append([format(max[0], '.6f'), format(max[1], '.6f')])
                alldata.append(data)
                allxmax.append(xmax)
                allycords.append(ycords)
                allagainstE.append(againstE)
                allFileNames.append(file_instance.name)
            if binWidth == None:
                code, sumxmax, sumymax, sumX, sumY = mergePlots(allycords, allxmax, allagainstE, alldata,
                                                                allLegendNames,
                                                                allFileNames, pltLeg)
                sumX = sumX.tolist()
                sumY = sumY.tolist()
            else:
                code, sumxmax, sumymax, sumX, sumY = mergeBin(allycords, allxmax, allagainstE, alldata, allLegendNames,
                                                              allFileNames,
                                                              pltLeg, binWidth)
            if output == 1:
                outputs = []
                outputs.append(sumX)
                outputs.append(sumY)
                outputs = json.dumps(outputs)
            endmax.append([format(sumxmax, '.6f'), format(sumymax, '.6f')])
            allFileNames.append('Summed Files')
    else:
        fig = plt.figure(figsize=(15, 10))
        code = mpld3.fig_to_html(fig)
    procEntry = db.session.query(logBook).filter_by(name="Process Entry").first()
    if procEntry != None:
        procEntry.plot = code
        db.session.commit()
    else:
        processEntry = logBook()
        processEntry.name = "Process Entry"
        processEntry.plot = code
        processEntry.user = user
        db.session.add(processEntry)
        db.session.commit()
    senddata.append({'max': endmax, 'filenames': allFileNames})
    return render_template("data_process.html", user=user, ses=current_user.current_session, code=code, data=senddata, outputs=outputs)


@app.route('/peakFit', methods=['GET', 'POST'])
@login_required
def peak_at_max():
    '''
    Peak fitting function that uses either the file defaults or what the user has done to the file on the format page.

    Currently peak fitting is done using a centroid analysis.  All files are peak fitted before being summed up on the sum page.
    :return:
    '''
    idthis = request.form.get('idnum', type=int)
    fitType = request.form.get('fitType', type=str)
    inputCord = request.form.get('inputCord', type=float)
    fitRange = request.form.get('inputRange', type=float)
    localRange = request.form.get('localRange', type=float)
    sendOut = request.form.get('sendOut', type=int)
    signalType = ' '.join(request.form.get('signal', type=str).split())
    energyType = ' '.join(request.form.get('energy', type=str).split())
    unit = request.form.get('unit', type=str)
    code, ycords, form = peakFit(idthis, energyType, signalType, unit, fitType, fitRange, inputCord, localRange)
    if sendOut == 1:
        ycords[0] = ycords[0].tolist()
        return json.dumps(ycords)
    return render_template("data_format.html", user=current_user, ses=current_user.current_session, code=code,
                           form=form,
                           shiftVal=str(abs(ycords[0][0])))


@app.route('/modifyDAT', methods=['GET', 'POST'])
@login_required
def modifyDAT():
    '''
    Template function for the modifyDAT page.

    Essentially just plotting the DAT information stored in the user's currentDAT.

    Must have generated a DAT file via either a DAT session being loaded or summing data on the sum page.
    :return:
    '''
    try:
        DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
    except Exception, e:
        code = 'No DAT selected'
        return render_template("modifyDAT.html", user=current_user, ses=current_user.current_session, code=code)
    if DAT == None:
        code = 'No DAT selected'
        return render_template("modifyDAT.html", user=current_user, ses=current_user.current_session, code=code)
    user = db.session.query(User).filter_by(username=current_user.username).first()
    fig = plt.figure(figsize=(10, 7))
    css = """
    .legend-box{
        cursor: pointer;
    }
    """
    xs = []
    ys = []
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    fig, ax = plt.subplots()
    data = json.loads(DAT.DAT)
    xs = data[0]
    ys = data[1]
    line = ax.plot(xs, ys, alpha=0, label='Summed')
    lines.append(line[0])
    labels.append('Summed')
    mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 1, nameID, css))
    mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return render_template("modifyDAT.html", user=current_user, ses=DAT.DATname, code=code)


@app.route('/setDAT', methods=['GET', 'POST'])
@login_required
def setDAT():
    '''
    Updates the current DAT file that the user is viewing with a DAT file that was selected.

    This is usually called from the /select page when choosing a DAT file.

    Sets the user's currentDAT.
    :return:
    '''
    DAT = request.form.get('DAT', type=str)
    DName = request.form.get('DName', type=str)
    meta = db.metadata
    for table in (meta.sorted_tables):
        if table.name == 'currentDAT':
            db.session.execute(table.delete())
    db.session.commit()

    cDAT = currentDAT()
    cDAT.user = current_user
    xs = []
    ys = []
    user = db.session.query(User).filter_by(username=current_user.username).first()
    data = DAT.split("\n")
    try:
        data = [x for x in data if not x.startswith(user.commentChar)]
    except TypeError:
        data = [x for x in data if not x.startswith('#')]
    for i in data:
        if not i:
            continue
        line = i.split()
        xs.append(float(line[0]))
        ys.append(float(line[1]))
    DAT = [xs, ys]
    DAT = json.dumps(DAT)
    cDAT.DAT = DAT
    cDAT.originDAT = DAT
    if DName is not None:
        cDAT.DATname = DName
    db.session.add(cDAT)
    db.session.commit()
    return 'Set'


@app.route('/remBackDAT', methods=['GET', 'POST'])
@login_required
def remBackDAT():
    '''
    Removes the background data from a DAT file based on user specifications.

    Either removes a flat value, a linear value, or a averaged linear value from the DAT data stored in currentDAT.

    Updates currentDAT with the data for the new line.
    :return:
    Calls /modifyDAT as that will plot the altered currentDAT.
    '''
    show = request.form.get('show', type=int)
    flatVal = request.form.get('flatVal', type=int)
    if flatVal != None:
        if show == 0:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            data = json.loads(DAT.DAT)
            for i in range(len(data[1])):
                data[1][i] = data[1][i] - flatVal
            DAT.DAT = json.dumps(data)
            db.session.commit()
            return redirect(url_for('modifyDAT'))
        else:
            DAT = db.session.query(currentDAT).one()
            data = json.loads(DAT.DAT)
            code = addLines(data, flatVal)
            return code
    leftX = request.form.get('leftX', type=float)
    leftY = request.form.get('leftY', type=float)
    rightX = request.form.get('rightX', type=float)
    rightY = request.form.get('rightY', type=float)
    if leftX != None:
        if show == 0:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            data = json.loads(DAT.DAT)
            xs = numpy.array([leftX, rightX])
            ys = numpy.array([leftY, rightY])
            slope, intercept = numpy.polyfit(xs, ys, 1)
            tempX = []
            tempY = []
            for i in range(len(data[0])):
                if data[0][i] > leftX and data[0][i] < rightX:
                    tempX.append(data[0][i])
                    tempY.append(data[1][i])
            data[0] = tempX
            data[1] = tempY
            for i in range(len(data[1])):
                data[1][i] = data[1][i] - abs((slope * data[0][i]) + intercept)
            DAT.DAT = json.dumps(data)
            db.session.commit()
            return redirect(url_for('modifyDAT'))
        else:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            data = json.loads(DAT.DAT)
            code = addLines(data, [leftX, rightX, leftY, rightY])
            return code
    leftIn = request.form.get('leftIn', type=int)
    rightIn = request.form.get('rightIn', type=int)
    if leftIn != None:
        if show == 0:
            cords = calcAverageBack(leftIn, rightIn)
            leftSlope, leftIntercept = numpy.polyfit(numpy.array([cords[0], cords[4]]),
                                                     numpy.array([cords[1], cords[5]]), 1)
            middleSlope, middleIntercept = numpy.polyfit(numpy.array([cords[4], cords[2]]),
                                                         numpy.array([cords[5], cords[3]]), 1)
            rightSlope, rightIntercept = numpy.polyfit(numpy.array([cords[2], cords[6]]),
                                                       numpy.array([cords[3], cords[7]]), 1)
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            data = json.loads(DAT.DAT)
            tempX = []
            tempY = []
            for i in range(len(data[0])):
                if data[0][i] > leftIn and data[0][i] < rightIn:
                    tempX.append(data[0][i])
                    tempY.append(data[1][i])
            data[0] = tempX
            data[1] = tempY
            for i in range(len(data[1])):
                if data[0][i] <= cords[4]:
                    data[1][i] = data[1][i] - abs((leftSlope * data[0][i]) + leftIntercept)
                elif data[0][i] <= cords[2]:
                    data[1][i] = data[1][i] - abs((middleSlope * data[0][i] + middleIntercept))
                else:
                    data[1][i] = data[1][i] - abs((rightSlope * data[0][i] + rightIntercept))
            DAT.DAT = json.dumps(data)
            db.session.commit()
            return redirect(url_for('modifyDAT'))
        else:
            DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
            data = json.loads(DAT.DAT)
            cords = calcAverageBack(leftIn, rightIn)
            code = addLines(data, cords)
            leftX = ("%.4f" % cords[5])
            rightX = ("%.4f" % cords[6])
            data = json.dumps([code, leftX, rightX])
            return data
    return redirect(url_for('modifyDAT'))


@app.route('/resetDAT', methods=['GET', 'POST'])
@login_required
def resetDAT():
    '''Reverts the currentDAT back to how it was originally'''
    DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
    DAT.DAT = DAT.originDAT
    db.session.commit()
    return redirect(url_for('modifyDAT'))


@app.route('/updateHRM', methods=['GET', 'POST'])
@login_required
def updateHRM():
    '''
    Sets the HRM to one of the static parameter sets in the HRM database

    HRM is used primarily with energy_xtal, energy_xtal_temp, and temp_corr on the /format page.
    :return:
    '''
    idthis = request.form.get('idnum', type=int)
    hrm = request.form.get('hrm', type=str)
    format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                currentMeta.file_id == idthis,
                                                                currentMeta.session == current_user.current_session)).first()
    hrmInstance = db.session.query(HRM).filter_by(name=hrm).first()
    hrm = {'name': hrmInstance.name, 'hrm_e0': hrmInstance.hrm_e0, 'hrm_bragg1': hrmInstance.hrm_bragg1,
           'hrm_bragg2': hrmInstance.hrm_bragg2, 'hrm_geo': hrmInstance.hrm_geo, 'hrm_alpha1': hrmInstance.hrm_alpha1,
           'hrm_alpha2': hrmInstance.hrm_alpha2, 'hrm_theta1_sign': hrmInstance.hrm_theta1_sign,
           'hrm_theta2_sign': hrmInstance.hrm_theta2_sign}
    hrm = json.dumps(hrm)
    format_instance.hrm = hrm
    db.session.commit()
    return hrmInstance.name


@app.route('/updateSumCheck', methods=['GET', 'POST'])
@login_required
def updateSumCheck():
    '''
    Updates the current meta to keep track of the checkbox associated with adding the file to the sum.
    :return:
    '''
    idthis = request.form.get('id', type=int)
    checkVal = request.form.get('check').lower() == "true"
    format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                currentMeta.file_id == idthis,
                                                                currentMeta.session == current_user.current_session)).first()
    format_instance.checked = checkVal
    db.session.commit()
    return 'Updated'


@app.route('/shareSes', methods=['GET', 'POST'])
@login_required
def shareSes():
    '''
    Shares a session with another user.

    Similar to the admin sharing feature, but for users.

    *Should probably be implemented with other sharing features*
    :return:
    '''
    idthis = request.form.get('id', type=int)
    shareUser = request.form.get('toUser', type=str)
    type = request.form.get('type', type=str)
    thisUser = db.session.query(User).filter_by(username=shareUser).first()
    toAuth = thisUser.id
    if type == 'dat':
        dat_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        auths = dat_instance.authed.split(',')
        if toAuth in auths:
            return 'Already Shared'
        else:
            dat_instance.authed = dat_instance.authed + ',' + str(toAuth)
            userFile = userFiles()
            userFile.file_id = idthis
            userFile.user_id = thisUser.id
            db.session.add(userFile)
            db.session.commit()
    else:
        session_instance = db.session.query(sessionFiles).filter_by(id=idthis).first()
        auths = session_instance.authed.split(',')
        if toAuth in auths:
            return 'Already Shared'
        else:
            session_instance.authed = session_instance.authed + ',' + str(toAuth)
            db.session.commit()
    return 'Shared'


@app.route('/shareFile', methods=['GET', 'POST'])
@login_required
def shareFile():
    '''
    Shares a file with another user.

    Similar to the admin sharing feature, but for users.

    *Should probably be implemented with other sharing features*
    :return:
    '''
    idthis = request.form.get('id', type=int)
    shareUser = request.form.get('toUser', type=str)
    thisUser = db.session.query(User).filter_by(username=shareUser).first()
    toAuth = thisUser.id
    file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
    auths = file_instance.authed.split(',')
    if toAuth in auths:
        return 'Already Shared'
    else:
        file_instance.authed = file_instance.authed + ',' + str(toAuth)
        userFile = userFiles()
        userFile.file_id = idthis
        userFile.user_id = thisUser.id
        db.session.add(userFile)
        db.session.commit()
    return 'Shared'


@app.route('/headerFile', methods=['GET', 'POST'])
@login_required
def headerFile():
    idthis = request.form.get('id', type=int)
    file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
    header = getHeader(file_instance.name, file_instance.path)
    return json.dumps(header)


@app.route('/linkGlobus', methods=['GET', 'POST'])
@login_required
def linkGlobus():
    '''
    client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    #client.oauth2_start_flow(refresh_tokens=True)
    client.oauth2_start_flow()
    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))
    get_input = getattr(__builtins__, 'raw_input', input)
    auth_code = get_input('Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)
    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    AUTH_TOKEN = globus_auth_data['access_token']
    TRANSFER_TOKEN = globus_transfer_data['access_token']
    TRANSFER_REFRESH = globus_transfer_data['refresh_token']
    TRANSFER_EXP = globus_transfer_data['expires_at_seconds']
    #authorizer = globus_sdk.RefreshTokenAuthorizer(TRANSFER_REFRESH, client, access_token=TRANSFER_TOKEN, expires_at=TRANSFER_EXP)
    authorizer = globus_sdk.AccessTokenAuthorizer(access_token=TRANSFER_TOKEN)
    tc = globus_sdk.TransferClient(authorizer=authorizer)
    petrel = 'e890db9e-8182-11e5-993f-22000b96db58'
    ep = tc.get_endpoint(petrel)
    epResult = tc.endpoint_autoactivate(petrel)
    r = tc.operation_ls(petrel, path='/')
    for item in r:
        print("{}: {} [{}]".format(item["type"], item["name"], item["size"]))
    return 'Linked'
    '''
    '''
    api = getApi('caschmitz', 'password')
    print api.endpoint_ls('petrel#sdm')
    code, reason, result = api.endpoint_autoactivate('petrel#sdm', if_expires_in=600)
    print code, reason, result
    code, message, data = api.transfer_submission_id()
    print code, message, data
    submission_id = data['value']
    t = Transfer(submission_id, "petrel#sdm", "petrel#sdm")
    t.add_item("/test/testfile.txt", "/test/col/dir1/testfile01")
    code, reason, data = api.transfer(t)
    task_id = data['task_id']
    print "TASK_ID: ", task_id
    for i in range(0, 10):
        code, reason, data = api.task(task_id, fields="status")
        status = data["status"]
        print "STATUS: ", status
        time.sleep(10)
    '''
    global globusClient
    globusClient = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    globusClient.oauth2_start_flow()
    authorize_url = globusClient.oauth2_get_authorize_url()
    return format(authorize_url)

@app.route('/connectGlobus', methods=['GET', 'POST'])
@login_required
def connectGlobus():
    authID = request.form.get('authURL')
    token_response = globusClient.oauth2_exchange_code_for_tokens(authID)
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    authorizer = globus_sdk.AccessTokenAuthorizer(access_token=globus_transfer_data['access_token'])
    tc = globus_sdk.TransferClient(authorizer=authorizer)
    extrepid = '9c9cb97e-de86-11e6-9d15-22000a1e3b52'
    ep = tc.get_endpoint(extrepid)
    r = tc.operation_ls(extrepid, path='/gdata/dm')
    for item in r:
        print("{}: {} [{}]".format(item["type"], item["name"], item["size"]))

    # Setup for actually transferring files
    '''
    local_ep = globus_sdk.LocalGlobusConnectPersonal()
    local_ep_id = local_ep.endpoint_id
    tdata = globus_sdk.TransferData(tc, ep.endpoint_id, local_ep_id)
    searchPath = "/test"
    for file in searchPath:
        tdata.add_item(file, app.config['UPLOAD_DIR'] + '/rawData')
    tc.submit_transfer(tdata)


    r = tc.operation_ls(petrel, path='/test')
    for item in r:
        print("{}: {} [{}]".format(item["type"], item["name"], item["size"]))
    '''

    return 'Connected'

def getApi(username, password):
    goAuthTuple = get_access_token(username=username, password=password)
    api = TransferAPIClient(goAuthTuple.usernmae, goauth=goAuthTuple.token)
    return api


def peakFit(idthis, energyType, signalType, unit, fitType, fitRange, inputCord, localRange):
    if fitType == 'Unfit':
        fitType = 'AtMax'
    file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
    format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                currentMeta.file_id == file_instance.id,
                                                                currentMeta.session == current_user.current_session)).first()
    if str(file_instance.type) == 'mda':
        data, name, unusedpath = readMda(file_instance.path)
    else:
        data, name, unusedpath = readAscii(file_instance.path, file_instance.comChar)
    form = populate_from_instance(format_instance)
    columns, bools = splitForm(form)
    basedColumns = zeroBaseColumns(columns)
    used = []
    additional = []
    legendNames = []
    if energyType == 'Energy xtal':
        energy = numpy.divide(energy_xtal(data, unicode_to_int(basedColumns[3].data),
                                          unicode_to_int(basedColumns[4].data), format_instance.hrm), 1000000)
        additional.append(energy)
        legendNames.append(basedColumns[1].id)
    elif energyType == 'Energy xtal w/T':
        energy = numpy.divide(energy_xtal_temp(data, unicode_to_int(basedColumns[3].data),
                                               unicode_to_int(basedColumns[4].data),
                                               unicode_to_int(basedColumns[5].data),
                                               unicode_to_int(basedColumns[6].data), format_instance.hrm), 1000000)
        additional.append(energy)
        legendNames.append(basedColumns[2].id)
    else:
        used.append(unicode_to_int(basedColumns[0].data))
        legendNames.append(basedColumns[0].id)
    if signalType == 'Signal Normalized':
        signal = signal_normalized(data, unicode_to_int(basedColumns[8].data),
                                   unicode_to_int(basedColumns[10].data))
        additional.append(signal)
        legendNames.append(basedColumns[9].id)
    else:
        used.append(unicode_to_int(basedColumns[8].data))
        legendNames.append(basedColumns[8].id)
    max, xmax, ycords = convert_Numpy(used, data, additional)
    npXcords = numpy.array(ycords[0])
    if unit == 'keV':
        npYcords = numpy.array(ycords[1])
    else:
        npXcords = numpy.multiply(npXcords, 1000000)
        npYcords = numpy.array(ycords[1])
    if fitType == 'AtMax':
        leftBound = (find_nearest(npXcords, npXcords[xmax[1]] - (fitRange / 2)))
        rightBound = (find_nearest(npXcords, npXcords[xmax[1]] + (fitRange / 2)))
        targetRange = [x for x in npXcords if x >= leftBound]
        targetRange = [x for x in targetRange if x <= rightBound]
        npData = []
        for xcord in targetRange:
            oneCord = numpy.where(npXcords == xcord)[0][0]
            npData.append(ycords[1][oneCord])
        targetX = numpy.array(targetRange)
        targetY = numpy.array(npData)
        center = centroid(targetX, targetY)
        ycords[0] = npXcords
        moveXcords(ycords, center)
        format_instance.fit_type = 'AtMax'
        format_instance.fit_pos = center
        format_instance.fit_range = fitRange
    elif fitType == 'AtPoint':
        leftBound = (find_nearest(npXcords, inputCord + npXcords[0] - (fitRange / 2)))
        rightBound = (find_nearest(npXcords, inputCord + npXcords[0] + (fitRange / 2)))
        targetRange = [x for x in npXcords if x >= leftBound]
        targetRange = [x for x in targetRange if x <= rightBound]
        npData = []
        for xcord in targetRange:
            oneCord = numpy.where(npXcords == xcord)[0][0]
            npData.append(ycords[1][oneCord])
        targetX = numpy.array(targetRange)
        targetY = numpy.array(npData)
        center = centroid(targetX, targetY)
        ycords[0] = npXcords
        moveXcords(ycords, center)
        format_instance.fit_type = 'AtPoint'
        format_instance.fit_pos = center
        format_instance.fit_range = fitRange
    else:
        leftBound = (find_nearest(npXcords, inputCord + npXcords[0] - (localRange / 2)))
        rightBound = (find_nearest(npXcords, inputCord + npXcords[0] + (localRange / 2)))
        targetRange = [x for x in npXcords if x >= leftBound]
        targetRange = [x for x in targetRange if x <= rightBound]
        npData = []
        for xcord in targetRange:
            oneCord = numpy.where(npXcords == xcord)[0][0]
            npData.append(ycords[1][oneCord])
        npData = numpy.array(npData)
        max = numpy.argmax(npData)
        maxIndex = oneCord - len(targetRange) + max + 1

        leftBound = (find_nearest(npXcords, npXcords[maxIndex] - (fitRange / 2)))
        rightBound = (find_nearest(npXcords, npXcords[maxIndex] + (fitRange / 2)))
        targetRange = [x for x in npXcords if x >= leftBound]
        targetRange = [x for x in targetRange if x <= rightBound]
        npData = []
        for xcord in targetRange:
            oneCord = numpy.where(npXcords == xcord)[0][0]
            npData.append(ycords[1][oneCord])
        targetX = numpy.array(targetRange)
        targetY = numpy.array(npData)
        center = centroid(targetX, targetY)
        ycords[0] = npXcords
        moveXcords(ycords, center)
        format_instance.fit_type = 'AtPoint'
        format_instance.fit_pos = center
        format_instance.fit_range = fitRange
    db.session.commit()
    code = simplePlot(ycords, xmax, file_instance.name, legendNames, 0, 0)
    return code, ycords, form


def getHeader(fileName, filePath):
    d = mda.readMDA(filePath, 4, 0, 0)
    if not d:
        return 0

    rank = d[0]['rank']
    (phead_fmt, dhead_fmt, pdata_fmt, ddata_fmt, columns) = mdaAscii.getFormat(d, 1)
    output = "### " + fileName + " is a " + str(d[0]['rank']) + "dimensional file.\n"
    if (rank > len(d) - 1):
        output += "file doesn't contain the data that it claims to contain\n"
        output += "rank=%d, dimensions found=%d" % (rank, len(d) - 1)
        return output
    output += "### Number of data points = ["
    for i in range(d[0]['rank'], 1, -1):
        output += "%-d," % str(d[i].curr_pt)
    output += str(d[1].curr_pt) + "]\n"

    output += "### Number of detector signals = ["
    for i in range(d[0]['rank'], 1, -1): output += "%-d," % d[i].nd
    output += str(d[1].nd) + "]\n"
    output += "#\n# Scan-environment PV values:\n"
    ourKeys = d[0]['ourKeys']
    maxKeyLen = 0
    for i in d[0].keys():
        if (i not in ourKeys):
            if len(i) > maxKeyLen: maxKeyLen = len(i)
    for i in d[0].keys():
        if (i not in ourKeys):
            output += "#" + str(i) + str((maxKeyLen - len(i)) * ' ') + str(d[0][i]) + "\n"
    output += "#\n# " + str(d[1]) + "\n"
    output += "#  scan date, time: " + str(d[1].time) + "\n"
    output += "#\n"
    for j in range(d[1].np):
        output += phead_fmt[j] % (d[1].p[j].fieldName) + "\n"
    for j in range(d[1].nd):
        output += dhead_fmt[j] % (d[1].d[j].fieldName) + "\n"

    output += "#\n"
    for j in range(d[1].np):
        output += phead_fmt[j] % (d[1].p[j].name) + "\n"
    for j in range(d[1].nd):
        output += dhead_fmt[j] % (d[1].d[j].name) + "\n"

    output += "#\n"
    for j in range(d[1].np):
        output += phead_fmt[j] % (d[1].p[j].desc) + "\n"
    for j in range(d[1].nd):
        output += dhead_fmt[j] % (d[1].d[j].desc) + "\n"
    return output


def writeOutput(output, colNames, name, lname):
    '''
    Writes a .txt output file based on the location that the user is requesting the output from.

    Leave the name of the file(s) as a comment on the top of the file using the user's comment character as saved on their profile
    If the user does not have a comment character saved on their profile it defaults to #
    '''
    comChar = current_user.commentChar
    if comChar == None:
        comChar = '#'
    if isinstance(name, list):
        filename = lname + ' ' + str(getTime())
    else:
        filename = name + ' ' + str(getTime())
    f = open(app.config['UPLOAD_DIR'] + '/outData/' + filename, 'w')
    if isinstance(name, list):
        f.write('#Files Included:')
        f.write('\n')
        for id in name:
            file = db.session.query(dataFile).filter_by(id=id).first()
            f.write('#' + file.name)
            f.write('\n')
    else:
        f.write('#' + name)
        f.write('\n')
    for i in range(len(output)):
        if isinstance(colNames[i], str):
            f.write(comChar + str(colNames[i]) + '= Column: ' + str(i + 1))
        else:
            f.write(comChar + str(colNames[i].text) + '= Column: ' + str(i + 1))
        f.write('\n')
    for i in range(len(output[0])):
        for j in range(len(output)):
            f.write(str(output[j][i]) + (' ' * 10))
        f.write('\n')
    f.close()

    downloadLocation = os.path.join(app.config['UPLOAD_DIR']) + '/outData'

    path = downloadLocation + '/' + filename

    return filename


def atMax(ycords, npXcords, xmax, fitRange):
    '''
    Finds the center of the npXcords that fall within the fitRange

    Calls centroid to get the actual center while this primarily does the bounding to collect the points to pass to centroid.
    '''
    leftBound = (find_nearest(npXcords, xmax[1] - (fitRange / 2)))
    rightBound = (find_nearest(npXcords, xmax[1] + (fitRange / 2)))
    targetRange = [x for x in npXcords if x >= leftBound]
    targetRange = [x for x in targetRange if x <= rightBound]
    npData = []
    for xcord in targetRange:
        oneCord = numpy.where(npXcords == xcord)[0][0]
        npData.append(ycords[1][oneCord])
    targetX = numpy.array(targetRange)
    targetY = numpy.array(npData)
    center = centroid(targetX, targetY)
    return center


def moveXcords(data, max):
    data[0] = numpy.subtract(data[0], max)
    return data


def centroid(xVals, yVals):
    bot = numpy.sum(yVals)
    topArray = numpy.multiply(xVals, yVals)
    top = numpy.sum(topArray)
    shiftVal = top / bot
    return shiftVal


def unicode_to_int(unicode):
    convertI = int(unicode)
    return convertI


def splitForm(form):
    columns = []
    bools = []
    for field in form:
        if field.type == 'IntegerField':
            columns.append(field)
        else:
            bools.append(field)
    return columns, bools


def zeroBaseColumns(columns):
    zColumns = copy.deepcopy(columns)
    for zColumn in zColumns:
        if zColumn.data is not None:
            zColumn.data -= 1
    return zColumns


def modified(path):
    """Returns modified time of this."""
    return datetime.fromtimestamp(os.path.getmtime(path))


def getTime():
    return datetime.now()


def size(path):
    """A size of this file."""
    return os.path.getsize(path)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def populate_from_instance(instance):
    form = InputForm()
    for field in form:
        try:
            field.data = getattr(instance, field.name)
        except AttributeError:
            continue
    return form


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


def run_once_with_args(f):
    def wrapper(*args, **kwargs):
        global usedArgs
        if not args[0] in usedArgs:
            if args[0] != -1:
                usedArgs.append(*args)
                return f(*args, **kwargs)
            else:
                usedArgs = []

    return wrapper


@run_once_with_args
def setBaseComment(idnext):
    file_instance = db.session.query(dataFile).filter_by(id=idnext).first()
    format_instance = db.session.query(currentMeta).filter(and_(currentMeta.user_id == current_user.get_id(),
                                                                currentMeta.file_id == file_instance.id,
                                                                currentMeta.session == current_user.current_session)).first()
    if format_instance is not None:
        format_instance.comment = file_instance.comment
        db.session.commit()


def find_nearest(array, value):
    idx = (numpy.abs(array - value)).argmin()
    return array[idx]


def readAscii(path, comChar):
    count = 0
    name = path.split("/")
    name = name[-1]
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(comChar):
                continue
            if len(line) == 0:
                continue
            line = line[1:]
            line = line.split()
            if count == 0:
                data = [[] for x in xrange(len(line))]
            count += 1
            for i in range(len(line)):
                data[i].append(line[i])
    return data, name, path


def readMdaAscii(path):
    count = 0
    name = path.split("/")
    name = name[-1]
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("#"):
                continue
            if len(line) == 0:
                continue
            line = line.split(" ")
            if count == 0:
                data = [[] for x in xrange(len(line))]
            count += 1
            for i in range(len(line)):
                data[i].append(line[i])
    return data, name, path


def readMda(path):
    name = path.split("/")
    name = name[-1]
    endData = []
    mdaData = mda.readMDA(path, 1, 0, 0)
    for column in mdaData[1].p:
        endData.append(column.data)
    for column in mdaData[1].d:
        endData.append(column.data)
    return endData, name, path


def simplePlot(data, xmax, filename, linenames, legend, sized):
    plt.close('all')
    fig = plt.figure(figsize=(10, 7))
    css = """
    .legend-box{
        cursor: pointer;
    }
    """
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    if legend == 0:
        fig, ax = plt.subplots()
        xs = data[0]
        ys = data[1]
        plt.plot(xs, ys)
        # plt.plot(xs[xmax[1]], ys[xmax[1]], '-bD')
    else:
        fig, ax = plt.subplots()
        xs = data[0]
        ys = data[1]
        line = ax.plot(xs, ys, alpha=0, label=filename)
        lines.append(line[0])
        # point = ax.plot(xs[xmax[1]], ys[xmax[1]], '-bD')
        labels.append(filename)
        # lines.append(point[0])

        mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, sized, nameID, css))
        mpld3.plugins.connect(fig, HideLegend(nameID))
    plt.xlabel('meV')
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return code


def mergePlots(allycords, allxmax, allagainstE, alldata, allLegendNames, allFileNames, pltLeg):
    '''Merges a list of plots using linear interpolation then plots the result'''
    plt.close('all')
    fig = plt.figure(figsize=(10, 7))
    css = """
    .legend-box{
        cursor: pointer;
    }
    """
    count1 = 0
    count2 = 0
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    if pltLeg == 0:
        for plot in alldata:
            xs = range(1, len(plot) + 1)
            ys = plot
            if allagainstE[count1] == 'Energy' or allagainstE[count1] == 'Energy xtal' or allagainstE[
                count1] == 'Energy xtal w/T':
                xs = alldata[count1][1]
                xs = numpy.multiply(xs, 1000000)
            plt.plot(xs, ys)
            # plt.plot(xs[allxmax[count1][count2]], ys[allxmax[count2]], '-bD')
            count2 += 1
    else:
        fig, ax = plt.subplots()
        for oneDat in allycords:
            xs = oneDat[0]
            ys = oneDat[1]
            line = ax.plot(xs, ys, alpha=0, label=allFileNames[count1])
            lines.append(line[0])
            # point = ax.plot(xs[allxmax[count1][1]], ys[allxmax[count1][1]], '-bD')
            labels.append(allFileNames[count1])
            # lines.append(point[0])
            count1 += 1
        sumNumpy = []
        YVals = []
        for i in allycords:
            sumNumpy.append(i[0])
            YVals.append(i[1])
            if len(sumNumpy) == 2:
                numCat = numpy.array(sumNumpy)
                numCat[0] = numpy.array(numCat[0])
                numCat[1] = numpy.array(numCat[1])
                YVals[0] = numpy.array(YVals[0])
                YVals[1] = numpy.array(YVals[1])
                if numCat[0].size > numCat[1].size:
                    smallerx = numCat[1]
                    smallery = YVals[1]
                    largerx = numCat[0]
                    largery = YVals[0]
                else:
                    smallerx = numCat[0]
                    smallery = YVals[0]
                    largerx = numCat[1]
                    largery = YVals[1]
                smallLeft = (find_nearest(largerx, smallerx[0]))
                smallRight = (find_nearest(largerx, smallerx[-1]))
                largeLeft = (find_nearest(smallerx, largerx[0]))
                largeRight = (find_nearest(smallerx, largerx[-1]))
                smallleftPad = 0
                smallrightPad = 0
                largeleftPad = 0
                largerightPad = 0
                largeInnerX = []
                largeInnerY = []
                smallInnerX = []
                smallInnerY = []
                first = 0
                smallRightPadIndex = 'None'
                largeRightPadIndex = 'None'
                for element in largerx:
                    if element < smallLeft:
                        smallleftPad += 1
                    elif element > smallRight:
                        if first == 0:
                            smallRightPadIndex = numpy.where(largerx == element)[0][0]
                            first = 1
                        smallrightPad += 1
                    else:
                        largeInnerX.append(element)
                        atIndex = numpy.where(largerx == element)[0][0]
                        largeInnerY.append(largery[atIndex])
                first = 0
                for element in smallerx:
                    if element < largeLeft:
                        largeleftPad += 1
                    elif element > largeRight:
                        if first == 0:
                            largeRightPadIndex = numpy.where(smallerx == element)[0][0]
                            first = 1
                        largerightPad += 1
                    else:
                        smallInnerX.append(element)
                        atIndex = numpy.where(smallerx == element)[0][0]
                        smallInnerY.append(smallery[atIndex])

                smallInnerX = numpy.array(smallInnerX)
                smallInnerY = numpy.array(smallInnerY)
                largeInnerX = numpy.array(largeInnerX)
                largeInnerY = numpy.array(largeInnerY)

                if largeInnerX.size > smallInnerX.size:
                    smallInnerY = numpy.interp(largeInnerX, smallInnerX, smallInnerY)
                    adjLargex = largerx
                    if largeRightPadIndex != 'None':
                        adjSmallx = numpy.concatenate(
                            (smallerx[:largeleftPad], largeInnerX, smallerx[largeRightPadIndex:]))
                        smallery = numpy.concatenate(
                            (smallery[:largeleftPad], smallInnerY, smallery[largeRightPadIndex:]))
                    else:
                        adjSmallx = numpy.concatenate((smallerx[:largeleftPad], largeInnerX))
                        smallery = numpy.concatenate((smallery[:largeleftPad], smallInnerY))
                elif largeInnerX.size < smallInnerX.size:
                    adjSmallx = smallerx
                    largeInnerY = numpy.interp(smallInnerX, largeInnerX, largeInnerY)
                    if smallRightPadIndex != 'None':
                        adjLargex = numpy.concatenate(
                            (largerx[:smallleftPad], smallInnerX, largerx[smallRightPadIndex:]))
                        largery = numpy.concatenate((largery[:smallleftPad], largeInnerY, largery[smallRightPadIndex:]))
                    else:
                        adjLargex = numpy.concatenate((largerx[:smallleftPad], smallInnerX))
                        largery = numpy.concatenate((largery[:smallleftPad], largeInnerY))
                else:
                    if smallRightPadIndex != 'None':
                        adjLargex = numpy.concatenate(
                            (largerx[:smallleftPad], largeInnerX, largerx[smallRightPadIndex:]))
                    else:
                        adjLargex = numpy.concatenate((largerx[:smallleftPad], largeInnerX))
                    if largeRightPadIndex != 'None':
                        adjSmallx = numpy.concatenate(
                            (smallerx[:largeleftPad], largeInnerX, smallerx[largeRightPadIndex:]))
                    else:
                        adjSmallx = numpy.concatenate((smallerx[:largeleftPad], largeInnerX))

                smallPady = numpy.pad(smallery, (smallleftPad, smallrightPad), 'constant', constant_values=(0, 0))
                largePady = numpy.pad(largery, (largeleftPad, largerightPad), 'constant', constant_values=(0, 0))

                if largeRightPadIndex != 'None':
                    largePadx = numpy.concatenate((smallerx[:largeleftPad], adjLargex, smallerx[largeRightPadIndex:]))
                else:
                    largePadx = numpy.concatenate((smallerx[:largeleftPad], adjLargex))
                if smallRightPadIndex != 'None':
                    smallPadx = numpy.concatenate((largerx[:smallleftPad], adjSmallx, largerx[smallRightPadIndex:]))
                else:
                    smallPadx = numpy.concatenate((largerx[:smallleftPad], adjSmallx))

                small = numpy.array((smallPadx, smallPady))
                large = numpy.array((largePadx, largePady))
                ySummed = numpy.add(small[1], large[1])
                sum2D = numpy.array((largePadx, ySummed))
                sumNumpyStep = largePadx.tolist()
                YValsStep = ySummed.tolist()
                sumNumpy = []
                YVals = []
                sumNumpy.append(sumNumpyStep)
                YVals.append(YValsStep)

        sum2Dymax = numpy.amax(sum2D)
        sum2Dxmax = numpy.ndarray.argmax(sum2D)
        line = ax.plot(largePadx, ySummed, color='k', alpha=0, label='Sum of selected')
        lines.append(line[0])

        # point = ax.plot(sum2D[0][sum2Dxmax - largePadx.size], sum2Dymax, '-bD')
        labels.append('Sum of selected')
        # lines.append(point[0])
        mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 1, nameID, css))
    mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return code, sum2D[0][sum2Dxmax - largePadx.size], sum2Dymax, largePadx, ySummed


def mergeBin(allycords, allxmax, allagainstE, alldata, allLegendNames, allFileNames, pltLeg, binWidth):
    '''Merges a list of plots with binning and plots the result'''
    plt.close('all')
    fig = plt.figure(figsize=(10, 7))
    css = """
    .legend-box{
        cursor: pointer;
    }
    """
    count1 = 0
    count2 = 0
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    if pltLeg == 0:
        for plot in alldata:
            xs = range(1, len(plot) + 1)
            ys = plot
            if allagainstE[count1] == 'Energy' or allagainstE[count1] == 'Energy xtal' or allagainstE[
                count1] == 'Energy xtal w/T':
                xs = alldata[count1][1]
            plt.plot(xs, ys)
            # plt.plot(xs[allxmax[count1][count2]], ys[allxmax[count2]], '-bD')
            count2 += 1
    else:
        fig, ax = plt.subplots()
        for oneDat in allycords:
            xs = oneDat[0]
            ys = oneDat[1]
            line = ax.plot(xs, ys, alpha=0, label=allFileNames[count1])
            lines.append(line[0])
            # point = ax.plot(xs[allxmax[count1][1]], ys[allxmax[count1][1]], '-bD')
            labels.append(allFileNames[count1])
            # lines.append(point[0])
            count1 += 1
        minValue = 0
        maxValue = 0
        endX = []
        endY = []
        for i in allycords:
            if i[0][0] < minValue:
                minValue = i[0][0]
            if i[0][-1] > maxValue:
                maxValue = i[0][-1]
        bins = numpy.arange(minValue, maxValue, binWidth)
        for i in range(len(allycords)):
            sumNumpy = []
            YVals = []
            endX.append([])
            endY.append([])
            binnedIdx = numpy.digitize(allycords[i][0], bins)
            resultIdx = 0
            for j in range(len(binnedIdx)):
                if j == 0:
                    YVals.append([allycords[i][1][j], binnedIdx[j], 1])
                    sumNumpy.append([allycords[i][0][j], binnedIdx[j], 1])
                    continue
                if binnedIdx[j] == binnedIdx[j - 1]:
                    YVals[resultIdx][0] += allycords[i][1][j]
                    YVals[resultIdx][2] += 1
                    sumNumpy[resultIdx][0] += allycords[i][0][j]
                    sumNumpy[resultIdx][2] += 1
                else:
                    resultIdx += 1
                    YVals.append([allycords[i][1][j], binnedIdx[j], 1])
                    sumNumpy.append([allycords[i][0][j], binnedIdx[j], 1])
            for k in range(len(sumNumpy)):
                endX[i].append([sumNumpy[k][0] / sumNumpy[k][2], sumNumpy[k][1]])
                endY[i].append([YVals[k][0] / YVals[k][2], YVals[k][1]])
        sumXvals = []
        sumYvals = []
        binIdx = 1
        for i in range(len(bins)):
            sumXvals.append(None)
            sumYvals.append(None)
            for j in range(len(endX)):
                for k in range(len(endX[j])):
                    if endX[j][k][1] == binIdx:
                        if sumXvals[binIdx - 1] == None:
                            sumXvals[binIdx - 1] = endX[j][k][0]
                            sumYvals[binIdx - 1] = endY[j][k][0]
                        else:
                            sumXvals[binIdx - 1] = (sumXvals[binIdx - 1] + endX[j][k][0]) / 2
                            sumYvals[binIdx - 1] = sumYvals[binIdx - 1] + endY[j][k][0]
            binIdx += 1
        sumXvals = [value for value in sumXvals if value != None]
        sumYvals = [value for value in sumYvals if value != None]
        line = ax.plot(sumXvals, sumYvals, color='k', alpha=0, label='Sum of selected')
        lines.append(line[0])

        sum2D = numpy.array((sumXvals, sumYvals))
        sum2Dymax = numpy.amax(sum2D)
        sum2Dxmax = numpy.ndarray.argmax(sum2D)

        # point = ax.plot(sum2D[0][sum2Dxmax - len(sumXvals)], sum2Dymax, '-bD')
        labels.append('Sum of selected')
        # lines.append(point[0])
        mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 1, nameID, css))
    mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return code, sum2D[0][sum2Dxmax - len(sumXvals)], sum2Dymax, sumXvals, sumYvals


def plotData(data, used, againstE, additional, lineNames, eType, unit):
    plt.close('all')
    fig = plt.figure(figsize=(10, 7))
    css = """
    .legend-box{
        cursor: pointer;
    }
    """
    xs = []
    ys = []
    labels = []
    lines = []
    count = 0
    nameID = str(uuid.uuid4())
    fig, ax = plt.subplots()
    for i in used:
        xs = range(1, len(data[i]) + 1)
        ys = data[i]
        plt.xlabel('Point #')
        if againstE == 'Energy' or againstE == 'Energy xtal' or againstE == 'Energy xtal w/T':
            xs = [float(x) for x in eType]
            if unit == 'keV':
                xs = numpy.subtract(xs, xs[0])
                plt.xlabel('keV')
            else:
                xs = numpy.multiply(xs, 1000000)
                xs = numpy.subtract(xs, xs[0])
                plt.xlabel('meV')
        elif againstE == 'Energy Fitted':
            xs = [float(x) for x in eType]
            plt.xlabel('meV')
        line = ax.plot(xs, ys, alpha=0, label=lineNames[0][count])
        lines.append(line[0])
        labels.append(lineNames[0][count])
        count += 1

    if additional:
        for i in range(len(additional)):
            xs = range(1, len(additional[i]) + 1)
            ys = additional[i]
            plt.xlabel('Point #')
            if againstE == 'Energy' or againstE == 'Energy xtal' or againstE == 'Energy xtal w/T':
                xs = [float(x) for x in eType]
                if unit == 'keV':
                    xs = numpy.subtract(xs, xs[0])
                    plt.xlabel('keV')
                else:
                    xs = numpy.multiply(xs, 1000000)
                    xs = numpy.subtract(xs, xs[0])
                    plt.xlabel('meV')
            elif againstE == 'Energy Fitted':
                xs = [float(x) for x in eType]
                plt.xlabel('meV')
            line = ax.plot(xs, ys, alpha=0, label=lineNames[1][i])
            lines.append(line[0])
            labels.append(lineNames[1][i])

    if not used and not additional:
        ax = plt.plot(ys, ys)
    else:
        mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 0, nameID, css))
        mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return code


def convert_Numpy(used, data, additional):
    toNumpy = []

    if additional:
        for i in range(len(additional)):
            dat = additional[i]
            toNumpy.append(dat)

    for idx, column in enumerate(data):
        for i in used:
            if (idx) == i:
                dat = [float(j) for j in data[i]]
                toNumpy.append(dat)
    npData = numpy.array(toNumpy)
    max = []
    xcord = []
    for plot in npData:
        max.append(numpy.amax(plot))
        xcord.append(numpy.argmax(plot))
    return max, xcord, toNumpy


def energy_xtal(data, a1, a2, hrm):
    hrm = json.loads(hrm)
    energy = []
    a1Dat = data[a1]
    a2Dat = data[a2]
    a1Dat = [hrm['hrm_theta1_sign'] * float(i) for i in a1Dat]
    a2Dat = [hrm['hrm_theta2_sign'] * float(i) for i in a2Dat]
    hrm_tan1 = math.tan(math.radians(hrm['hrm_bragg1']))
    hrm_tan2 = math.tan(math.radians(hrm['hrm_bragg2']))

    if hrm['hrm_geo'] == '++':
        a = 1.0e-6 * hrm['hrm_e0'] / (hrm_tan1 + hrm_tan2)
        b = a1Dat[0] - a2Dat[0]
        for i in range(len(a1Dat)):
            energy.append(a * (a1Dat[i] - a2Dat[i] - b))
    else:
        a = 1.0e-6 * hrm['hrm_e0'] / (hrm_tan1 - hrm_tan2)
        b = a1Dat[0] + a2Dat[0]
        for i in range(len(a1Dat)):
            energy.append(a * (a1Dat[i] + a2Dat[i] - b))
    return energy


def energy_xtal_temp(data, a1, a2, t1, t2, hrm):
    energy = []
    xtal = energy_xtal(data, a1, a2, hrm)
    corr = temp_corr(data, t1, t2, hrm)
    for i in range(len(xtal)):
        energy.append(xtal[i] + corr[i])
    return energy


def temp_corr(data, t1, t2, hrm):
    hrm = json.loads(hrm)
    corr = []
    t1Dat = data[t1]
    t2Dat = data[t2]
    t1Dat = [float(i) for i in t1Dat]
    t2Dat = [float(i) for i in t2Dat]
    hrm_tan1 = math.tan(math.radians(hrm['hrm_bragg1']))
    hrm_tan2 = math.tan(math.radians(hrm['hrm_bragg2']))
    at1 = hrm['hrm_alpha1'] * hrm_tan1
    at2 = hrm['hrm_alpha2'] * hrm_tan2

    if hrm == '++':
        a = - hrm['hrm_e0'] / (hrm_tan1 + hrm_tan2)
        b = at1 * t1Dat[0] + at2 * t2Dat[0]
        for i in range(len(t1Dat)):
            corr.append(a * (at1 * t1Dat[i] + at2 * t2Dat[i] - b))
    else:
        a = - hrm['hrm_e0'] / (hrm_tan1 - hrm_tan2)
        b = at1 * t1Dat[0] - at2 * t2Dat[0]
        for i in range(len(t1Dat)):
            corr.append(a * (at1 * t1Dat[i] - at2 * t2Dat[i] - b))
    return corr


def signal_normalized(data, sCol, nCol):
    signal = []
    sDat = data[sCol]
    nDat = data[nCol]
    sDat = [float(i) for i in sDat]
    nDat = [float(i) for i in nDat]

    normFac = norm_factors(data, nCol)

    for i in range(len(sDat)):
        signal.append(sDat[i] * normFac[i])
    return signal


def norm_factors(data, nCol):
    norm = []
    nDat = data[nCol]
    nDat = [float(i) for i in nDat]

    ave = numpy.mean(nDat)
    for i in range(len(nDat)):
        norm.append(ave / nDat[i])
    return norm


def calcAverageBack(leftIn, rightIn):
    DAT = db.session.query(currentDAT).filter(currentDAT.user == current_user).first()
    leftCords = [[] for _ in xrange(2)]
    rightCords = [[] for _ in xrange(2)]
    data = json.loads(DAT.DAT)
    for i in range(len(data[0])):
        if data[0][i] <= leftIn:
            leftCords[0].append(data[0][i])
            leftCords[1].append(data[1][i])
        if data[0][i] >= rightIn:
            rightCords[0].append(data[0][i])
            rightCords[1].append(data[1][i])
    try:
        linRegLeft = stats.linregress(leftCords[0], leftCords[1])
        (slope, intercept, rvalue, pvalue, stderr) = linRegLeft
        Lx1 = data[0][1]
        Lx2 = leftIn
        Ly1 = data[1][1]
        try:
            Ly2 = linRegLeft.slope * (Lx2 - Lx1) + Ly1
        except AttributeError:
            Ly2 = slope * (Lx2 - Lx1) + Ly1
    except ValueError:
        print('No points less than left value')
        raise ValueError('Average can not be found when there are no points smaller than the given left to average.')
    try:
        linRegRight = stats.linregress(rightCords[0], rightCords[1])
        (slope, intercept, rvalue, pvalue, stderr) = linRegRight
        Rx1 = rightIn
        Rx2 = data[0][-1]
        Ry2 = data[1][-1]
        try:
            Ry1 = linRegRight.slope * (Rx1 - Rx2) + Ry2
        except AttributeError:
            Ry1 = slope * (Rx1 - Rx2) + Ry2
    except ValueError:
        print('No points greater than right value')
        raise ValueError('Average can not be found when there are no points greater than the given right to average.')

    fig = plt.figure(figsize=(10, 7))
    css = """
        .legend-box{
            cursor: pointer;
        }
        """
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    fig, ax = plt.subplots()
    xs = data[0]
    ys = data[1]
    line = ax.plot(xs, ys, alpha=0, label='Summed')
    lines.append(line[0])
    labels.append('Summed')

    line = ax.plot([Lx1, Lx2], [Ly1, Ly2], alpha=0, label='Left Lin Reg')
    lines.append(line[0])
    labels.append('Left Lin Reg')
    line = ax.plot([Rx1, Rx2], [Ry1, Ry2], alpha=0, label='Right Lin Reg')
    lines.append(line[0])
    labels.append('Right Lin Reg')
    mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 1, nameID, css))
    mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    averaged = [Lx1, Lx2, Rx1, Rx2, Ly1, Ly2, Ry1, Ry2]
    sending = averaged
    return sending


def addLines(line1, line2):
    fig = plt.figure(figsize=(10, 7))
    css = """
            .legend-box{
                cursor: pointer;
            }
            """
    labels = []
    lines = []
    nameID = str(uuid.uuid4())
    fig, ax = plt.subplots()
    xs = line1[0]
    ys = line1[1]
    line = ax.plot(xs, ys, alpha=0, label='Summed')
    lines.append(line[0])
    labels.append('Summed')
    xs = []
    ys = []
    try:
        for i in range(len(line2)):
            if i < len(line2) / 2:
                xs.append(line2[i])
            else:
                ys.append(line2[i])
        line = ax.plot(xs, ys, alpha=0, label='Background')
    except TypeError:
        line = ax.plot(line1[0], [line2] * len(line1[0]), alpha=0, label='Background')

    lines.append(line[0])
    labels.append('Background')
    mpld3.plugins.connect(fig, InteractiveLegend(lines, labels, 1, nameID, css))
    mpld3.plugins.connect(fig, HideLegend(nameID))
    code = mpld3.fig_to_html(fig)
    plt.close('all')
    return code


class HideLegend(mpld3.plugins.PluginBase):
    """mpld3 plugin to hide legend on plot"""

    JAVASCRIPT = """
    var my_icon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABVklEQVR42pXTO0sDQRSG4dmsyXptQ8BKCwsbq4CCiPgDrOwkIsTSf2Ul2KidhaAWYiFBFC1UWKN4VzTeQ0DfDd8u47gpLB4yc3Zy9szMWWOM8ZARz/ltFRvGlmJJ8D928axxy0UDKGMdo8gqfo66te7Xn9owhX3c4AWXGl/hBA1ne8kkh2+8KtEsPpXkHmP4wiN60iq4xYTGG1i1ys6jigX040kvaSbI6y1lBbpQsRIHOMAi9hQbwUec4B13mvgoIbTmb6rGtxJH4zPMG2UqKBg9nMGpxnVtx76+uPROVW6KOES3kkzjAkuqzLcSVKwDj148GB9iUYtzmofOQWV0eNtKeI1l9xYmdeeB9ldDu571qfM6dM1zSvSnlaP7fcAKhtRAUWWbGNezNWdbycBXt4Uq8Rg7cqTu7E1p+WRQ06nH2bPaTmA1lKu5BU+ZG1pof762tJj3A656Tx0L91EcAAAAAElFTkSuQmCC";
    mpld3.register_plugin("hidelegend", HideLegend);
    HideLegend.prototype = Object.create(mpld3.Plugin.prototype);
    HideLegend.prototype.constructor = HideLegend;
    HideLegend.prototype.requiredProps = ["nameID"];
    HideLegend.prototype.defaultProps = {};
    function HideLegend(fig, props){
        var tempName = props.nameID
        mpld3.Plugin.call(this, fig, props);
        var HideLegendButton = mpld3.ButtonFactory({
            buttonID: "hideLegend",
            sticky: false,
            onActivate: function(){
                var legend = $('[name=' + tempName + ']');
                var holder = $('[name=legendHolder]');
                var pltStat = localStorage.getItem('pltStat');
                if (pltStat == 0){
                    legend[0].style.visibility = "visible";
                    holder[0].style.visibility = "visible";
                    localStorage.setItem('pltStat', 1);
                }
                else{
                    legend[0].style.visibility = "hidden";
                    holder[0].style.visibility = "hidden";
                    localStorage.setItem('pltStat', 0);
                }
            },
            icon: function(){
                return my_icon;
            }
        });
        this.fig.buttons.push(HideLegendButton);
    }
    """

    def __init__(self, nameID):
        self.dict_ = {'type': 'hidelegend',
                      'nameID': nameID}


class InteractiveLegend(mpld3.plugins.PluginBase):
    """"A plugin that allows the user to toggle lines though clicking on the legend"""

    JAVASCRIPT = """
        mpld3.register_plugin("interactive_legend", InteractiveLegend);
        InteractiveLegend.prototype = Object.create(mpld3.Plugin.prototype);
        InteractiveLegend.prototype.constructor = InteractiveLegend;
        InteractiveLegend.prototype.requiredProps = ["line_ids", "labels", "sized", "nameID"];
        InteractiveLegend.prototype.defaultProps = {};
        function InteractiveLegend(fig, props){
           mpld3.Plugin.call(this, fig, props);
        };
        InteractiveLegend.prototype.draw = function(){
            if (this.props.sized == 1){
                var svg = document.getElementsByClassName("mpld3-figure");
                svg[0].setAttribute("viewBox", "0 0 600 480");
                svg[0].setAttribute("width", 900);
                svg[0].setAttribute("height", 600);
            }
            var labels = new Array();
            var lineCount = this.props.labels.length
            for(var i=1; i<=lineCount; i++){
                var obj = {};
                obj.label = this.props.labels[i - 1];
                line = mpld3.get_element(this.props.line_ids[i - 1], this.fig);
                obj.line1 = line
                //point = mpld3.get_element(this.props.line_ids[(i * 2) - 1], this.fig);
                //obj.line2 = point;
                obj.visible = false;
                obj.lineNum = i;
                //var outer = point.parent.baseaxes[0][0].children[1];
                //var points = outer.getElementsByTagName("g");
                //if (typeof InstallTrigger !== 'undefined'){
                    //Firefox
                //    points[i-1].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                //    points[i-1].firstChild.style.setProperty('fill-opacity', 0, 'important');
                //}
                //else if (!!window.chrome && !!window.chrome.webstore){
                    //Chrome
                 //   points[(lineCount)-i].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                 //   points[(lineCount)-i].firstChild.style.setProperty('fill-opacity', 0, 'important');
                //}
                //else{
                    //implement more if needed
                 //   points[i-1].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                 //   points[i-1].firstChild.style.setProperty('fill-opacity', 0, 'important');
                //}

               labels.push(obj);
            }
            var ax = this.fig.axes[0];
            if (this.props.sized == 1){
                var foreign = this.fig.canvas.append('foreignObject')
                                        .attr("name", "legendHolder")
                                        .attr("x", 200)
                                        .attr("y", 30)
                                        .attr("width", 400)
                                        .attr("height", 200)
                                        .append("xhtml:div")
                                        .style("max-height", "180px")
                                        .style("overflow-y", "scroll")

                var legend = foreign.append("svg")
                                        .attr("name", this.props.nameID)
                                        .attr("id", "legendSVG")
                                        .attr("width", 387)
                                        .attr("height", labels.length * 25)
                                        .attr("x", 0)
                                        .attr("y", 0)
            }
            else{
                var legend = this.fig.canvas.append("svg")
                                        .attr("name", this.props.nameID)
                                        .attr("id", "legendSVG")
            }


            legend.selectAll("rect")
                        .data(labels)
                    .enter().append("rect")
                        .attr("height", 10)
                        .attr("width", 25)
                        .attr("x", ax.width+10+ax.position[0] - 150)
                        .attr("y", function(d, i){
                            return ax.position[1] + i * 25 - 10;})
                        .attr("stroke", function(d){
                            return d.line1.props.edgecolor})
                        .attr("class", "legend-box")
                        .style("fill", "white")
                        .on("click", click)

            legend.selectAll("text")
                        .data(labels)
                    .enter().append("text")
                        .attr("x", function(d){
                            return ax.width+10+ax.position[0] + 25 + 15 - 150
                            })
                        .attr("y", function(d, i){
                            return ax.position[1] + i * 25
                            })
                        .text(function(d){return d.label})

            if (this.props.sized == 1){
                legend.selectAll("rect")
                            .attr("x", ax.width+10+ax.position[0] - 400)
                            .attr("y", function(d, i){
                                return ax.position[1] + (i * 25) - 40
                                })

                legend.selectAll("text")
                            .attr("x", ax.width+10+ax.position[0] - 350)
                            .attr("y", function(d, i){
                                return ax.position[1] + (i * 25) - 30
                            })
            }

            if (this.props.sized == 1){
                var boxes = legend.selectAll("rect");
                var lastbox = $(boxes[0]).last();
                lastbox[0].__onclick();
            }
            else{
                var boxes = legend.selectAll("rect")
                var tempboxes = boxes[0]
                for (var i = 0; i < tempboxes.length; i++){
                    var temp = tempboxes[i];
                    temp.__onclick();
                }

            }


            function click(d, i){
                d.visible = !d.visible;
                d3.select(this)
                    .style("fill", function(d, i){
                        var color = d.line1.props.edgecolor;
                        return d.visible ? color : "white";
                    })
                d3.select(d.line1.path[0][0])
                    .style("stroke-opacity", d.visible? 1 : d.line1.props.alpha)

                //if(d.visible == true){
                    //var outer = d.line2.parent.baseaxes[0][0].children[1];
                    //var points = outer.getElementsByTagName("g");

                    //if (typeof InstallTrigger !== 'undefined'){
                        //Firefox
                        //points[d.lineNum-1].firstChild.style.setProperty('stroke-opacity', 1, 'important');
                        //points[d.lineNum-1].firstChild.style.setProperty('fill-opacity', 1, 'important');
                    //}
                    //else if (!!window.chrome && !!window.chrome.webstore){
                        //Chrome
                       // points[(lineCount)-d.lineNum].firstChild.style.setProperty('stroke-opacity', 1, 'important');
                      //  points[(lineCount)-d.lineNum].firstChild.style.setProperty('fill-opacity', 1, 'important');
                    //}
                    //else{
                        //implement more if needed
                      //  points[d.lineNum-1].firstChild.style.setProperty('stroke-opacity', 1, 'important');
                      //  points[d.lineNum-1].firstChild.style.setProperty('fill-opbacity', 1, 'important');
                    //}

                //}
                //else{
                    //var outer = d.line2.parent.baseaxes[0][0].children[1];
                   // var points = outer.getElementsByTagName("g");

                    //if (typeof InstallTrigger !== 'undefined'){
                        //Firefox
                     //   points[d.lineNum-1].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                     //   points[d.lineNum-1].firstChild.style.setProperty('fill-opacity', 0, 'important');
                    //}
                    //else if (!!window.chrome && !!window.chrome.webstore){
                        //Chrome
                       // points[(lineCount)-d.lineNum].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                       // points[(lineCount)-d.lineNum].firstChild.style.setProperty('fill-opacity', 0, 'important');
                    //}
                    //else{
                        //implement more if needed
                       // points[d.lineNum-1].firstChild.style.setProperty('stroke-opacity', 0, 'important');
                      //  points[d.lineNum-1].firstChild.style.setProperty('fill-opacity', 0, 'important');
                   // }
                //}
            }
        };
    """

    def __init__(self, lines, labels, sized, nameID, css):
        self.css_ = css or ""

        self.lines = lines

        self.dict_ = {"type": "interactive_legend",
                      "line_ids": [mpld3.utils.get_id(line) for line in lines],
                      "labels": labels,
                      "nameID": nameID,
                      "sized": sized}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
