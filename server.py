from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, flash
from pymongo import MongoClient
import bcrypt
import secrets
import hashlib
import os
import base64
import requests

app = Flask(__name__)
mongo_client = MongoClient("mongo")
db = mongo_client["TBD"]
auth = db['auth']

@app.route("/")
def landing_page():
    body = render_template("landingPage.html")
    response = make_response(body)
    response.headers["Content-Type"] = "text/html"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route("/static/images/<filename>", methods=['GET'])
def handle_img(filename):
    path = 'static/images'
    if filename == 'favicon.ico':
        response = make_response(send_from_directory(path, filename))
        response.headers["Content-Type"] = "image/x-icon"
    else:
        response = make_response(send_from_directory(path, filename))
        response.headers["Content-Type"] = "image/png"

    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/static/styles/filename', methods=['GET'])
def handle_css(filename):
    body = render_template(filename)
    response = make_response(body)
    response.headers["Content-Type"] = "text/css"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/static/function/filename', methods=['GET'])
def handle_js(filename):
    body = render_template(filename)
    response = make_response(body)
    response.headers["Content-Type"] = "application/javascript"
    response.headers['X-Content-Type-Options'] = 'nosniff'
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
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        #if the email is already registered
        if check:
            Failmessage = "There are already an account asscociated with this Email!"
            body = render_template('register.html', Failmessage=Failmessage )
            response = make_response(body,403)
            response.headers["Content-Type"] = "text/html"
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        email = email.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        password = password.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        hashedpw = bcrypt.hashpw(password.encode(),bcrypt.gensalt())
        csrf = secrets.token_urlsafe(80) 
        user = {"email": email,'password': hashedpw,'csrf':csrf}
        auth.insert_one(user)
        check = auth.find_one({'email': email})
        body = render_template("register.html")
        response = make_response(body)
        response.headers["Content-Type"] = "text/html"
        return response
    else:
        body = render_template("register.html")
        response = make_response(body)
        response.headers["Content-Type"] = "text/html"
        return response
    






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)