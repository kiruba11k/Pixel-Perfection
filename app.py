from flask import Flask, redirect, render_template, request, url_for
from flask import Flask, render_template, request, jsonify,send_file
from ibm_botocore.client import Config, ClientError
from flask import session

import cv2
import numpy as np
import io
import base64
import ibm_boto3
import os
import ibm_db

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form data
        name = request.form.get('uname')
        password = request.form.get('pasword')

        conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=2f3279a5-73d1-4859-88f0-a6c3e6b4b907.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30756;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lhr17622;PWD=dBrHOnecwHxMNRzp;","","")
        stmt=ibm_db.prepare(conn,"SELECT * FROM REGISTER WHERE NAME=? AND PASSWORD =?")
        ibm_db.bind_param(stmt,1,name)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)

        if ibm_db.fetch_row(stmt):
            # Store the user's name in the session
            session['username'] = name
            return redirect(url_for('home'))
        else:
            return "Invalid username or password"
        
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove the username from the session
    session.pop('username', None)
    return redirect(url_for('home'))
       
# IBM COS configuration
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"  # Enter your COS endpoint URL
COS_API_KEY_ID = "voljiuqu4FVs9NF8bQGbnLoxfvkDhT6jE-BgFhf94uc9"  # Enter your COS API key
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/4b0c90db31564e0fa35fdbe20b04f82b:8d8cb6b3-baa3-4d1c-8635-afb651b9aa79::"  # Enter your COS instance CRN
COS_BUCKET_NAME = 'uploadpx'  # Enter your COS bucket name

def upload_to_cos(file_bytes, filename):
    cos_client = ibm_boto3.client('s3',
                                  ibm_api_key_id=COS_API_KEY_ID,
                                  ibm_service_instance_id=COS_INSTANCE_CRN,
                                  config=Config(signature_version='oauth'),
                                  endpoint_url=COS_ENDPOINT)

    try:
        cos_client.put_object(Bucket=COS_BUCKET_NAME, Key=filename, Body=file_bytes)
        return True
    except ClientError as e:
        print('Error uploading to COS:', e)
        return False


@app.route('/')
def indexr():
    return redirect(url_for('remov'))

