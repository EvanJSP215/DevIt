from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, flash, abort
from pymongo import MongoClient
from flask import session,redirect, url_for
from datetime import datetime, timedelta
import datetime
import bcrypt
import secrets
import hashlib
import os
import base64
import requests
import json
import magic
from flask_socketio import SocketIO, emit
from util.search_db import get_Profile_Picture,get_username,get_email
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is not a Secret!'
socketio = SocketIO(app)

mongo_client = MongoClient("mongo")
db = mongo_client["TBD"]
auth = db['auth']
authtoken = db['authtoken']
chat = db['chat']
id = db['chatid']
UsernameStorage = db['usernames']
OnlineRTimer = db['OnlineTimer']
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
likes = db['likes']
profile_picture = db['pic']
tracker = db['track']
banned_ips = db["banned_ips"]
req_counts = db["request_counts"]
user_lists = {}
Lock = {}


RATE_LIMIT = 50  # maximum number of requests
TIME_PERIOD = 10  # time period in seconds

@app.before_request
def check_rate_limit():
    ip_address = request.headers.get('X-Real-IP')
    
    # Check if the IP is banned
    current_time = time.time()
    ban_record = banned_ips.find_one({'ip': ip_address})
    if ban_record and ban_record['time'] > current_time:
        abort(429, "Rate limit exceeded. Please try again after 30.")

    # Check rate limits
    record = req_counts.find_one({'ip': ip_address})
    if record:
        time_passed = current_time - record['first_request_time']
        if time_passed < TIME_PERIOD:
            if record['count'] >= RATE_LIMIT:
                # Ban the IP if it exceeds the limit
                banned_ips.update_one({'ip': ip_address}, {'$set': {'time': current_time + 30}}, upsert=True)
                abort(429, "Rate limit exceeded. Please try again later.")
            else:
                req_counts.update_one({'ip': ip_address}, {'$inc': {'count': 1}})
        else:
            # Reset count and time
            req_counts.update_one({'ip': ip_address}, {'$set': {'count': 1, 'first_request_time': current_time}})
    else:
        # Create new record
        req_counts.insert_one({'ip': ip_address, 'count': 1, 'first_request_time': current_time})

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return str(error), 429

#add a nosniff after all responses
@app.after_request
def nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route("/")
def landing_page():
    body = render_template("landingPage.html")
    response = make_response(body)
    response.headers["Content-Type"] = "text/html"
    return response

@app.route("/static/images/<filename>", methods=['GET'])
def handle_img(filename):
    path = 'static/images'
    if filename == 'favicon.ico':
        response = make_response(send_from_directory(path, filename),200)
        response.headers["Content-Type"] = "image/x-icon"
    else:
        response = make_response(send_from_directory(path, filename),200)
        response.headers["Content-Type"] = "image/png"


    return response

@app.route("/pictures/<filename>", methods=['GET'])
def prof_picture_rendering(filename):
    path = 'pictures'
    type = filename.split('.')[1]
    filename = filename.replace('/','')
    if type == 'jpeg':
        response = make_response(send_from_directory(path, filename),200)
        response.headers["Content-Type"] = "image/jpeg"
    elif type == 'png':
        response = make_response(send_from_directory(path, filename),200)
        response.headers["Content-Type"] = "image/png"
    elif type == 'gif':
        response = make_response(send_from_directory(path, filename),200)
        response.headers["Content-Type"] = "image/gif"
    else:
        return 'invalid picture', 400
    return response


@app.route('/static/styles/<filename>', methods=['GET'])
def handle_css(filename):
    path = 'static/styles'
    response = make_response(send_from_directory(path, filename),200)
    response.headers["Content-Type"] = "text/css"
    return response


