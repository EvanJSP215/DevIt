from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, flash
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


app = Flask(__name__)
mongo_client = MongoClient("mongo")
db = mongo_client["TBD"]
auth = db['auth']
authtoken = db['authtoken']
chat = db['chat']
id = db['chatid']
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
likes = db['likes']
profile_picture = db['pic']
tracker = db['track']


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
    else:
        return 'invalid profile picture', 400
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
        password = password.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
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
            resp.set_cookie('auth_token', token, httponly=True, max_age=3600)
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


@app.route('/blogPage', methods=['GET', 'POST'])
def blogPage():
    if request.method == 'POST':
        message = request.form.get("message",None)
        authcookie = request.cookies.get('auth_token',None)
        if message != None:
            message = message.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        else:
            message = "none"
        uid = id.find_one({})
        chatId = None
        if uid:
            chatId = uid['id']
            chatId = int(chatId) + 1
            id.update_one({}, {'$set':{'id' : str(chatId)}})
        else:
            id.insert_one({'id' : "0"})
            chatId = id.find_one({})
            chatId = chatId['id']
        if authcookie != None:
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser:
                email = authUser['email']
            else:
                # have the authcookie but authtoken does not exist
                email = 'Guest'
        else:
            # no auth cookie
            email = 'Guest'
        
        blogData = {'message': message, 'email': email, 'id': str(chatId), 'likeCount' : "0" , 'status': 'Active'}
        chat.insert_one(blogData)
        return getBlogPage()
              
    else:
        return getBlogPage()
        
        
@app.route('/like/<messageId>', methods=['POST'])
def like_post(messageId):
    authcookie = request.cookies.get('auth_token', None)
    if not authcookie:
        return jsonify({'error': 'Authentication required'}), 401

    hashAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
    user = authtoken.find_one({'authtoken_hash': hashAuthCookie})
    if not user:
        return jsonify({'error': 'User not authenticated'}), 403

    already_liked = likes.find_one({'messageId': messageId, 'email': user['email']})
    if already_liked:
        return jsonify({'error': 'You have already liked this post'}), 400

    likes.insert_one({'messageId': messageId, 'email': user['email']})
    return jsonify({'message': 'Like added successfully'}), 200

@app.route('/chat', methods=['GET'])
def chatm():
    chatData = chat.find({'status': 'Active'})
    arr =[]
    authcookie = request.cookies.get('auth_token',None)
    email = 'None'
    if authcookie:
        hashAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : hashAuthCookie})
        if authUser:
            email = authUser['email']
    for result in chatData:
        edit = 'False'
        like_count = likes.count_documents({'messageId': result['id']})
        result['likeCount'] = str(like_count)
        if email == result['email']:
            edit = 'True'
        dic = {'message': result['message'], 'username': result['email'], 'id': result['id'], 'likeCount' : result['likeCount'], 'edit_permission': edit}
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
        response = make_response(body,302)
        response.headers["Content-Type"] = "text/html"
        response.set_cookie('auth_token', '0', httponly=True, max_age=-3600)
        return response
    else:
        body = make_response(redirect(url_for('blogPage')))
        resp = make_response(body)
        resp.headers["Content-Type"] = "text/html"
        return resp
    
@app.route("/chat/<messageId>", methods=['DELETE'])
def deletemsg(messageId):
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        find = chat.find_one({'id': messageId})
        if(find):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser['email'] == find['email']:
                chat.update_one({'id': messageId}, {'$set': {'status': 'Deleted'}})
                response = make_response(jsonify('Deleted'), 200)
                
                return response
            else:
                response = make_response(jsonify('Not the actual user'), 404)
                return response
        else:
            response = make_response(jsonify('Message not found'), 204)
            return response 
    response = make_response(jsonify('Not authenticated'), 404)
    return response

@app.route("/chat/<messageId>", methods=['PUT'])
def updatemsg(messageId):
    authcookie = request.cookies.get('auth_token',None)
    if(authcookie):
        find = chat.find_one({'id': messageId})
        if(find):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser['email'] == find['email']:
                msg = request.json
                message = msg.get('message')
                print(message)
                chat.update_one({'id': messageId}, {'$set': {'message': message}})
                response = make_response(jsonify('Updated'), 200)
                return response
            else:
                response = make_response(jsonify('Not the actual user'), 404)
                return response
        else:
            response = make_response(jsonify('Message not found'), 204)
            return response 
    response = make_response(jsonify('Not authenticated'), 404)
    return response

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
            if authUser:
                username = authUser['email']
                picture = profile_picture.find_one({'email':username})
                body = render_template('blog.html', UsernameReplace= username, image_url = "/static/images/default.png" , image_url2 = "/static/images/default.png")
                if picture:
                    path = picture['path']
                    body = render_template('blog.html', UsernameReplace= username, image_url = path, image_url2 = path)
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)