from flask import Flask, render_template, request, session, url_for, redirect
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import os, json
from PIL import Image
from pytesseract import pytesseract
import re
import cv2
from matplotlib import pyplot as plt
import numpy as np
import csv
#from tesserocr import PyTessBaseAPI, RIL

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
    mask = analyze(filename)
    print "starting tesseract"
    hocr = 'pytesseractTemp'
    text = pytesseract.run_tesseract(UPLOAD_FOLDER + '/' + filename, UPLOAD_FOLDER + '/' + hocr, lang='eng', boxes=True, config="hocr")
    boxes = []
    with open(UPLOAD_FOLDER + '/' + hocr + '.box', 'rb') as f:
        reader = csv.reader(f, delimiter = ' ')
        for row in reader:
            if(len(row)==6):
                boxes.append(row)
    boxes = pytesseract.image_to_string(Image.open(UPLOAD_FOLDER + '/' + filename), lang="eng", boxes = True).split('\n')
    text = pytesseract.image_to_string(Image.open(UPLOAD_FOLDER + '/' + filename), lang="eng")

    for b in boxes:
        #marking box        
        be = b.split()
        if len(be) == 6:
            print "marking box"
            print b
            cx = int(be[1]) + int(be[3]) / 2
            cy = int(be[2]) + int(be[4]) / 2
            cv2.circle(mask, (cx, cy), 7, (0, 0, 0), -1)

    cv2.imshow('found circles', mask)
    cv2.waitKey(0)
    
    
    ret = {"status": "success"}
    ret.update(processText(text, boxes))
    #mark it out
    for b in ret["boxes"]:
        #marking box
        
        print "marking box"
        print b
        cx = int(b[1]) + int(b[3]) / 2
        cy = int(b[2]) + int(b[4]) / 2
        cv2.circle(mask, (cx, cy), 7, (0, 0, 0), -1)

    cv2.imshow('found circles', mask)
    cv2.waitKey(0)
    
    #now detect the circle (img should be blurred out)
    #edges = cv2.Canny(mask.copy(), 0, 255)
    """
    blurred = cv2.blur(mask, (5, 5))
    plt.subplot(121),plt.imshow(mask),plt.title('Original')
    plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(blurred),plt.title('Blurred')
    plt.xticks([]), plt.yticks([])
    plt.show()
    
    edges = cv2.medianBlur(mask, 5)
    cimg = cv2.cvtColor(edges,cv2.COLOR_GRAY2BGR)

    circles = cv2.HoughCircles(edges,cv2.HOUGH_GRADIENT,1,30,
                            param1=50,param2=30,minRadius=10,maxRadius=200)
    circles = np.uint16(np.around(circles))
    for i in circles[0,:]:
        # draw the outer circle
        cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
        # draw the center of the circle
        cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)
    cv2.imshow('detected circles',cimg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    """
    """
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    contours=contours[1]
    for cnt in contours:
        M = cv2.moments(cnt)
        cX = int(M["m10"] / M["m00"])
	cY = int(M["m01"] / M["m00"])
 
	# draw the contour and center of the shape on the image
	cv2.drawContours(mask, [cnt], -1, (0, 255, 0), 2)
	cv2.circle(mask, (cX, cY), 7, (255, 255, 255), -1)
	cv2.putText(mask, "center", (cX - 20, cY - 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
 
    plt.imshow(mask, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()
"""
    #cv2.imshow("Image", mask)
    #cv2.waitKey(0)
    
    return json.dumps(ret)

def allowed_file(filename):
    return "." in filename and filename.rsplit( ".", 1 )[1].lower() in ALLOWED_EXTENSIONS


# Basic preprocess
def analyze(fn):
    img = cv2.imread(UPLOAD_FOLDER + '/' + fn, 0)
    #why is this showingin yellow?
    gray = cv2.medianBlur( img, 3 ) #denoise
    #cv2.imshow("Image", gray)
    _, thresh = cv2.threshold(gray,225,255,cv2.THRESH_BINARY)
    #_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    #thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
     #                              cv2.THRESH_BINARY,11,3)
    cv2.imshow("Image2", thresh)
    cv2.imwrite(UPLOAD_FOLDER + '/' + fn, thresh)
    return thresh
    
def processText(text, boxes): #account for interference from circling
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

    choices = re.split(whitespace, text)[-4:] #assume last 4

    #identify box locations (approx is fine, match region)
    boxText = "".join([b[0] for b in boxes])
    illegal = re.compile('[^\x00-\x7F]+')
    boxClean = re.sub(illegal, '*', boxText)
    targetPat = re.compile('[\x00-\x7F]\)')
    #put these in as first guess
    print boxClean
    approxI = [m.start(0) for m in re.finditer(targetPat, boxClean)]
    print approxI
    #then match below if better - (But it won't ever be. - overriding default for some reason)
    """
    for i in range(len(choices)):
        cClean = re.sub(whitespace, '', choices[i])
        index = boxClean.find(cClean[:2])
        if index != -1:
            approxI[i] = index
    print "debug approx"
    print approxI
    print len(boxes)
    """
    ret["boxes"] = [boxes[i].split() if i != -1 else [] for i in approxI]    
    print ret["boxes"]
    #choicePat = re.compile('\S?[a-eA-E1-5]')
    #ineffective pattern if char not recognized
    #we expect this to appear somewhat regularly
    #matchArr = [choicePat.match(choice) for choice in choices]
    #resArr = map(lambda m: m.group(), filter(lambda m: m != None, choices)) #python chaining is sacrilegious

    #matching first bit is more effective.
    sanPat = re.compile('[a-eA-E1-5]')
    ret["choices"] = [sanPat.search(choice).group().upper() if sanPat.search(choice) != None else "" for choice in choices]

    #fuzzy match with alpha or numeric:
    choiceMatches = [['A','B','C','D'],['1','2','3','4']]    
    bestMatch = reduce(lambda a,b: a if Levenshtein(ret["choices"], a) < Levenshtein(ret["choices"], b) else b, choiceMatches)
    ret["choices"] = bestMatch
    ret["text"] = text
    
    return ret

#Dynamic - overkill exercise
def Levenshtein(s1, s2):
    #s1 is src, s2 is target (gives changes to reach s2)
    #dist is len(s1) by len(s2) matrix - ij is dist between s1[:i], s2[:j]
    dist = [[0 for col in range(len(s2) + 1)] for row in range(len(s1) + 1)]
    #initial
    for i in range(1, len(s1) + 1):
        dist[i][0] = i
    for j in range(1, len(s2) + 1):
        dist[0][j] = j
    #dynamic
    for j in range(1, len(s2) + 1):
        for i in range(1, len(s1) + 1):
            subCost = 0 if s2[j-1] == s1[i-1] else 1
            dist[i][j] = min(dist[i-1][j-1] + subCost,
                             dist[i-1][j] + 1,
                             dist[i][j-1] + 1)            
    return dist[-1][-1]
            
        
if __name__ == "__main__":
    app.debug = True
    app.run()
