<<<<<<< HEAD
#Assumptions
# 1. During registration - role{0:volunteers, 1:ngo, 2: donor}, type{0:student,1:professional}
# 2. chapter head login will be using their volunteer registration details and the username will be checked in the chapter db

#Flow
# 3. for volunteers : register->test->submit->chapter assigned->register for event when it is created
# 4. for chapter head: register as vol->test->submit->chapter assigned->chapter head status confirmed->notify of events
# 5. for ngo: register->name checked->confimation mail->upload event->get volunteers
# 6. for donor: register->details->donate

#TODO
# 1. login credentials
# 2. assigning chapter head (hardcode)
# 3. ngo event registration
# 4. volunteer finding algorithm
# 5. mailing chapter heads
# 6. payment gateway
# 7. hardocding the ngo types
# 8. hardcoding the volunteer traits
# 9. creating UI
# 10. create dynamic URL for events

from flask import Flask, session, redirect, url_for, escape, request,jsonify, Response, render_template
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
import datetime
#import bcrypt
from flask.ext.bcrypt import Bcrypt
import requests, bs4
app = Flask(__name__)
#app.config['SECRET KEY']='5506e74'
app.secret_key = "5506e74"

client = MongoClient()
db = client.noob_db
bcrypt=Bcrypt(app)

@app.route('/')
def start():
    session.pop('user',None)
    print(session, file=sys.stdout)
    return render_template("home.html")
    # if 'user' in session:
    #     return jsonify({'user':1,"session":session['user']})
    # else:
    #     return jsonify({"user":0,"session":session['user']})



@app.route('/register',methods=['POST'])
def register():
    if request.method =='POST':
        if request.is_json:
            content = request.get_json(force=True)
            #print(content,file=sys.stdout)
            if content['role'] in [0,1,2]:
                if content['role']==0:
                    if db.volunteers.find({"$and":[{'name':{"$eq": content['name']}},{'emailid':{"$eq":content['emailid']}}]}).count()== 0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        i_d = db.volunteers.insert(content)
                        db.volunteers.insert({"chapter-head":0})
                        session['user']= [content['name'],content['role']]
                        location="/test/"+str(i_d)
                        return jsonify({"location":location,"role":content['role']})
                    else:
                        return jsonify({"error":"Existing User"})
                elif content['role']==1:
                    if db.ngo.find({"$and":[{'name':{"$eq": content['name']}},{'registration':{"$eq":content['registration']}}]}).count()==0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        db.ngo.insert(content)
                        session['user']= [content['name'],content['role']]
                        confirmation(reg = content['registration'],mail = content['emailid'], name = content['name'], state = content['state'], city = content['city'])
                        return jsonify({"status":200})
                    else:
                        return jsonify({"error":"Existing User"})
                elif content['role']==2:
                    if db.donor.find({"$and":[{'name':{"$eq": content['name']}},{'emailid':{"$eq":content['emailid']}}]}).count()==0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        db.donor.insert(content)
                        session['user']= [content['name'],content['role']]
                        return jsonify({"status":200})
                    else:
                        return jsonify({"error":"Existing User"})
            else:
                return redirect(url_for('badData'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user' in session:
        print(session, file=sys.stdout)
        return "Already in session: %s" % session['user'][0]
    else:
        if request.method =='GET':
            return render_template('index.html')
        else:
            content = request.get_json(force=True)
            username = content['username']
            #print(username, file=sys.stdout)
            password =content['password']
            # print(password, file=sys.stdout)
            # print(request.form['role'], file=sys.stdout)
            if int(content['role'])==1:
                pw_hash = db.ngo.find_one({"username":content['username']},{"pass":1,"_id":0,"name":1})
                print(pw_hash, file=sys.stdout)
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        print("Inside login")
                        session['user']= [pw_hash['name'],1]
                        #return redirect(url_for('dashboard'))
                        return "Session ngo created"

                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            elif int(content['role'])==2:
                pw_hash = db.donor.find_one({"username":username},{"pass":1,"_id":0,"name":1})
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        session['user']= [pw_hash['name'],2]
                        return redirect(url_for('dashboard'))
                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            elif int(content['role'])==0:
                pw_hash = db.volunteers.find_one({"username":username},{"pass":1,"_id":0,"name":1,"chapter-head":1})
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        if pw_hash['chapter-head']:
                            session['user']= [pw_hash['name'],0]
                            return redirect(url_for('dashboard'))
                        else:
                            return jsonify({"login":-2})
                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            else:
                return redirect(url_for('badData'))


@app.route('/chapter')
def chapterAssign(testid):
    ''' Adds the volunteer details to the campus chapter db. Volunteers stored as <list> in the db.
    TODO: sends mail to volunteer once the registration and chapter assigning is done'''
    chapter = db.chapter
    # check for campus
    x = db.volunteers.find_one({"_id":ObjectId(testid)},{"campus":1,"name":1})
    #print(x,file=sys.stdout)
    if db.chapter.find_one({"campus":{"$eq":x['campus']}}):
        print('inside')
        db.chapter.update({"campus":x['campus']},{"$push":{"volunteer":x['_id']}})
        ch_id = db.chapter.update({"campus":x['campus']},{"$push":{"volunteer":x['name']}})
        i_d = db.chapter.find_one({"campus":x['campus']},{"_id":1})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter":i_d['_id']}})
        #TODO Send email to volunteer and chapter head

    else:
        print('not inside')
        i_d = db.chapter.insert({"campus":x['campus']})
        db.chapter.update({"_id":ObjectId(str(i_d))},{"$push":{"volunteer":x['_id']}})
        ch_id = db.chapter.update({"_id":ObjectId(str(i_d))},{"$push":{"volunteer":x['name']}})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter":i_d}})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter-head":1}})
        #TODO Send email to recipient


