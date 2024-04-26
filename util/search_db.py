from pymongo import MongoClient
import hashlib
import base64

mongo_client = MongoClient("mongo")
db = mongo_client["TBD"]
auth = db['auth']
authtoken = db['authtoken']
chat = db['chat']
id = db['chatid']
UsernameStorage = db['usernames']
likes = db['likes']
profile_picture = db['pic']
tracker = db['track']


def get_Profile_Picture(email):
    ppicture = '/static/images/default.png'
    check_profile = profile_picture.find_one({'email' : email})
    if check_profile:
        ppicture = check_profile['path']
    
    return ppicture


def get_username(email):
    username = email
    check = UsernameStorage.find_one({'email' : email})
    if check:
        username = check['username']
    return username


def get_email(authcookie):
    email = 'None'
    if authcookie:
        hashAuthCookie = hashlib.sha256(authcookie.encode()).hexdigest()
        authUser = authtoken.find_one({'authtoken_hash' : hashAuthCookie})
        if authUser:
            email = authUser['email']
    return email