@app.route('/static/function/<filename>', methods=['GET'])
def handle_js(filename):
    path = 'static/function'
    response = make_response(send_from_directory(path, filename),200)
    response.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return response



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('reg_email').lower()
        password = request.form.get('reg_pass')
        confirmpw = request.form.get('reg_cpass')
        check = auth.find_one({'email': email})
        #If password are not equivalent
        if confirmpw != password:
            Failmessage = "Password Not Match, Please try again!"
            body = render_template('register.html', Failmessage=Failmessage )
            response = make_response(body,403)
            response.headers["Content-Type"] = "text/html"
            return response
        #if the email is already registered
        if check:
            Failmessage = "There are already an account asscociated with this Email!"
            body = render_template('register.html', Failmessage=Failmessage )
            response = make_response(body,403)
            response.headers["Content-Type"] = "text/html"
            return response
        email = email.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        password = password
        hashedpw = bcrypt.hashpw(password.encode(),bcrypt.gensalt())
        csrf = secrets.token_urlsafe(80) 
        user = {"email": email,'password': hashedpw,'csrf':csrf}
        auth.insert_one(user)
        check = auth.find_one({'email': email})
        body = make_response(redirect(url_for('login')))
        response = make_response(body)
        response.headers["Content-Type"] = "text/html"
        return response
    else:
        body = render_template("register.html")
        response = make_response(body)
        response.headers["Content-Type"] = "text/html"
        return response
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['login_email']
        password = request.form['login_pass'].encode('utf-8')
        user = auth.find_one({'email': email})

        if user and bcrypt.checkpw(password, user['password']):
            # Generate a random token and its hash
            token = secrets.token_urlsafe(80)
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Store the hash of the token in the database
            authentication = authtoken.find_one({'email': email})
            if (authentication):
                authtoken.update_one({'email': email}, {'$set': {'authtoken_hash': token_hash}})
            else:
                auth_user = {"email": email,'authtoken_hash': token_hash}
                authtoken.insert_one(auth_user)

            # change the url for blog page
            body = make_response(redirect(url_for('blogPage')))
            resp = make_response(body)
            resp.headers["Content-Type"] = "text/html"
            resp.set_cookie('auth_token', token, httponly=True, max_age=3600, secure=True)
            return resp
        else:
            # Authentication failed
            loginFailMessage = "Invalid email or password. Please try again."
            body = render_template('login.html', loginFailMessage=loginFailMessage)
            response = make_response(body)
            response.headers["Content-Type"] = "text/html"
            return response
    
    body = render_template('login.html')
    response = make_response(body)
    response.headers["Content-Type"] = "text/html"
    return response


@app.route('/blogPage', methods=['GET'])
def blogPage():
    
    return getBlogPage()


@app.route('/chat', methods=['GET'])
def chatm():
    chatData = chat.find({'status': 'Active'})
    arr =[]
    authcookie = request.cookies.get('auth_token',None)
    email = get_email(authcookie)      
    for result in chatData:
        edit = 'False'
        like_count = likes.count_documents({'messageId': result['id']})
        result['likeCount'] = str(like_count)
        ppicture = '/static/images/default.png'
        username = result['email']
        if email == result['email']:
            edit = 'True'
        username = get_username(result['email'])
        ppicture = get_Profile_Picture(result['email'])
        dic = {'message': result['message'], 'username': username, 'id': result['id'], 'likeCount' : result['likeCount'], 'edit_permission': edit, 'imagePath' : result['imagePath'], 'profile_picture': ppicture}
        arr.append(dic)
    jsonStr = json.dumps(arr)
    body = jsonStr
    response = make_response(body)
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/logout', methods=['POST'])
def logout():
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authtoken.delete_one({'authtoken_hash' : haskAuthCookie})
        username = 'Guest'
        body = render_template('blogLogin.html', UsernameReplace= username)
        body = make_response(redirect(url_for('blogLogin')))
        response = make_response(body,302)
        response.headers["Content-Type"] = "text/html"
        response.set_cookie('auth_token', '0', httponly=True, max_age=-3600)
        return response
    else:
        body = make_response(redirect(url_for('blogLogin')))
        resp = make_response(body)
        resp.headers["Content-Type"] = "text/html"
        return resp
    
@app.route('/blogLogin', methods=['GET'])
def blogLogin():
    username = 'Guest'
    response = make_response(render_template('blogLogin.html', UsernameReplace=username))
    response.headers["Content-Type"] = "text/html"
    response.set_cookie('auth_token', '0', httponly=True, max_age=-3600)
    return response


@app.route("/updateUsername", methods=['POST'])
def update_username():
    authcookie = request.cookies.get('auth_token', None)
    if authcookie:
        hash_auth_cookie = hashlib.sha256(authcookie.encode()).hexdigest()
        auth_user = authtoken.find_one({'authtoken_hash': hash_auth_cookie})
        if auth_user:
            user = auth_user['email']
            new_username = request.form.get('newUsername')
            if len(new_username) > 10:
                response = make_response(redirect(url_for('blogPage')))
                return response
            new_username = new_username.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            data = {'email':user, 'username':new_username}
            check = UsernameStorage.find_one({'email' : user})
            if check:
                UsernameStorage.update_one({'email' : user},{'$set': data})
            else:
                UsernameStorage.insert_one(data)
            response = make_response(redirect(url_for('blogPage')))
            return response
        else:
            return "User not found"
    else:
        return "Unauthorized access"
    
