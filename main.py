import json
from os import stat
import re
from this import d
from tkinter.messagebox import NO
from unittest import result
import uuid
import os
import pandas as pd
import shutil
import zipfile

from flask import Flask, redirect, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy

from ocr import ocr

app = Flask(__name__, template_folder='templates', static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:pswd@ip:3306/db'
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = True
db = SQLAlchemy(app)


class USER(db.Model):
    name = db.Column(db.Text)
    uid = db.Column(db.String(15), primary_key=True)
    password = db.Column(db.Text)
    cookies = db.Column(db.String(37), unique=True)

    def __init__(self, name, uid, password):
        self.name = name
        self.uid = uid
        self.password = password
        self.cookies = str(uuid.uuid4())


class RECORDS(db.Model):
    sname = db.Column(db.Text)
    sid = db.Column(db.String(37))
    recordid = db.Column(db.String(37), primary_key=True)
    JKM_id = db.Column(db.String(37), unique=True)
    HS_id = db.Column(db.String(37), unique=True)
    pid = db.Column(db.String(37))
    status = db.Column(db.Text)
    conclusion = db.Column(db.Text)

    def __init__(self, sname, sid, JKM_id, HS_id, pid, status, conclusion):
        self.sname = sname
        self.sid = sid
        self.JKM_id = JKM_id
        self.HS_id = HS_id
        self.pid = pid
        self.recordid = str(uuid.uuid4())
        self.status = status
        self.conclusion = conclusion


class PAGES(db.Model):
    pname = db.Column(db.Text)
    pid = db.Column(db.String(37), primary_key=True)
    JKM = db.Column(db.Boolean)
    HS = db.Column(db.Boolean)
    ownerid = db.Column(db.String(37))

    def __init__(self, pname, JKM, HS, ownerid):
        self.pname = pname
        self.JKM = JKM
        self.HS = HS
        self.ownerid = ownerid
        self.pid = str(uuid.uuid4())


@app.route('/')
def _G():
    return redirect('/login')


@app.route('/login', methods=["get"])
def _loginG():
    cookie = request.cookies.get("session")
    if cookie != None:
        currentUser = USER.query.filter_by(cookies=cookie)
        if currentUser.first() != None:
            return redirect('/backend')
    return render_template('login.html', info="")


@app.route('/login', methods=["post"])
def _loginP():
    data = dict(request.form)
    currentUser = USER.query.filter_by(uid=data["inputId"])
    if currentUser.first() == None:
        return "<script>alert('用户名不存在');history.go(-1);</script>"
    elif currentUser.first().password == data["inputPassword"]:
        nuuid = str(uuid.uuid4())
        currentUser.update({USER.cookies: nuuid})
        responce = make_response(redirect('/backend'))
        try:
            data["remember-me"]
            responce.set_cookie("session", nuuid, max_age=604800)
        except:
            responce.set_cookie("session", nuuid)
        return responce
    else:
        return "<script>alert('用户名或密码错误');history.go(-1);</script>"


@app.route('/backend', methods=["get"])
def _backendG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    pages = PAGES.query.filter_by(ownerid=currentUser.first().uid)
    empty = ""
    if pages.first() == None:
        empty = "您当前还没有有效的收集表，点击上方按钮新建一个吧!"
    return render_template('backend.html', name=currentUser.first().name, pages=pages, empty=empty)


@app.route('/logout', methods=["get"])
def _logoutG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    currentUser.update({USER.cookies: None})
    return redirect('/login')


@app.route('/new', methods=["get"])
def _newG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    return render_template('new.html', name=currentUser.first().name)


@app.route('/new', methods=["post"])
def _newP():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    data = dict(request.form)
    if data['projectName'] == "":
        return "<script>alert('请输入有效的名称');history.go(-1);</script>"
    try:
        data['JKM']
        JKM = True
    except:
        JKM = False
    try:
        data['HS']
        HS = True
    except:
        HS = False
    if(JKM == False and HS == False):
        return "<script>alert('至少选择一项截图提交');history.go(-1);</script>"
    newpage = PAGES(data['projectName'], JKM, HS, currentUser.first().uid)
    db.session.add(newpage)
    return redirect('/manage?pid='+newpage.pid)

@app.route('/manage', methods=["get"])
def _manageG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    pid = request.args.get("pid")
    page = PAGES.query.filter_by(pid=pid)
    if page.first() == None:
        return redirect('/backend')
    if currentUser.first().uid != page.first().ownerid:
        return redirect('/backend')
    records = RECORDS.query.filter_by(pid=pid)
    if page.first().JKM == True:
        JKMchecked = "checked"
    else:
        JKMchecked = ""
    if page.first().HS == True:
        HSchecked = "checked"
    else:
        HSchecked = ""
    return render_template('detail.html', pid=pid, name=currentUser.first().name, records=records, JKMchecked=JKMchecked, HSchecked=HSchecked, project=page.first().pname, count=len(list(records)))

@app.route('/manage', methods=["post"])
def _manageP():
    cookie = request.cookies.get("session")
    data = dict(request.form)
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    pid = data["pid"]
    page = PAGES.query.filter_by(pid=pid)
    if page.first() == None:
        print(1)
        return redirect('/backend')
    if currentUser.first().uid != page.first().ownerid:
        print(2)
        return redirect('/backend')  
    if data['projectName'] == "":
        return "<script>alert('请输入有效的名称');history.go(-1);</script>"
    try:
        data['JKM']
        JKM = True
    except:
        JKM = False
    try:
        data['HS']
        HS = True
    except:
        HS = False
    if(JKM == False and HS == False):
        return "<script>alert('至少选择一项截图提交');history.go(-1);</script>"
    page.update({PAGES.pname: data['projectName'], PAGES.JKM: JKM, PAGES.HS: HS})
    return "<script>alert('修改成功');history.go(-1);</script>"



@app.route('/view', methods=["get"])
def _viewG():
    recordid = request.args.get("recordid")
    record = RECORDS.query.filter_by(recordid=recordid).first()
    JKMid = record.JKM_id
    HSid = record.HS_id
    print(JKMid, HSid)
    result = ""
    if JKMid!=None:
        result += '<td><img src="static/uploads/%s.jpg" border=0></td>'%str(JKMid)
    if HSid!=None:
        result += '<td><img src="static/uploads/%s.jpg" border=0></td>'%str(HSid)
    return result


@app.route('/upload', methods=["get"])
def _uploadG():
    pid = request.args.get("pid")
    page = PAGES.query.filter_by(pid=pid)
    if page.first().JKM == True:
        JKMs = "form-group"
    else:
        JKMs = "hidden"
    if page.first().HS == True:
        HSs = "form-group"
    else:
        HSs = "hidden"
    return render_template('upload.html', JKMishidden=JKMs, HSishidden=HSs, project=page.first().pname, pid=pid)

@app.route('/upload', methods=["post"])
def _uploadP():
    data = dict(request.form)
    print(data)
    pid = data["pid"]
    page = PAGES.query.filter_by(pid=pid)
    if page.first().JKM == True:
        JKMs = "form-group"
    else:
        JKMs = "hidden"
    if page.first().HS == True:
        HSs = "form-group"
    else:
        HSs = "hidden"
    conclusion = ""
    status = 0 # -1:识别失败 0:正常 1:异常
    JKMuuid, HSuuid = None, None
    JKMFile = request.files['JKMFile']
    if JKMFile.filename != '':
        JKMuuid = str(uuid.uuid4())
        JKMFile.save("static/uploads/%s.jpg"%JKMuuid)
        jkmS = ocr.JKM_OCR("static/uploads/%s.jpg"%JKMuuid) # -1失败，0绿码，1黄码，2红码
        if jkmS == 1 or jkmS ==2:
            status = 1
            conclusion+="红黄码异常！"
        elif jkmS==-1:
            status=-1
            conclusion+="健康码识别失败，请复核。"
        else:
            conclusion+="绿码"
    HSFile = request.files['HSFile']
    if HSFile.filename != '':
        HSuuid = str(uuid.uuid4())
        HSFile.save("static/uploads/%s.jpg"%HSuuid)
        hsS = ocr.HS_OCR("static/uploads/%s.jpg"%HSuuid) # （阴性， 采样时间， 报告时间）
        if hsS[0] == "阳性" or hsS == "待复核":
            status=1
            conclusion+="核酸阳性！"
        elif hsS[0] == "阴性":
            conclusion+="核酸阴性，采样%s，报告%s"%(hsS[1], hsS[2])
        else:
            conclusion+="核酸识别失败，请复核"
    if status==-1:
        sLabel = "warning"
    elif status==1:
        sLabel = "danger"
    else:
        sLabel = "success"
    newrecord = RECORDS(data["name"], data['sid'], JKMuuid, HSuuid, pid, sLabel, conclusion)
    db.session.add(newrecord)
    return "<script>alert('上传成功');history.go(-1);;</script>"


@app.route('/delete', methods=["get"])
def _deleteG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    pid = request.args.get("pid")
    page = PAGES.query.filter_by(pid=pid)
    if page.first() == None:
        return redirect('/backend')
    if currentUser.first().uid != page.first().ownerid:
        return redirect('/backend')
    db.session.delete(page.first())
    db.session.query(RECORDS).filter(RECORDS.pid==pid).delete()
    return "<script>alert('删除成功');window.location.replace(document.referrer);</script>"

def zip(dirpath, name):
    f = zipfile.ZipFile(dirpath+name,'w',zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标根路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath= path.replace(dirpath,'') 
        for filename in filenames:
            f.write(os.path.join(path, filename), os.path.join(fpath, filename))
    f.close()


@app.route('/download', methods=["get"])
def _downloadG():
    cookie = request.cookies.get("session")
    currentUser = USER.query.filter_by(cookies=cookie)
    if cookie == None:
        return redirect('/login')
    if currentUser.first() == None:
        return redirect('/login')
    pid = request.args.get("pid")
    page = PAGES.query.filter_by(pid=pid).first()
    if page == None:
        return redirect('/backend')
    if currentUser.first().uid != page.ownerid:
        return redirect('/backend')
    records = RECORDS.query.filter_by(pid=pid)
    try:
        shutil.rmtree("static/downloads/%s/"%pid)
    except:
        pass
    os.mkdir("static/downloads/%s/"%pid)
    resultxls = []
    for each in records:
        txls = [each.sname, each.sid, each.conclusion]
        resultxls.append(txls)
    df = pd.DataFrame(resultxls,columns=["姓名","学号","识别结果"])
    writer = pd.ExcelWriter("static/downloads/%s/result.xlsx"%pid)
    df.to_excel(writer)
    writer.save() 
    if page.JKM == True:
        os.mkdir("static/downloads/%s/JKM/"%pid)
        for each in records:
            shutil.copyfile("static/uploads/%s.jpg"%each.JKM_id, "static/downloads/%s/JKM/%s.jpg"%(pid, each.sname))
    if page.HS == True:
        os.mkdir("static/downloads/%s/HS/"%pid)
        for each in records:
            shutil.copyfile("static/uploads/%s.jpg"%each.HS_id, "static/downloads/%s/HS/%s.jpg"%(pid, each.sname))
    zip("static/downloads/", "%s.zip"%pid)
    return redirect("/static/downloads/%s.zip"%pid)
            




if __name__ == '__main__':
    app.run(debug=True)
