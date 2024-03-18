from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, flash
from pymongo import MongoClient
from flask import session
from datetime import datetime, timedelta
import datetime
import bcrypt
import secrets
import hashlib
import os
import base64
import requests
import json


app = Flask(__name__)
mongo_client = MongoClient("mongo")
db = mongo_client["TBD"]
auth = db['auth']
authtoken = db['token']
chat = db['chat']
id = db['chatid']
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

#add a nosniff after all responses
@app.after_request
def nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

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
    response.headers["Content-Type"] = "application/javascript"
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
        body = render_template("login.html")
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
            body = render_template('blog.html', UsernameReplace=email)
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
        body = render_template('blog.html', UsernameReplace= email)
        response = make_response(body)
        response.headers["Content-Type"] = 'text/html'

        return response
              
    else:
        #get request
        authcookie = request.cookies.get('auth_token',None)
        if(authcookie):
            haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
            username = 'Guest'
            authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
            if authUser:
                username = authUser['email']
            
            body = render_template('blog.html', UsernameReplace= username)
            response = make_response(body)
            response.headers["Content-Type"] = "text/html"
            return response

        else:
            authcookie = request.cookies.get('auth_token',None)
            username = 'Guest'
            body = render_template('blogLogin.html', UsernameReplace= username)
            response = make_response(body)
            response.headers["Content-Type"] = "text/html"
            return response

@app.route('/chat', methods=['GET'])
def chatm():
    chatData = chat.find({'status': 'Active'})
    arr =[]
    authcookie = request.cookies.get('auth_token',None)
    email = 'None'
    if authcookie:
        haskAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : haskAuthCookie})
        if authUser:
            email = authUser['email']
    for result in chatData:
        edit = 'False'
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
        username = 'Guest'
        body = render_template('blogLogin.html', UsernameReplace= username)
        response = make_response(body,302)
        response.headers["Content-Type"] = "text/html"
        response.set_cookie('auth_token', '0', httponly=True, max_age=-3600)
        return response
    
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)