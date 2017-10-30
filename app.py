######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login


import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'AipgAipg90'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM Users")
users = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')

#FIRST:REGISTER USER
@app.route("/register", methods=['POST'])
def register_user():
    try:
        fname = request.form.get('First Name')
        lname = request.form.get('Last Name')
        email = request.form.get('email')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        hometown = request.form.get('hometown')
        password = request.form.get('password')

    except:
        print("couldn't find all tokens")  # this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute("INSERT INTO Users (fname, lname, email, dob, gender, hometown, password) VALUES ('{0}', '{1}', '{2}','{3}','{4}','{5}', '{6}')".format(fname, lname, email, dob, gender, hometown, password)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

def getUserDataFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT fname, lname, dob, gender, hometown FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetcall()


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT uid  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


# end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    UserData = getUserDataFromEmail(flask_login.current_user.id)
    FriendsofUser = getFriendsofUser(flask_login.current_user.id)
    AlbumsofUser = getAlbumsFromEmail(fask_login.current_user.id)
    TopTenUsers = TopTenUsers()
    print (TopTenUsers)
    return render_template('hello.html', name=flask_login.current_user.id, userdata = UserData, friends = FriendsofUser, UserActivity = TopTenUsers, message="Here's your profile")


# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        print(caption)
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Photo (pid, uid, caption) VALUES ('{0}', '{1}', '{2}' )".format(photo_data, uid,
                                                                                                    caption))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!',
                               photos=getUsersPhotos(uid))
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html')


#end photo uploading code

#SECOND: ADD AND LIST FRIENDS
def getFriendsofUser(email):
    cursor = conn.cursor()
    cursor.execute("SELECT u2.fname, u2.lastname, u2.email FROM Users u1, Users u2, Friendship F, WHERE u1.uid = F.uid1 AND u2.uid = F.uid2 AND U1.email ='{0}'")
    return cursor.fetchall()

@app.route('/Friends', methods = ['POST'])
@flask_login.login_required
def AddFriends():
    email = request.form.get('email')
    cursor = conn.cursor()
    cursor.execute("SELECT U1.uid, U1.fname, U2.uid, U2.fname FROM Users U1, Users U2 WHERE U1.email = '{0}' and U2.email = '{1}'".format(flask_login.current_user.id, email))
    output = cursor.fetchall()[0]
    print (output)
    output2 = cursor.execute("INSERT INTO Friendship(uid1, uid2) VALUES ('{0}', '{1}')").format(output[0], output[2])
    print (output2)
    conn.commit()
    return flask.redirect('/profile')

#THIRD: TOP TEN USERS (USER ACTIVITY)
def TopTenUsers():
    cursor = conn.cursor()
    cursor.execute("SELECT U1.email, count(*) AS counter FROM Users U1, Albums A, Photo P WHERE U1.uid = A.aid AND P.aid = A.aid GROUP BY uid;")
    Photos = cursor.fetchcall()
    cursor.execute("SELECT U2.email, count(*) AS counter FROM Users U2, Comments C WHERE U2.uid = C.cid GROUP BY uid")
    Comments = cursor.fetchall
    TopUsers = list()
    for x in Photos:
        number = x[1]
        for y in Comments:
            print (x)
            print (y)
            print (number)
            if x[0] == y[0]:
                number += y[1]
        TopUsers.append([x[0], number])
    FinalTopUsers = sorted(TopUsers, key=itemgetter(1), reverse = True)
    return FinalTopUsers


#FOURTH: PHOTO AND ALBUM BROWSING

#FIFTH: PHOTO AND ALBUM CREATING
def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT P.pid, P.caption, P.data FROM Photo P WHERE uid = '{0}'".format(uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]

def getAlbumsFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT A.aid, A.name, A.doc FROM Albums A, Users U WHERE A.uid = U.uid AND U.email = '{0}'".format(email))
    return cursor.fetchall()

def getAlbumAid(name):
    cursor = conn.cursor()
    cursor.execute ("SELECT A.aid FROM Albums A WHERE name = '{0}'".format(name))
    return cursor.fetchall()

#SIXTH: VIEWING YOUR PHOTOS BY TAG NAME
# @app.route("/albums", methods = ['GET'])
# @flask_login.login_required
    # def Albums():
    # uid = getUserIdFromEmail(flask_login.current_uid)
    # try:
      #  aid = request.args[aid]
#tag = request.args['tag']

#SEVENTH: VIEWING ALL PHOTOS BY TAG NAME


#EIGHT: VIEWING THE MOST POPULAR TAGS (LIST)



#NINTH: PHOTO SEARCH

@app.route("/showPhotos", methods=['GET'])
def showPhotos():
    # get photopath from the database: SELECT photopath FROM PHOTOS WHERE USER_ID = .....
        photopath = "/static/rhett_alone1.jpg"
        return render_template('testShowPhoto.html', photopath=photopath)

#TENTH: LEAVING COMMENTS
def getComments(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT C.cid, C.content, C.doc FROM Comment C WHERE pid = '{0}'".format(pid))




#ELEVENTH: LIKE FUNCTIONALITY
def getLikes(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM Liketable L WHERE pid = '{0}'".format(pid))
    return cursor.fetchall()

#TWELVETH: SEARCH ON COMMENTS

#THIRTEENTH: FRIEND RECOMMENDATION

#FOURTEENTH: "YOU MAY ALSO LIKE"


# default page
@app.route("/", methods=['GET'])
def hello():
    TopTenUsers = TopTenUsers()
    print(TopTenUsers)
    return render_template('hello.html', UserActivity = TopTenUsers, message='Welecome to Photoshare')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
