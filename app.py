from flask import Flask, render_template, request, session, url_for, redirect
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import os, json
from PIL import Image
import pytesseract
import re
import cv2

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
    analyze(filename)
    text = pytesseract.image_to_string(Image.open(UPLOAD_FOLDER + '/' + filename))
    ret = {"status": "success"}
    ret.update(processText(text))
    return json.dumps(ret)

def allowed_file(filename):
    return "." in filename and filename.rsplit( ".", 1 )[1].lower() in ALLOWED_EXTENSIONS


# Basic preprocess
def analyze(fn):
    img = cv2.imread(UPLOAD_FOLDER + '/' + fn, 0)
    gray = cv2.medianBlur( img, 1 ) #denoise
    cv2.imwrite(UPLOAD_FOLDER + '/' + fn, gray)
    
def processText(text): #account for interference from circling
    #manual string parsing, what this (update with regex)
    #First we find the question start
    ret = {'text': 'success'}
    qS = -1
    qE = -1
    digits = re.compile('\d') #should probably look for earliest digit within threshold of 10...
    for index, char in enumerate(text):
        if qS == -1 and digits.match(char):
            qS = index
            continue
        if qS != -1 and digits.match(char) == None:
            qE = index
            break
    if qS == -1 or qE == -1:
        ret['text'] = 'fail'
        return ret
    qN = text[qS:qE]
    ret["qN"] = str(qN)

    #Now look for the choices (assume a,b,c,d,e or 1,2,3,4,5 after some space character)
    whitespace = re.compile('[\t\n]+') #one or more whitespace not including spaces

    choices = re.split(whitespace, text)
    #print "START DEBUG"
    print choices
    #print "END DEBUG"
    #parse in reverse - search for a,b,c,d,e or 1,2,3,4,5 in some regularity
    choicePat = re.compile('\S?[a-eA-E1-5]')
    #we expect this to appear somewhat regularly
    matchArr = [choicePat.match(choice) for choice in choices]
    resArr = map(lambda m: m.group(), filter(lambda m: m != None, matchArr)) #python chaining is sacrilegious    
    ret["choices"] = []
    for choice in resArr[-4:]: #for now, take last 4 chunks
        #isolate the A B C D E withini these (assume they are non-num for now)
        #sanitize the last bit
        sanPat = re.compile('[a-eA-E1-5][).]?') 
        sanitized = sanPat.findall(choice)[-1]
        ret["choices"].append(sanitized)
    ret["text"] = text
    return ret
    
if __name__ == "__main__":
    app.debug = True
    app.run()
