from flask import Flask, render_template, request, session, url_for, redirect
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import os, json

app = Flask(__name__)
app.secret_key = "secrets"

# Site Navigation / Flask Routes =====================

@app.route("/")
def root():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('root'))

# Image upload - we don't really want to save it, but for now, save it...

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])
UPLOAD_FOLDER = join(dirname(realpath(__file__)), "static/temp")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/upload/", methods=["POST"])
def upload():
    #below checks should be done in js, but just in case
    if "upload" not in request.files:    
        return json.dumps({"status": "Upload not found"})
    f = request.files["upload"]    
    if not allowed_file(f.filename):
        return json.dumps({"status": "Illegal filename"})
    
    filename = secure_filename(f.filename)
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return json.dumps({"status": "success"})

def allowed_file(filename):
    return "." in filename and filename.rsplit( ".", 1 )[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.debug = True
    app.run()
