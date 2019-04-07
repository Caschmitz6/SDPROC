__author__ = 'caschmitz'

from flask import Flask, render_template, request, session, redirect, url_for, escape, redirect, make_response
import matplotlib.pyplot as plt
import mpld3
import os
from PyQt4 import QtXml
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from app import app
from db_model import db, User, metaData, dataFile, fileFormat
from forms import InputForm, CommentForm
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import math
import numpy

login_manager = LoginManager()
login_manager.init_app(app)
ALLOWED_EXTENSIONS = {'txt', 'mda'}

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)

@app.route('/reg', methods=['GET', 'POST'])
def register():
    from forms import register_form
    form = register_form(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    from forms import login_form
    form = login_form(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login_form.html', form=form, session=session)


@app.route('/select', methods=['GET', 'POST'])
@login_required
def index():
    user = current_user
    data = []
    files = dataFile.query.order_by('id')
    for instance in files:
        fsize = size(instance.path)
        lastMod = modified(instance.path)
        temp = lastMod.strftime("%d/%m/%Y %H:%M:%S")
        modname = [instance.name + temp]
        data.insert(0, {'name': instance.name, 'path': instance.path, 'id': instance.id, 'comment': instance.comment, 'authed': instance.authed, 'size': fsize, 'modified': lastMod, 'modname': modname})
    if request.method == 'POST':
        return redirect(url_for('dataFormat'))
    return render_template('view_output.html', data=data, user=user)


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/data', methods=['GET', 'POST'])
@login_required
def dataFormat():
    user = current_user
    findPlot = request.form.get('plot', type=int)
    if findPlot != 1:
        form = InputForm(request.form)
        fig = plt.figure(figsize=(10, 7))
        code = mpld3.fig_to_html(fig)
        plt.clf()
        againstE = False
    else:
        idthis = request.form.get('idnext', type=int)
        file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        fpath = file_instance.path

        format_instance = db.session.query(fileFormat).filter_by(path=fpath).first()
        if format_instance is not None:
            againstE = format_instance.against_E
            form = populate_from_instance(format_instance)
            columns, bools = splitForm(form)
            used = []
            data, name, unusedpath = readAscii(file_instance.path)
            for i in range(len(bools)):
                if bools[i].data:
                    if columns[i].data == None:
                        if i == 1:
                            energy = energy_xtal(data, unicodeFloat_to_int(columns[2].data), unicodeFloat_to_int(columns[3].data))
                        elif i == 6:
                            energy = temp_corr(data, unicodeFloat_to_int(columns[4].data), unicodeFloat_to_int(columns[5].data))
                        elif i == 8:
                            signal = signal_normalized(data, unicodeFloat_to_int(columns[7].data), unicodeFloat_to_int(columns[9].data))
                        else:
                            norm = norm_factors(data, unicodeFloat_to_int(columns[9]))
                        continue
                    used.append(unicodeFloat_to_int(columns[i].data))
            code = plotData(data, used, againstE)
            format_instance.plot = code
            db.session.commit()
            #data.append({'form': format_instance, 'plot': plot, 'id': file_instance.id, 'comment': file_instance.comment, 'columns': columns, 'bools': bools})
        else:
            data, name, unusedpath = readAscii(file_instance.path)
            used = []

            format = fileFormat()
            format.name = file_instance.name
            format.path = file_instance.path
            format.ebool = True
            format.sbool = True
            format.energy = '1'
            format.signal = '11'
            format.xtal1A = '2'
            format.xtal2A = '3'
            format.xtal1T = '12'
            format.xtal2T = '15'
            format.norm = '7'
            format.extra = '1'
            format.against_E = False

            used.append(1)
            used.append(11)

            code = plotData(data, used, False)
            format.plot = code
            db.session.add(format)
            db.session.commit()

            code = format.plot
            form = populate_from_instance(format)
    return render_template("data_format.html", user=user, code=code, form=form, againstE=againstE)


@app.route('/save_graph', methods=['GET', 'POST'])
@login_required
def save_graph():
    form = InputForm(request.form)
    idthis = request.form.get("idnum", type=int)
    if idthis is not None:
        againstE = request.form.get("agaE", type=str)
        if againstE == 'true':
            againstE = True
        elif againstE == 'false':
            againstE = False
        else:
            print(againstE)
        file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        fpath = file_instance.path

        format_instance = db.session.query(fileFormat).filter_by(path=fpath).first()
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




@app.route('/process', methods=['GET', 'POST'])
@login_required
def dataProc():
    form = InputForm(request.form)
    data = readAscii()
    used = []
    session["checkboxes"] = form.bools
    for field in form.columns:
        for box in form.bools:
            if field.name == box.label:
                used.append(int(field.data))
    code = plotData(data, used)
    return render_template("data_process.html", form=form, code=code)


@app.route('/db')
@login_required
def sesData():
    data = []
    user = current_user
    if user.is_authenticated():
        instances = user.metaData.order_by('id').all()
        for instance in instances:
            form = populate_from_instance(instance)
            columns, bools = splitForm(form)
            plot = instance.plot
            if instance.comment:
                comment = instance.comment
            else:
                comment = ''
            data.append({'form': form, 'plot': plot, 'id': instance.id, 'comment': comment, 'columns': columns, 'bools': bools, 'name': instance.name})
    return render_template("session.html", data=data)

@app.route('/addf', methods=['POST'])
@login_required
def addFile():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pathfilename = filename + str(datetime.now())
            file.save(os.path.join(app.config['UPLOAD_DIR'], pathfilename))

            dfile = dataFile()
            dfile.name = filename
            dfile.path = '/home/phoebus/CASCHMITZ/Desktop/dataDir/' + pathfilename
            dfile.comment = ''
            dfile.authed = current_user.get_id()
            db.session.add(dfile)
            db.session.commit()
    return 'Added'

@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_file():
    if request.method == 'POST':
        idnum = request.form.get('id', type=int)
        table = request.form.get('table', type=str)
        user = current_user
        if table == 'File':
            instance = db.session.query(dataFile).filter_by(id=idnum).first()
            db.session.delete(instance)
        if table == 'Meta':
            instance = user.metaData.filter_by(id=idnum).first()
            db.session.delete(instance)
        db.session.commit()
    return 'Deleted'

@app.route('/save_comment', methods=['GET', 'POST'])
@login_required
def save_comment():
    if request.method == 'POST':
        comment = request.form.get('comment', type=str)
        idprev = request.form.get('idprev', type=int)
        formatting = request.form.get('format', type=int)
        if idprev is not None and formatting is None:
            instance = db.session.query(dataFile).filter_by(id=idprev).first()
            instance.comment = comment
            db.session.commit()
        if idprev is not None and formatting == 1:
            instance = db.session.query(dataFile).filter_by(id=idprev).first()
            instance.comment = comment
            format_instance = db.session.query(fileFormat).filter_by(path=instance.path).first()
            format_instance.comment = comment
            db.session.commit()
    return 'Saved'

@app.route('/show_comment', methods=['GET', 'POST'])
@login_required
def show_comment():
    if request.method == 'POST':
        send_comment = ''
        idnext = request.form.get('idnext', type=int)
        if idnext is not None:
            instance = db.session.query(dataFile).filter_by(id=idnext).first()
            if instance is not None:
                send_comment = instance.comment
        return send_comment


@app.route('/make_name', methods=['GET', 'POST'])
@login_required
def make_name():
    if request.method == 'POST':
        idthis = request.form.get('id', type=int)
        instance = db.session.query(dataFile).filter_by(id=idthis).first()
        lastMod = modified(instance.path)
        temp = lastMod.strftime("%Y-%m-%d %H:%M:%S")
        modname = str(instance.name) + ' ' + temp
        return str(modname)

@app.route('/del_entry', methods=['GET', 'POST'])
@login_required
def delete_entry():
    user = current_user
    if request.method == 'POST':
        idthis = request.form.get('id', type=int)
        if idthis == -1:
            user.metaData.delete()
        else:
            instance = db.session.query(metaData).filter_by(id=idthis).first()
            db.session.delete(instance)
        db.session.commit()
    return 'Deleted'

@app.route('/add_entry', methods=['GET', 'POST'])
@login_required
def add_entry():
    user = current_user
    if request.method == 'POST':
        idthis = request.form.get('id', type=int)
        file_instance = db.session.query(dataFile).filter_by(id=idthis).first()
        format_instance = db.session.query(fileFormat).filter_by(path=file_instance.path).first()
        if format_instance != None:
            form = populate_from_instance(format_instance)
            meta = metaData()
            form.populate_obj(meta)
            meta.user = user
            meta.plot = format_instance.plot
            meta.comment = file_instance.comment
            meta.name = file_instance.name
            db.session.add(meta)
            db.session.commit()
    return 'Added'











def unicodeFloat_to_int(unicode):
    convertF = float(unicode)
    convertI = int(convertF)
    return convertI


def splitForm(form):
    columns = []
    bools = []
    for field in form:
        if field.type == 'FloatField':
            columns.append(field)
        else:
            bools.append(field)
    return columns, bools

def modified(path):
    """Returns modified time of this."""
    return datetime.fromtimestamp(os.path.getmtime(path))

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


@run_once
def setupAllMeta():
    allMeta = MetaDataAll()
    return allMeta


def readAscii(path):
    count = 0
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("%File name:"):
                path = line.split('W:', 1)[-1]
                name = path.rsplit('/', 1)[-1]
            if line.startswith("%"):
                continue
            line = line[1:]
            line = line.split("   ")
            if count == 0:
                data = [[] for x in xrange(len(line))]
            count += 1
            for i in range(len(line)):
                data[i].append(line[i])
    return data, name, path


def plotData(data, used, againstE):
    plt.close()
    fig = plt.figure(figsize=(10, 7))
    xs = []
    ys = []

    for idx, column in enumerate(data):
        for i in used:
            if (idx + 1) == i:
                xs = range(1, len(data[idx]) + 1)
                ys = data[idx]
                if againstE:
                    xs = data[0]
                ax = plt.plot(xs, ys)

    if not used:
        ax = plt.plot(ys, ys)
    code = mpld3.fig_to_html(fig)
    plt.close()
    return code

def energy_xtal(data, a1, a2):
    energy = []
    a1Dat = data[a1]
    a2Dat = data[a2]
    a1Dat = [float(i) for i in a1Dat]
    a2Dat = [float(i) for i in a2Dat]
    hrm_e0 = 14412500.0
    hrm_bragg1 = 18.4704
    hrm_bragg2 = 77.5328
    hrm_tan1 = math.tan(math.radians(hrm_bragg1))
    hrm_tan2 = math.tan(math.radians(hrm_bragg2))

    a = 1.0e-6 * hrm_e0 / (hrm_tan1 + hrm_tan2)
    b = a1Dat[0] - a2Dat[0]
    for i in range(len(a1Dat)):
        energy.append(a * (a1Dat[i] - a2Dat[i] - b))
    return energy

def temp_corr(data, t1, t2):
    energy = []
    t1Dat = data[t1]
    t2Dat = data[t2]
    t1Dat = [float(i) for i in t1Dat]
    t2Dat = [float(i) for i in t2Dat]
    hrm_e0 = 14412500.0
    hrm_bragg1 = 18.4704
    hrm_bragg2 = 77.5328
    hrm_tan1 = math.tan(math.radians(hrm_bragg1))
    hrm_tan2 = math.tan(math.radians(hrm_bragg2))
    hrm_alpha1 = 2.6e-6
    hrm_alpha2 = 2.6e-6
    at1 = hrm_alpha1 * hrm_tan1
    at2 = hrm_alpha2 * hrm_tan2

    a = - hrm_e0 / (hrm_tan1 + hrm_tan2)
    b = at1 * t1Dat[0] + at2 * t2Dat[0]
    for i in range(len(t1Dat)):
        energy.append(a * (at1 * t1Dat[i] + at2 * t2Dat[i] - b))
    return energy

def signal_normalized(data, sCol, nCol):
    signal = []
    sDat = data[sCol]
    nDat = data[nCol]
    sDat = [float(i) for i in sDat]
    nDat = [float(i) for i in nDat]

    ave = numpy.mean(nDat)
    for i in range(len(sDat)):
        signal.append(sDat[i] * ave / nDat[i])
    return signal

def norm_factors(data, nCol):
    norm = []
    nDat = data[nCol]
    nDat = [float(i) for i in nDat]

    ave = numpy.mean(nDat)
    for i in range(len(nDat)):
        norm.append(ave / nDat[i])
    return norm









class MetaDataOne:
    def __init__(self, checkboxes, columns, name, comment, path):
        # Information on current state
        self.checkboxes = checkboxes
        self.columns = columns
        self.name = name
        self.cmnt = comment
        self.path = path

        # Information stored in list
        self.info = {}
        self.storeInfo()

    # Separates information into two lists based on if the box is checked or not
    def storeInfo(self):
        columnD = {0: 'energy', 1: 'xtal1A', 2: 'xtal2A', 3: 'xtal1T', 4: 'xtal2T', 5: 'tempCorr', 6: 'signal',
                   7: 'signalNorm', 8: 'norm', 9: 'normFac', 10: 'extra'}

        for i in range(len(columnD)):
            if columnD[i] in self.checkboxes:
                self.info[str(columnD[i])] = [self.columns[columnD[i]], True]
            else:
                self.info[str(columnD[i])] = [self.columns[columnD[i]], False]

    def update(self, checkboxes, columns, name, comment, path):
        # Update all variables with current information from GUI
        self.checkboxes = checkboxes
        self.columns = columns
        self.name = name
        self.cmnt = comment
        self.path = path

        self.storeInfo()
        return self


class MetaDataAll:
    def __init__(self):
        self.allMeta = []

    # Append current scan object to list of all scan objects
    def addData(self, oneMeta):
        self.allMeta.append(oneMeta)

    # Return true if the current scan object has the same file name as a scan object already recorded  NOT NEEDED?
    def checkDuplicate(self, oneMeta):
        for i in range(len(self.allMeta)):
            if self.allMeta[i].name == oneMeta.name:
                return True
        return False

    # Replace the duplicate old information with new information  NOT NEEDED?
    def updateDuplicate(self, oneMeta):
        for i in range(len(self.allMeta)):
            if self.allMeta[i].name == oneMeta.name:
                self.allMeta[i] = oneMeta

    def load(self, xml):
        n = xml.firstChild()
        while n:
            e = n.toElement()
            if e:
                name = (e.tagName())
                print (name)
            n = n.nextSibling()

    # Converts and returns the list of all scans in xml format
    def save(self):
        doc = QtXml.QDomDocument("Test")
        root = doc.createElement("MetaData")

        doc.appendChild(root)

        for i in range(len(self.allMeta)):
            scantag = doc.createElement("Scan")
            root.appendChild(scantag)
            pathtag = doc.createElement("Path")
            scantag.appendChild(pathtag)
            path = doc.createTextNode(self.allMeta[i].path)
            pathtag.appendChild(path)

            nametag = doc.createElement("Name")
            scantag.appendChild(nametag)
            name = doc.createTextNode(self.allMeta[i].name)
            nametag.appendChild(name)

            cmntag = doc.createElement("Comment")
            scantag.appendChild(cmntag)
            cmnt = doc.createTextNode(self.allMeta[i].cmnt)
            cmntag.appendChild(cmnt)

            for key in self.allMeta[i].info:
                tempTag = doc.createElement(str(key))
                scantag.appendChild(tempTag)
                tempVal = doc.createTextNode(str(self.allMeta[i].info.get(key)[0]))
                tempTag.appendChild(tempVal)
                tempAtt = doc.createAttribute("Enabled")
                if self.allMeta[i].info.get(key)[1]:
                    tempAtt.setValue("True")
                else:
                    tempAtt.setValue("False")
                tempTag.setAttributeNode(tempAtt)

        xml = doc.toString()
        return xml


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