@app.route('/test/<testid>',methods=['GET'])
def test(testid):
    ''' Renders the test for the user with 'testid'. Frontend: Then POST data to /test/<testid> to save it on the db.
    Using <testid> along with sessions because of 1. easier 2. easier to manage if the session expires'''
    if 'user' in session:
        print(session,file=sys.stdout)
        return jsonify({'user':1,'testid':testid})
    else:
        return jsonify({"user":0,'testid':testid})
    # return 'Test for user with ObjectId as %s' % testid

@app.route('/test/<testid>',methods=['POST'])
def savetest(testid):
    '''POST data is stored as primary and secondary attribute fields in volunteer db'''
    '''callback: chapterAssign(data)'''
    contents = request.get_json()
    #checking for valid user
    if db.volunteers.find({"$and":[{"_id":ObjectId(testid)},{"primary":{"$eq":0}},{"secondary":{"$eq":0}}]}).count()==1:
        try:
            db.volunteers.update_one({"_id":ObjectId(str(testid))},{"$set":{"primary":contents['primary'],"secondary":contents['secondary']}})
            chapterAssign(testid)
        except Exception as e:
            print(str(e), file=sys.stdout)
            return jsonify({"error":"DB insert failure"})
    else:
        return redirect(url_for('badData'))

@app.route("/donor/donate", methods=['POST'])
def donorDonation():
    if 'user' in session:
        if session['user'][1]==2:
            contents = request.get_json
            amount = contents['amount']
            bank = contents['bank']
            account_no = contents['accountno']
            x = db.donor.find_one({"name":contents['name']},{"_id":1})
            db.donation.insert({
                "_id":x['_id'],
                "amount":amount,
                "bank":bank,
                "account_no":account_no
                })
            return jsonify({"status":200})


@app.route("/donor/history",methods=['POST'])
def history():
    if 'user' in session and session['user'][1]==2:
        contents = request.get_json
        x =  db.donor.find_one({"name":contents['name']},{"_id":1})
        y = db.donation.find({"_id":x['_id']})
        for row in x:
                results.append(row)
                return toJson(results)



@app.route
@app.route('/event',methods=['POST'])
def eventRegister():
    if 'user' in session:
        if session['user'][1]==1:
            content = request.get_json(force=True)
            name= content['eventname']
            user= session['user'][0]
            minimum = content['minimum']
            maximum = content['maximum']
            startDate =  datetime.datetime.strptime(content['startdate'], '%d-%m-%y').date().isoformat()
            endDate = datetime.datetime.strptime(content['enddate'], '%d-%m-%y').date().isoformat()
            details = content['details']
            traits = list(content['triats'])
            date = datetime.datetime.strptime(content['date'], '%d-%m-%y').date().isoformat()
            try:
                i_d = db.event.insert(
                    {
                    "name":name.replace(" ","-"),
                    "ngo":user,
                    "min":minimum,
                    "max":maximum,
                    "starts":ISODate(startDate),
                    "end":ISODate(endDate),
                    "details":details,
                    "traits":traits,
                    "date":date
                    });
                return jsonify({"status":200})
            except Exception as e:
                print(str(e), file = sys.stdout)
            #createEventURL(id=i_d, eventname=name)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route("/event/<eventname>", methods=['GET', 'POST'])