@app.route('/remov', methods=['POST', 'GET'])
def remov():
    if 'username' not in session:  # Redirect to login page if not logged in
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Load the image
        file = request.files['image']
        image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Convert image to RGB color space
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Create a mask to indicate areas of probable foreground and background
        mask = np.zeros(image_rgb.shape[:2], np.uint8)

        # Define the background and foreground model
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Define the rectangular region for GrabCut
        rect = (10, 10, image_rgb.shape[1] - 10, image_rgb.shape[0] - 10)

        # Apply GrabCut algorithm to estimate the foreground mask
        cv2.grabCut(image_rgb, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # Create a mask with probable foreground and definite foreground regions
        mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')

        # Apply the mask to the original image to remove the background
        result = image_rgb * mask[:, :, np.newaxis]

        # Convert the result image to base64 string
        _, buffer = cv2.imencode('.jpg', result)
        result_image_str = base64.b64encode(buffer).decode()

        # Save the result image to IBM COS
        result_image_filename = 'result.jpg'
        upload_to_cos(buffer.tobytes(), result_image_filename)

        # Return the result image URL
        return jsonify({'result_image': f'{COS_ENDPOINT}/{COS_BUCKET_NAME}/{result_image_filename}'})

    return render_template('remov.html')



COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"  # Enter your COS endpoint URL
COS_API_KEY_ID = "voljiuqu4FVs9NF8bQGbnLoxfvkDhT6jE-BgFhf94uc9"  # Enter your COS API key
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/4b0c90db31564e0fa35fdbe20b04f82b:8d8cb6b3-baa3-4d1c-8635-afb651b9aa79::"  # Enter your COS instance CRN
COS_BUCKET_NAME = 'cartoonpjx'  # Enter your COS bucket name

def upload_to_cos(file_bytes, filename):
    cos_client = ibm_boto3.client(
        "s3",
        ibm_api_key_id=COS_API_KEY_ID,
        ibm_service_instance_id=COS_INSTANCE_CRN,
        config=Config(signature_version="oauth"),
        endpoint_url=COS_ENDPOINT,
    )

    try:
        cos_client.put_object(Bucket=COS_BUCKET_NAME, Key=filename, Body=file_bytes)
        return True
    except ClientError as e:
        print("Error uploading to COS:", e)
        return False

@app.route('/')
def indexc():
    return redirect(url_for('cartoon'))


@app.route('/cartoon', methods=['POST', 'GET'])
def cartoon():
    if 'username' not in session:  # Redirect to login page if not logged in
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Load the image
        file = request.files['image']
        image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Apply cartoon effect to the image
        cartoon_image = cv2.stylization(image, sigma_s=150, sigma_r=0.25)

        # Convert the cartoon image to base64 string
        _, buffer = cv2.imencode('.jpg', cartoon_image)
        result_image_str = base64.b64encode(buffer).decode()

        # Save the result image to IBM COS
        result_image_filename = 'result_cartoon.jpg'
        upload_to_cos(buffer.tobytes(), result_image_filename)

        # Return the result image URL
        return jsonify({'result_image': f'{COS_ENDPOINT}/{COS_BUCKET_NAME}/{result_image_filename}'})

    return render_template('cartoon.html')

# IBM COS configuration
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"  # Enter your COS endpoint URL
COS_API_KEY_ID = "voljiuqu4FVs9NF8bQGbnLoxfvkDhT6jE-BgFhf94uc9"  # Enter your COS API key
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/4b0c90db31564e0fa35fdbe20b04f82b:8d8cb6b3-baa3-4d1c-8635-afb651b9aa79::"  # Enter your COS instance CRN
COS_BUCKET_NAME = 'gauspjx'  # Enter your COS bucket name



def upload_to_cos(file_bytes, filename):
    cos_client = ibm_boto3.client('s3',
                                  ibm_api_key_id=COS_API_KEY_ID,
                                  ibm_service_instance_id=COS_INSTANCE_CRN,
                                  config=Config(signature_version='oauth'),
                                  endpoint_url=COS_ENDPOINT)

    try:
        cos_client.put_object(Bucket=COS_BUCKET_NAME, Key=filename, Body=file_bytes)
        return True
    except ClientError as e:
        print('Error uploading to COS:', e)
        return False


@app.route('/')
def indexf2():
    return redirect(url_for('filter2'))


@app.route('/filter2', methods=['POST', 'GET'])
def filter2():
    

    if request.method == 'POST':
        # Load the image
        file = request.files['image']
        image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Apply Filter 2 to the image (Gaussian blur)
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Convert the result image to base64 string
        _, buffer = cv2.imencode('.jpg', blurred)
        result_image_str = base64.b64encode(buffer).decode()

        # Save the result image to IBM COS
        result_image_filename = 'result.jpg'
        upload_to_cos(buffer.tobytes(), result_image_filename)

        # Return the result image URL
        return jsonify({'result_image': f'{COS_ENDPOINT}/{COS_BUCKET_NAME}/{result_image_filename}'})

    return render_template('filter2.html')
    



# IBM COS configuration
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"  # Enter your COS endpoint URL
COS_API_KEY_ID = "voljiuqu4FVs9NF8bQGbnLoxfvkDhT6jE-BgFhf94uc9"  # Enter your COS API key
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/4b0c90db31564e0fa35fdbe20b04f82b:8d8cb6b3-baa3-4d1c-8635-afb651b9aa79::"  # Enter your COS instance CRN
COS_BUCKET_NAME = 'beautypx'  # Enter your COS bucket name

def upload_to_cos(file_bytes, filename):
    cos_client = ibm_boto3.client('s3',
                                  ibm_api_key_id=COS_API_KEY_ID,
                                  ibm_service_instance_id=COS_INSTANCE_CRN,
                                  config=Config(signature_version='oauth'),
                                  endpoint_url=COS_ENDPOINT)

    try:
        cos_client.put_object(Bucket=COS_BUCKET_NAME, Key=filename, Body=file_bytes)
        return True
    except ClientError as e:
        print('Error uploading to COS:', e)
        return False
    
@app.route("/")
def indexb():
    return redirect(url_for('filter1'))

@app.route("/filter1", methods=['POST', 'GET'])
def filter1():
    if 'username' not in session:  # Redirect to login page if not logged in
        return redirect(url_for('login'))

    if request.method == "POST":
        # Load the uploaded image
        file = request.files["image"]
        image = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Apply Filter 1 to the image
        # Example: Grayscale conversion
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Convert the filtered image to base64 string
        _, buffer = cv2.imencode(".jpg", gray)
        filtered_image_str = base64.b64encode(buffer).decode()

        # Save the filtered image to IBM COS
        filtered_image_filename = "filtered_image.jpg"
        upload_to_cos(buffer.tobytes(), filtered_image_filename)

        # Return the filtered image URL
        return jsonify({"filtered_image": f"{COS_ENDPOINT}/{COS_BUCKET_NAME}/{filtered_image_filename}"})

    return render_template('filter1.html')

@app.route("/cartoono")
def cartoono():
    return render_template('cartoono.html')

@app.route("/testimonial")
def testimonial():
    return render_template('testimonial.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name=request.form['name']
        password=request.form['password']
        mail=request.form['mail']

        conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=2f3279a5-73d1-4859-88f0-a6c3e6b4b907.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30756;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lhr17622;PWD=dBrHOnecwHxMNRzp;","","")

        stmt=ibm_db.prepare(conn,"INSERT INTO REGISTER(NAME,PASSWORD,MAIL) VALUES (?,?,?)")
        ibm_db.bind_param(stmt,1,name)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.bind_param(stmt,3,mail)
        ibm_db.execute(stmt)
        ibm_db.close(conn)


        return redirect(url_for('login'))



    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True,port=5001,host='0.0.0.0')