@app.route("/uploadProfilePicture", methods=['POST'])
def upload():
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
        if authUser:
            #find the corresponding image increment number
            user = authUser['email']
            track = tracker.find_one({'type' : 'image'})
            if not (track):
                data = {'type' : 'image', '#': 0}
                tracker.insert_one(data)
            track = tracker.find_one({'type' : 'image'})
            number = int(track['#'])
            number += 1
            tracker.update_one({'type' : 'image'}, {'$set': {'#': number}})
            if 'file-upload' not in request.files:
                # Handle case where no file was uploaded
                return str(request.files) + ':'+str(request), 400

            file = request.files['file-upload']
            #determine the file type
            determine = magic.Magic(mime=True)
            type = determine.from_buffer(file.read(1024))
            file.seek(0)
            file_type = ''
            if type in ['image/jpeg', 'image/jpg']:
                file_type = '.jpeg'
            elif type in ['image/png']:
                file_type = '.png'
            elif type == 'image/gif':
                file_type = '.gif'
            else:
                response = make_response(jsonify('Invalid file type'), 404)
                return response
            filepath = 'pictures/image'+str(number)+file_type
            check = profile_picture.find_one({'email' : user})
            data = {'email' : user , 'path':'/'+filepath}
            if check:
                profile_picture.update_one({'email': user}, {'$set': {'path': '/'+filepath}})
            else:
                profile_picture.insert_one(data)
            if not os.path.exists('pictures'):
                os.makedirs('pictures')
            file.save(filepath)
            body = make_response(redirect(url_for('blogPage')))
            resp = make_response(body)
            resp.headers["Content-Type"] = "text/html"
            return resp 
    body = make_response(redirect(url_for('blogPage')))
    resp = make_response(body)
    resp.headers["Content-Type"] = "text/html"
    return resp

def getBlogPage():
    #get request
        authcookie = request.cookies.get('auth_token',None)
        if(authcookie):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            username = 'Guest'
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            Displayname = 'Guest'
            if authUser:
                username = authUser['email']
                Displayname = authUser['email']
                check = UsernameStorage.find_one({'email' : username})
                if check:
                    Displayname = check['username']
                picture = profile_picture.find_one({'email':username})
                body = render_template('blog.html', UsernameReplace= Displayname, image_url = "/static/images/default.png" , image_url2 = "/static/images/default.png")
                if picture:
                    path = picture['path']
                    body = render_template('blog.html', UsernameReplace= Displayname, image_url = path, image_url2 = path)
                response = make_response(body)
                response.headers["Content-Type"] = "text/html"
                return response 
            else:
                # token did not match
                username = 'Guest'
                body = render_template('blogLogin.html', UsernameReplace= username)
                response = make_response(body)
                response.headers["Content-Type"] = "text/html"
                return response
        else:
            # no authcookie 
            username = 'Guest'
            #body = make_response(redirect(url_for('logout')))
            body = render_template('blogLogin.html', UsernameReplace= username)
            response = make_response(body)
            response.headers["Content-Type"] = "text/html"
            return response
        

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template('Profile.html')

