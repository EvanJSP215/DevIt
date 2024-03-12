from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def landing_page():
    #TODO: Landing Page Function
    return render_template("landingPage.html")

#@app.route("/register")
#TODO: Register

#@app.route("/login")
#TODO: Login

#Add in the CSS, JS, and Image Folder


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)