def registerEvent(eventname):
    if request.method=='GET':
        try:
            x = db.event.find_one({"name":eventname},{"ngo":1})

            if x:
                #return render_template('register.html')
                pass
            else:
                return redirect(url_for("start"))

        except Exception as e:
            print(str(e), file=sys.stdout)
    else:
        x = db.event.find_one({"name":eventname},{"end":1,"traits":1,"_id":0})
        if x['end'].isoformat() > datetime.date.today().isoformat():
            vol = db.volunteers.find_one({"name":content['name']},{"chapter":1,"_id":1,"primary":1})
            chap = db.chapter.find_one({"_id":vol['chapter']})
            if chap:
                if vol['primary'] in x['traits']:
                    db.event.update({"name":eventname},{"$push":{"volunteers":vol['_id']}})

@app.route("/ngo-dashboard/events",methods=['POST'])
def ngoDashEvents():
    if 'user' in session:
        if session['user'][1]==1:
            x = db.event.find({"name":session['user'][0]},{"_id":0})
            results =[]
            for row in x:
                results.append(row)
                return toJson(results)


# def getNGO():
#     pg = 1
#     url = "http://ngodarpan.gov.in/index.php/home/statewise_ngo/3203/27/"
#     names=[]
#     reg=[]
#     while(pg<321):
#         res = requests.get((url+str(pg)))
#         res.raise_for_status()
#         soup = bs4.BeautifulSoup(res.text,"html.parser")
#         table = soup.select("td")
#         #print(table)
#         for x in range(1,51,5):
#             names.append(table[x].getText().lstrip())
#         for x in range(2,51,5):
#             reg.append(table[x].getText().lstrip().split(',')[0])
#         pg+=1
#     db.ngolist.insert({"name":name,"reg":reg})


@app.route('/dashboard', methods=['POST'])
def dashboard():
    '''Should redirect here once login is completed'''
    pass

def confirmation(name, mail, reg, state, city):
    url = "http://"+state+".ngosindia.com/"+city+"-ngos/"
    res = requests.get(url)
    res.raise_for_status()
    nss = bs4.BeautifulSoup(res.text,"html.parser")
    elem = nss.select('.lcp_catlist > li')
    ls =[]
    for element in elem:
        ls.append(element.getText().split(',')[0])

    print(ls,file=sys.stdout)
    if name in ls:
        #The NGO name has been confirmed. Could not find a link for registration number verification
    # pg = 1
    # url = "http://ngodarpan.gov.in/index.php/home/statewise_ngo/3203/27/"
    # names=[]
    # reg=[]
    # while(pg<321):
    #     res = requests.get((url+str(pg)))
    #     res.raise_for_status()
    #     soup = bs4.BeautifulSoup(res.text,"html.parser")
    #     table = soup.select("td")
    #     #print(table)
    #     for x in range(1,51,5):
    #         names.append(table[x].getText().lstrip())
    #     for x in range(2,51,5):
    #         reg.append(table[x].getText().lstrip().split(',')[0])
    #     pg+=1
    # print(names, file=sys.stdout)
    # print(reg, file=sys.stdout)

        ngo = db.ngo
        x = ngo.update({"name":{"$eq":name}},{"$set":{"name-verified":True}})
        #TODO- send mail to confirm that the ngo has been added
    else:
        ngo = db.ngo
        x = ngo.update({"name":{"$eq":name}},{"$set":{"name-verified":False}})

#---------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------