@socketio.on('blogMessage')
def handle_message(data):
    auth_token = request.cookies.get('auth_token', None)
    user = 'Guest'
    message = {}
    if auth_token != None:
        haskAuthCookie = hashlib.sha256(auth_token.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
        if authUser:
            user = authUser['email']
    message = PostMessageHandler(data,auth_token)
    if request.sid == user_lists.get(user,None):
        message['edit_permission'] = 'True'
        emit('NewMsg', message)
    elif user == 'Guest':
        emit('NewMsg', message)
    message['edit_permission'] = 'False'
    emit('NewMsg', message, broadcast=True, include_self=False)

@app.route("/user_list", methods=['GET'])
def handle_user_list():
    user_list = []
    for user in list(user_lists.keys()):
        ppicture = get_Profile_Picture(user)
        username = get_username(user)
        message = {'username':username, 'ppicture':ppicture ,'email':user}
        user_list.append(message)
    jsonStr = json.dumps(user_list)
    body = jsonStr
    response = make_response(body)
    response.headers["Content-Type"] = "application/json"
    return response


@socketio.on('connect')
def handle_connect():
    auth_token = request.cookies.get('auth_token', None)
    email = get_email(auth_token)
    if email != 'None':
        user_lists[email] = request.sid
        ppicture = get_Profile_Picture(email)
        username = get_username(email)
        message = {'username':username, 'ppicture':ppicture ,'email':email}
        emit('connect_user', message, broadcast=True)
        socketio.start_background_task(updateTime, message)
        
def updateTime(message):
    while message['email'] in Lock:
        pass
    while True:
        Lock[message['email']] = 1
        findUser = OnlineRTimer.find_one({'user': message['email']})
        if findUser:
            message['seconds'] = int(findUser['seconds']) + 1
            OnlineRTimer.update_one({'user': message['username']},{'$set': {'seconds': int(findUser['seconds']) + 1}})
        else:
            OnlineRTimer.insert_one({'user': message['username'],'seconds':1})
            message['seconds'] = 1
        for users in user_lists.items():
            socketio.emit('UpdateTimer', message, room=users )
        time.sleep(1)
        Lock.pop(message['email'])

@socketio.on('disconnect')
def handle_disconnect():
    auth_token = request.cookies.get('auth_token', None)
    email = get_email(auth_token)
    if email != 'None':
        if email in (user_lists):
            user_lists.pop(email)
            OnlineRTimer.delete_one({'user': email})
        message = {'email':email}
        emit('disconnect_user', message, broadcast=True)

        
@socketio.on('Like_Post')
def like_post(data):
    messageId = data.get('message_id')
    authcookie = request.cookies.get('auth_token', None)
    if not authcookie:
        message = {}
        message['auth'] = 'error'
        emit('Like_Post', message)
        return

    hashAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
    user = authtoken.find_one({'authtoken_hash': hashAuthCookie})
    if not user:
        message = {}
        message['auth'] = 'error'
        emit('Like_Post', message)
        return

    already_liked = likes.find_one({'messageId': messageId, 'email': user['email']})
    if already_liked:
        likes.delete_one({'messageId': messageId, 'email': user['email']})
        like_count = likes.count_documents({'messageId': data.get('message_id')})
        message = {}
        message['auth'] = 'correct'
        message['likeCount'] = str(like_count)
        message['message_id'] = messageId
        emit('Like_Post', message, broadcast=True)
        return
    
    likes.insert_one({'messageId': messageId, 'email': user['email']})
    like_count = likes.count_documents({'messageId': data.get('message_id')})
    message = {}
    message['auth'] = 'correct'
    message['likeCount'] = str(like_count)
    message['message_id'] = messageId
    emit('Like_Post', message, broadcast=True)
    return 

@socketio.on('Delete_Post')
def deletemsg(data):
    messageId = data.get('message_id',None)
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        find = chat.find_one({'id': messageId})
        if(find):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser['email'] == find['email']:
                chat.update_one({'id': messageId}, {'$set': {'status': 'Deleted'}})
                message = {}
                message['message_id'] = messageId 
                emit('Delete_Post', message,broadcast=True)
                return 
    return 


@socketio.on('Update_Post')
def updatemsg(data):
    messageId = data.get('message_id',None)
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        find = chat.find_one({'id': messageId})
        if(find):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser['email'] == find['email']:
                msg = data.get('update_message',None)
                message = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                chat.update_one({'id': messageId}, {'$set': {'message': message}})
                response = {'message': message,'message_id':messageId}
                emit('Update_Post', response,broadcast=True)
                return
    return 


def PostMessageHandler(request,authcookie):
    message = request.get("message",None)
    if message:
        if len(message)>2000:
            pass
    
    imageFile = request.get("image",None)
    uid = id.find_one({})
    chatId = '0'
    if uid:
        chatId = uid['id']
        chatId = int(chatId) + 1
        id.update_one({}, {'$set':{'id' : str(chatId)}})
    else:
        id.insert_one({'id' : "0"})
        chatId = id.find_one({})
        chatId = chatId['id']
        
    imagePath = ''
    if imageFile:
        type,b64Content = imageFile.split(",", 1)
        imageFile = base64.b64decode(b64Content)
        mimetype = type.split(';')[0].split(':')[1] 
        fileExtension = ''
        if mimetype in ['image/jpeg', 'image/jpg']:
            fileExtension = '.jpeg'
        elif mimetype == 'image/png':
            fileExtension = '.png'
        elif mimetype == 'image/gif':
            fileExtension = '.gif'
        else:
            uploadFail = 'Invalid image file format. Only JPG, JPEG, PNG, and GIF are allowed.'
            return render_template('uploadFail.html')
            
        imagePath = './pictures/image' + str(chatId) + fileExtension
        if not os.path.exists('pictures'):
            os.makedirs('pictures')
        with open(imagePath, 'wb') as f:
            f.write(imageFile)
            
    if message != None:
        message = message.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    else:
        message = "none"
    Displayname = 'Guest'
    if authcookie != None:
        haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
        if authUser:
            email = authUser['email']
            Displayname = authUser['email']
            check = UsernameStorage.find_one({'email' : email})
            if check:
                Displayname = check['username']
        else:
            # have the authcookie but authtoken does not exist
            email = 'Guest'
    else:
        # no auth cookie
        email = 'Guest'
        
    blogData = {'message': message, 'email': email, 'id': str(chatId), 'likeCount' : "0" , 'status': 'Active', 'imagePath': imagePath}
    chat.insert_one(blogData)
    ppicture = get_Profile_Picture(email)
    return {'message': blogData['message'],'username':Displayname,'id':str(chatId),'likeCount' : blogData['likeCount'],'imagePath': imagePath,'profile_picture': ppicture, 'edit_permission': 'False'}


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, debug=True, allow_unsafe_werkzeug=True)