from flask import Flask, render_template, request, redirect, url_for, session
import requests
import cv2 as cv2
import numpy as np
import os
import uuid
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import ipywidgets as widgets
import pytesseract


app = Flask(__name__)
app.debug = True
app.secret_key = 'my_super_secret_key'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        response = requests.post('http://127.0.0.1:5000/signup', json={'name': name, 'password': password })
        if response.status_code == 200:
            return redirect('http://127.0.0.1:3000')
        else:
            return "Couldn't Sign up"
    return render_template('signup.html')


@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        response = requests.post('http://127.0.0.1:5000/login', json={'name': name, 'password': password})
        if response.status_code == 200:
            return redirect(url_for('home'))
        else:
            return 'Invalid login credentials'
    return render_template('login.html')



@app.route('/card_details', methods=['GET'])
def load_card_details():
    response = requests.get('http://127.0.0.1:5000/getcarddetails')
    if response.status_code == 200:
       
        return render_template('card_details.html', response=response.json())



@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/process', methods=['GET' , 'POST'])
def process():
    print("PROCESSING")
    if request.method == 'POST':
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        # Get the uploaded image file
        img = request.files['file']
        filename = img.filename  # Get the filename
        filepath = os.path.join(os.getcwd(), 'uploads', filename)  # Get the full path
    

        # Save the uploaded image file
        img.save(filepath)

        # Run your Python code
        widthImg = 1920
        heightImg = 1000
        lower = 100
        upper = 150
        kernel = np.ones((5, 5))
        Name = " "
        Email = " "
        Address = " "
        Website = " "
        PhoneNo = " "
        Company = " "
        Role = " "

        # Read Uploaded Image
       
        img_card = cv2.imread(filepath)
        img_card = cv2.resize(img_card , (widthImg , heightImg) , interpolation = cv2.INTER_AREA)
        img_card = cv2.cvtColor(img_card , cv2.COLOR_BGR2RGB)
#cv2.imwrite('colored_img.jpg' , img_card)
        imgGray = cv2.cvtColor(img_card , cv2.COLOR_BGR2GRAY)

        imgBlur = cv2.GaussianBlur(img_card , (5,5) , 0)

        imgBlur1 = cv2.GaussianBlur(imgGray , (5,5) , 0)
        cv2.imwrite(os.path.join('static', "gaus-blur.jpg"), imgBlur1)
        #img_card = cv2.cvtColor(img_card, cv2.COLOR_BGR2RGB)
        #plt.imshow(img_card)

        imgThreshold = cv2.Canny(imgBlur1,lower,upper)
        cv2.imwrite(os.path.join('static', "canny.jpg"), imgThreshold)
        imgThreshold = cv2.adaptiveThreshold(imgBlur1, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 19, 2)

       
        dilation = cv2.dilate(imgThreshold, kernel, iterations=2)
        erosion = cv2.erode(dilation, kernel, iterations=1)

        # Find contours
        contours, hierarchy = cv2.findContours(erosion, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea)

         #Draw contour on the original image
        cv2.drawContours(img_card, contours , 0, (0, 255, 0), 2)
        cnt_img = img_card.copy()
        plt.imshow(img_card)
        plt.imshow(cnt_img)
        #cv2.imwrite(os.path.join('static', "contour.jpg"), cnt_img)

        #Select the contour that corresponds to the business card
        card_contour = np.array([])
        card_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02*perimeter, True)
                if len(approx) == 4 and area > card_area:
                    card_contour = approx
                    card_area = area

        # Reorder 4 points of corner's corner
        myPoints = card_contour
        myPoints = myPoints.reshape((4,2))
        myPointsNew = np.zeros((4,1,2),dtype=np.int32)
        add = myPoints.sum(1)

        myPointsNew[0] = myPoints[np.argmin(add)]
        myPointsNew[3] = myPoints[np.argmax(add)]
        diff = np.diff(myPoints, axis=1)
        myPointsNew[1] = myPoints[np.argmin(diff)]
        myPointsNew[2] = myPoints[np.argmax(diff)]
        biggest_new = myPointsNew

        pts1 = np.float32(biggest_new) # PREPARE POINTS FOR WARP
        pts2 = np.float32([[0, 0],[widthImg, 0], [0, heightImg],[widthImg, heightImg]]) # PREPARE POINTS FOR WARP
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        imgWarp = cv2.warpPerspective(img_card, matrix, (widthImg, heightImg))

        cv2.imwrite(os.path.join('static', "wrap.jpg"), imgWarp)

# #plt.subplot(4,4,4),plt.imshow(imgWarpColored),plt.title("Wrapped",fontdict=font)
# #plt.imshow(imgWarp )


        # Convert to grayscale
        imgWarp = cv2.cvtColor(imgWarp, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(imgWarp, cv2.COLOR_RGB2GRAY)

        # Apply Gaussian blur to reduce noise and blur
        blur = cv2.GaussianBlur(gray, (7,7), sigmaX=33, sigmaY=33)

        # Apply adaptive thresholding to get a binary image
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Invert the binary image
        thresh = 255 - thresh

        #plt.imshow(thresh, cmap='gray')

        kernel1 = np.ones((2, 2), np.uint8)
        img_erosion = cv2.erode(thresh, kernel1, iterations=1)
        #plt.imshow(img_erosion) 
        cv2.imwrite(os.path.join('static', "erosion.jpg"), img_erosion)

        kernel2 = np.ones((2, 2), np.uint8)
        img_dilation = cv2.dilate(img_erosion, kernel2, iterations=1)
        #plt.imshow(img_dilation)
        cv2.imwrite(os.path.join('static', "dilation.jpg"), img_dilation)

        extractedInformation = pytesseract.image_to_string(thresh, config='--psm 4 --oem 3')
        splt = extractedInformation.split('\n')
        for i in range(len(splt)-1, -1, -1):
            if len(splt[i]) < 4:
                del splt[i]
        result = ', '.join(splt)
        extractedInformation = result.split(',')
        print(extractedInformation)


        # Extract the properties of extractedInformation
        name = extractedInformation[0]
        role = extractedInformation[1]
        company = extractedInformation[2] + extractedInformation[3]
        phone = extractedInformation[4]
        email = extractedInformation[5]
        website = extractedInformation[6]
        address = extractedInformation[7]
        # + extractedInformation[8]

# Send the extracted properties to the backend
        response = requests.post('http://127.0.0.1:5000/carddetails', json={
            'name': name,
            'role': role,
            'company': company,
            'phone': phone,
            'email': email,
            'website': website,     
            'address': address
        })

# Check the response status code and render the template
        if response.status_code == 200:
            return render_template('process.html', extractedInformation=extractedInformation)




        #extractedInformation = [line.split(':') for line in splt]
        #extractedInformation = [[elem.strip('[]\'') for elem in inner_list] for inner_list in extractedInformation]
        #print(extractedInformation)
      
        # extractedInformation = '\n'.join(splt)

        # # save the extracted information in the session
        # session['extractedInformation'] = extractedInformation        


        # Render template with processed image
        #return render_template('information.html', extractedInformation=extractedInformation)
       
        #return render_template('process.html', img_filename=filename)

    return "Image processed successfully"

 
@app.route('/extracted', methods=['GET', 'POST'])
def extracted():
    # get the extracted information from the session
    extractedInformation = session.get('extractedInformation')

    # render the information.html template with the extracted information
    return render_template('information.html', extractedInformation=extractedInformation)


if __name__ == '__main__':
    app.run(debug=True)