@app.route('/abc/admin/login',methods=['GET','POST'])
def adminLogin():
    if 'user' in session:
        return "No admin rights"
    if 'admin' in session:
        return "Already logged in"
    else:
        if request.method =='GET':
            #render adminLogin.html
            pass
        else:
            content = request.get_json(force=True)
            username = content['username']
            password = content['password']
            pw_hash = db.admin.find_one({"username":username},{"pass":1,"_id":0,"id":1})
            if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        session['admin']=pw_hash['id']
                    else:
                        return jsonify({"login":0})
            else:
                return jsonify({"login":-1})


@app.route('/getvolunteers',methods=['POST'])
def volList():
    pageNumber = int(request.headers.get('Pagenumber'))
    pagelimit = int(request.headers.get('Pagelimit'))
    # print(pageNumber,file=sys.stdout)
    # print(pagelimit,file=sys.stdout)
    try:
        # print("entered")
        x = db.volunteers.find().sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
        json_results = []
        for result in x:
            json_results.append(result)
            return toJson(json_results)
    except:
        return redirect(url_for('badData'))

@app.route('/getngos/<int:validated>',methods=['POST'])
def ngoList(validated):
    pageNumber = int(request.headers.get('Pagenumber'))
    pagelimit = int(request.headers.get('Pagelimit'))
    if validated:
        try:
            x = db.ngo.find({"name-verified":True}).sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
            json_results=[]
            for result in x:
                json_results.append(result)
                return toJson(json_results)
        except:
            return redirect(url_for('badData'))
    else:
        try:
            x = db.ngo.find({"name-verified":False}).sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
            json_results=[]
            for result in x:
                json_results.append(result)
                return toJson(json_results)
        except:
            return redirect(url_for('badData'))

@app.route('/abc/admin/register',methods=['GET','POST'])
def adminRegister():
    if 'user' in session:
        return "No admin rights"
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    else:
        username = request.form['username']
        password = request.form['password']
        employeeid = request.form['employeeid']
        if db.admin.find({"$and":[{'id':{"$eq": employeeid}},{'username':{"$eq":username}}]}).count()==0:
            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            try:
                db.admin.insert({"username":username,"pass":pw_hash,"id":employeeid})
            except Exception as e:
                print(str(e), file=sys.stdout)
        else:
            return jsonify({"register":0})


@app.route('/error')
def badData():
    return 'Incorrect data'

def toJson(data):
    """Convert Mongo object(s) to JSON"""
    #print(type(data), file=sys.stdout)
=======
#Assumptions
# 1. During registration - role{0:volunteers, 1:ngo, 2: donor}, type{0:student,1:professional}
# 2. chapter head login will be using their volunteer registration details and the username will be checked in the chapter db

#Flow
# 3. for volunteers : register->test->submit->chapter assigned->register for event when it is created
# 4. for chapter head: register as vol->test->submit->chapter assigned->chapter head status confirmed->notify of events
# 5. for ngo: register->name checked->confimation mail->upload event->get volunteers
# 6. for donor: register->details->donate

#TODO
# 1. login credentials
# 2. assigning chapter head (hardcode)
# 3. ngo event registration
# 4. volunteer finding algorithm
# 5. mailing chapter heads
# 6. payment gateway
# 7. hardocding the ngo types
# 8. hardcoding the volunteer traits
# 9. creating UI
# 10. create dynamic URL for events

from flask import Flask, session, redirect, url_for, escape, request,jsonify, Response, render_template
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
import datetime
#import bcrypt
from flask.ext.bcrypt import Bcrypt
import requests, bs4
app = Flask(__name__)
#app.config['SECRET KEY']='5506e74'
app.secret_key = "5506e74"

client = MongoClient()
db = client.noob_db
bcrypt=Bcrypt(app)

@app.route('/')
def start():
    session.pop('user',None)
    print(session, file=sys.stdout)
    return render_template("home.html")
    # if 'user' in session:
    #     return jsonify({'user':1,"session":session['user']})
    # else:
    #     return jsonify({"user":0,"session":session['user']})



@app.route('/register',methods=['POST'])
def register():
    if request.method =='POST':
        if request.is_json:
            content = request.get_json(force=True)
            #print(content,file=sys.stdout)
            if content['role'] in [0,1,2]:
                if content['role']==0:
                    if db.volunteers.find({"$and":[{'name':{"$eq": content['name']}},{'emailid':{"$eq":content['emailid']}}]}).count()== 0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        i_d = db.volunteers.insert(content)
                        db.volunteers.insert({"chapter-head":0})
                        session['user']= [content['name'],content['role']]
                        location="/test/"+str(i_d)
                        return jsonify({"location":location,"role":content['role']})
                    else:
                        return jsonify({"error":"Existing User"})
                elif content['role']==1:
                    if db.ngo.find({"$and":[{'name':{"$eq": content['name']}},{'registration':{"$eq":content['registration']}}]}).count()==0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        db.ngo.insert(content)
                        session['user']= [content['name'],content['role']]
                        confirmation(reg = content['registration'],mail = content['emailid'], name = content['name'], state = content['state'], city = content['city'])
                        return jsonify({"status":200})
                    else:
                        return jsonify({"error":"Existing User"})
                elif content['role']==2:
                    if db.donor.find({"$and":[{'name':{"$eq": content['name']}},{'emailid':{"$eq":content['emailid']}}]}).count()==0:
                        content['pass'] =  bcrypt.generate_password_hash(content['pass']).decode('utf-8')
                        db.donor.insert(content)
                        session['user']= [content['name'],content['role']]
                        return jsonify({"status":200})
                    else:
                        return jsonify({"error":"Existing User"})
            else:
                return redirect(url_for('badData'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user' in session:
        print(session, file=sys.stdout)
        return "Already in session: %s" % session['user'][0]
    else:
        if request.method =='GET':
            return render_template('index.html')
        else:
            content = request.get_json(force=True)
            username = content['username']
            #print(username, file=sys.stdout)
            password =content['password']
            # print(password, file=sys.stdout)
            # print(request.form['role'], file=sys.stdout)
            if int(content['role'])==1:
                pw_hash = db.ngo.find_one({"username":content['username']},{"pass":1,"_id":0,"name":1})
                print(pw_hash, file=sys.stdout)
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        print("Inside login")
                        session['user']= [pw_hash['name'],1]
                        #return redirect(url_for('dashboard'))
                        return "Session ngo created"

                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            elif int(content['role'])==2:
                pw_hash = db.donor.find_one({"username":username},{"pass":1,"_id":0,"name":1})
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        session['user']= [pw_hash['name'],2]
                        return redirect(url_for('dashboard'))
                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            elif int(content['role'])==0:
                pw_hash = db.volunteers.find_one({"username":username},{"pass":1,"_id":0,"name":1,"chapter-head":1})
                if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        if pw_hash['chapter-head']:
                            session['user']= [pw_hash['name'],0]
                            return redirect(url_for('dashboard'))
                        else:
                            return jsonify({"login":-2})
                    else:
                        return jsonify({"login":0})
                else:
                    return jsonify({"login":-1})
            else:
                return redirect(url_for('badData'))


@app.route('/chapter')
def chapterAssign(testid):
    ''' Adds the volunteer details to the campus chapter db. Volunteers stored as <list> in the db.
    TODO: sends mail to volunteer once the registration and chapter assigning is done'''
    chapter = db.chapter
    # check for campus
    x = db.volunteers.find_one({"_id":ObjectId(testid)},{"campus":1,"name":1})
    #print(x,file=sys.stdout)
    if db.chapter.find_one({"campus":{"$eq":x['campus']}}):
        print('inside')
        db.chapter.update({"campus":x['campus']},{"$push":{"volunteer":x['_id']}})
        ch_id = db.chapter.update({"campus":x['campus']},{"$push":{"volunteer":x['name']}})
        i_d = db.chapter.find_one({"campus":x['campus']},{"_id":1})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter":i_d['_id']}})
        #TODO Send email to volunteer and chapter head

    else:
        print('not inside')
        i_d = db.chapter.insert({"campus":x['campus']})
        db.chapter.update({"_id":ObjectId(str(i_d))},{"$push":{"volunteer":x['_id']}})
        ch_id = db.chapter.update({"_id":ObjectId(str(i_d))},{"$push":{"volunteer":x['name']}})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter":i_d}})
        db.volunteers.update({"_id":ObjectId(str(testid))},{"$set":{"chapter-head":1}})
        #TODO Send email to recipient


@app.route('/test/<testid>',methods=['GET'])
def test(testid):
    ''' Renders the test for the user with 'testid'. Frontend: Then POST data to /test/<testid> to save it on the db.
    Using <testid> along with sessions because of 1. easier 2. easier to manage if the session expires'''
    if 'user' in session:
        print(session,file=sys.stdout)
        return jsonify({'user':1,'testid':testid})
    else:
        return jsonify({"user":0,'testid':testid})
    # return 'Test for user with ObjectId as %s' % testid

@app.route('/test/<testid>',methods=['POST'])
def savetest(testid):
    '''POST data is stored as primary and secondary attribute fields in volunteer db'''
    '''callback: chapterAssign(data)'''
    contents = request.get_json()
    #checking for valid user
    if db.volunteers.find({"$and":[{"_id":ObjectId(testid)},{"primary":{"$eq":0}},{"secondary":{"$eq":0}}]}).count()==1:
        try:
            db.volunteers.update_one({"_id":ObjectId(str(testid))},{"$set":{"primary":contents['primary'],"secondary":contents['secondary']}})
            chapterAssign(testid)
        except Exception as e:
            print(str(e), file=sys.stdout)
            return jsonify({"error":"DB insert failure"})
    else:
        return redirect(url_for('badData'))



@app.route
@app.route('/event',methods=['POST'])
def eventRegister():
    if 'user' in session:
        if session['user'][1]==1:
            content = request.get_json(force=True)
            name= content['eventname']
            user= session['user'][0]
            minimum = content['minimum']
            maximum = content['maximum']
            startDate =  datetime.datetime.strptime(content['startdate'], '%d-%m-%y').date().isoformat()
            endDate = datetime.datetime.strptime(content['enddate'], '%d-%m-%y').date().isoformat()
            details = content['details']
            traits = list(content['triats'])
            date = datetime.datetime.strptime(content['date'], '%d-%m-%y').date().isoformat()
            try:
                i_d = db.event.insert(
                    {
                    "name":name.replace(" ","-"),
                    "ngo":user,
                    "min":minimum,
                    "max":maximum,
                    "starts":ISODate(startDate),
                    "end":ISODate(endDate),
                    "details":details,
                    "traits":traits,
                    "date":date
                    });
                return jsonify({"status":200})
            except Exception as e:
                print(str(e), file = sys.stdout)
            #createEventURL(id=i_d, eventname=name)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route("/event/<eventname>", methods=['GET', 'POST'])
def registerEvent(eventname):
    if request.method=='GET':
        try:
            x = db.event.find_one({"name":eventname},{"ngo":1})

            if x:
                #return render_template('register.html')
                pass
            else:
                return redirect(url_for("start"))

        except Exception as e:
            print(str(e), file=sys.stdout)
    else:
        x = db.event.find_one({"name":eventname},{"end":1,"traits":1,"_id":0})
        if x['end'].isoformat() > datetime.date.today().isoformat():
            vol = db.volunteers.find_one({"name":content['name']},{"chapter":1,"_id":1,"primary":1})
            chap = db.chapter.find_one({"_id":vol['chapter']})
            if chap:
                if vol['primary'] in x['traits']:
                    db.event.update({"name":eventname},{"$push":{"volunteers":vol['_id']}})

@app.route("/ngo-dashboard/events",methods=['POST'])
def ngoDashEvents():
    if 'user' in session:
        if session['user'][1]==1:
            x = db.event.find({"name":session['user'][0]},{"_id":0})
            results =[]
            for row in x:
                results.append(row)
                return toJson(results)


# def getNGO():
#     pg = 1
#     url = "http://ngodarpan.gov.in/index.php/home/statewise_ngo/3203/27/"
#     names=[]
#     reg=[]
#     while(pg<321):
#         res = requests.get((url+str(pg)))
#         res.raise_for_status()
#         soup = bs4.BeautifulSoup(res.text,"html.parser")
#         table = soup.select("td")
#         #print(table)
#         for x in range(1,51,5):
#             names.append(table[x].getText().lstrip())
#         for x in range(2,51,5):
#             reg.append(table[x].getText().lstrip().split(',')[0])
#         pg+=1
#     db.ngolist.insert({"name":name,"reg":reg})


@app.route('/dashboard', methods=['POST'])
def dashboard():
    '''Should redirect here once login is completed'''
    pass

def confirmation(name, mail, reg, state, city):
    url = "http://"+state+".ngosindia.com/"+city+"-ngos/"
    res = requests.get(url)
    res.raise_for_status()
    nss = bs4.BeautifulSoup(res.text,"html.parser")
    elem = nss.select('.lcp_catlist > li')
    ls =[]
    for element in elem:
        ls.append(element.getText().split(',')[0])

    print(ls,file=sys.stdout)
    if name in ls:
        #The NGO name has been confirmed. Could not find a link for registration number verification
    # pg = 1
    # url = "http://ngodarpan.gov.in/index.php/home/statewise_ngo/3203/27/"
    # names=[]
    # reg=[]
    # while(pg<321):
    #     res = requests.get((url+str(pg)))
    #     res.raise_for_status()
    #     soup = bs4.BeautifulSoup(res.text,"html.parser")
    #     table = soup.select("td")
    #     #print(table)
    #     for x in range(1,51,5):
    #         names.append(table[x].getText().lstrip())
    #     for x in range(2,51,5):
    #         reg.append(table[x].getText().lstrip().split(',')[0])
    #     pg+=1
    # print(names, file=sys.stdout)
    # print(reg, file=sys.stdout)

        ngo = db.ngo
        x = ngo.update({"name":{"$eq":name}},{"$set":{"name-verified":True}})
        #TODO- send mail to confirm that the ngo has been added
    else:
        ngo = db.ngo
        x = ngo.update({"name":{"$eq":name}},{"$set":{"name-verified":False}})

#---------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------

@app.route('/abc/admin/login',methods=['GET','POST'])
def adminLogin():
    if 'user' in session:
        return "No admin rights"
    if 'admin' in session:
        return "Already logged in"
    else:
        if request.method =='GET':
            #render adminLogin.html
            pass
        else:
            content = request.get_json(force=True)
            username = content['username']
            password = content['password']
            pw_hash = db.admin.find_one({"username":username},{"pass":1,"_id":0,"id":1})
            if pw_hash:
                    if bcrypt.check_password_hash(pw_hash['pass'],password):
                        session['admin']=pw_hash['id']
                    else:
                        return jsonify({"login":0})
            else:
                return jsonify({"login":-1})


@app.route('/getvolunteers',methods=['POST'])
def volList():
    pageNumber = int(request.headers.get('Pagenumber'))
    pagelimit = int(request.headers.get('Pagelimit'))
    # print(pageNumber,file=sys.stdout)
    # print(pagelimit,file=sys.stdout)
    try:
        # print("entered")
        x = db.volunteers.find().sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
        json_results = []
        for result in x:
            json_results.append(result)
            return toJson(json_results)
    except:
        return redirect(url_for('badData'))

@app.route('/getngos/<int:validated>',methods=['POST'])
def ngoList(validated):
    pageNumber = int(request.headers.get('Pagenumber'))
    pagelimit = int(request.headers.get('Pagelimit'))
    if validated:
        try:
            x = db.ngo.find({"name-verified":True}).sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
            json_results=[]
            for result in x:
                json_results.append(result)
                return toJson(json_results)
        except:
            return redirect(url_for('badData'))
    else:
        try:
            x = db.ngo.find({"name-verified":False}).sort("name",1).skip((pageNumber-1)*pagelimit).limit(pagelimit)
            json_results=[]
            for result in x:
                json_results.append(result)
                return toJson(json_results)
        except:
            return redirect(url_for('badData'))

@app.route('/abc/admin/register',methods=['GET','POST'])
def adminRegister():
    if 'user' in session:
        return "No admin rights"
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    else:
        username = request.form['username']
        password = request.form['password']
        employeeid = request.form['employeeid']
        if db.admin.find({"$and":[{'id':{"$eq": employeeid}},{'username':{"$eq":username}}]}).count()==0:
            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            try:
                db.admin.insert({"username":username,"pass":pw_hash,"id":employeeid})
            except Exception as e:
                print(str(e), file=sys.stdout)
        else:
            return jsonify({"register":0})


@app.route('/error')
def badData():
    return 'Incorrect data'

def toJson(data):
    """Convert Mongo object(s) to JSON"""
    #print(type(data), file=sys.stdout)
>>>>>>> dfb7c2b185f8090cdce3e2f2f99e379937a3b1bc
    return Response(json.dumps(data, default=json_util.default), mimetype='application/json')