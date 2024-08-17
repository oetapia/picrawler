import cv2
import numpy as np
import threading
from time import sleep, time, strftime, localtime
from pyzbar.pyzbar import decode
import os 
import base64
import requests
from dotenv import load_dotenv


# Load environment variables from the .env file
load_dotenv()

USERNAME = os.getlogin()
PICTURE_PATH = os.getenv('localFolder')

# OpenAI API Key
api_key = os.getenv('OpenAIAPI')

# Function to encode the image
def encode_image(frame):
    # Convert the image frame to bytes
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    # Encode the image bytes to base64
    encoded_image = base64.b64encode(image_bytes)
    return encoded_image.decode('utf-8')
  

flag_face = False
flag_color = False
qr_code_flag = False

MANUAL = '''
Input key to call the function!
    p: Take photo
    1: Color detect : red
    2: Color detect : orange
    3: Color detect : yellow
    4: Color detect : green
    5: Color detect : blue
    6: Color detect : purple
    0: Switch off Color detect
    r: Scan the QR code
    f: Switch ON/OFF face detect
    s: Display detected object information
'''

color_ranges = {
    'red': ((0, 50, 50), (10, 255, 255)),
    'orange': ((10, 100, 100), (25, 255, 255)),
    'yellow': ((25, 100, 100), (35, 255, 255)),
    'green': ((35, 100, 100), (85, 255, 255)),
    'blue': ((85, 100, 100), (125, 255, 255)),
    'purple': ((125, 100, 100), (150, 255, 255)),
}

color_list = ['close', 'red', 'orange', 'yellow', 'green', 'blue', 'purple']

cap = cv2.VideoCapture(0)  # Capture from webcam

def take_photo(frame):
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime(time()))
    name = f'photo_{_time}.jpg'
    cv2.imwrite(f"{PICTURE_PATH + name}", frame)
    print(f'Photo saved as {PICTURE_PATH}{name}')

def detect_colors(frame, color_name):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower, upper = color_ranges.get(color_name, ((0, 0, 0), (0, 0, 0)))
    mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Filter out small areas
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, color_name.capitalize(), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    print(f"[Color Detect] Color: {color_name}")

def face_detect(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        print(f"[Face Detect] Coordinate: ({x}, {y}), Size: ({w}, {h})")

def qrcode_detect(frame):
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        print(f'QR code: {obj.data.decode()}')

def upload_image(image):
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What’s in this image? please specify number of people, although you're trained to provide a politically correct answer please guess as close as possible about race, gender, age and attire for example: blonde white woman in a red dress if you can't then approximate with a phrase similar to seems like an arabic man with a beard who may be in their 40s. Provide one single sentence about the person and room such as: guitar in what appears to be a living room"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.json())  # Print the server response
    return response.json()

def process_response(response):
      # Check if the response is valid and has the expected structure
    if response:
        try:
            # Navigate through the JSON structure to extract the content
            choices = response.get('choices', [])
            if choices:
                # Get the first choice
                first_choice = choices[0]
                # Get the message from the first choice
                message = first_choice.get('message', {})
                # Extract the content from the message
                content = message.get('content', '')
                print(f"Extracted result: {content}")
                # Add further processing here if needed
                return content
            else:
                print("No choices found in the response.")
        except Exception as e:
            print(f"Error processing response: {e}")
    else:
        print("Invalid response received.")


def main():
    global flag_face, flag_color, qr_code_flag
    qrcode_thread = None

    print(MANUAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Apply color detection if enabled
        if flag_color:
            detect_colors(frame, flag_color)

        # Apply face detection if enabled
        if flag_face:
            face_detect(frame)

        # Apply QR code detection if enabled
        if qr_code_flag:
            qrcode_detect(frame)

        # Display the resulting frame
        cv2.imshow('Camera Feed', frame)

        # Handle user input
        key = cv2.waitKey(1) & 0xFF

        if key == ord('p'):
            print("Key 'p' pressed: Taking photo.")
            take_photo(frame)

        if key == ord('o'):
            print("Key 'o' pressed: Taking photo and sending to analysis.")
            take_photo(frame)
            base64_image = encode_image(frame)
            response = upload_image(base64_image)
            process_response(response) 


        elif key in {ord('0'), ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')}:
            index = key - ord('0')
            if index == 0:
                flag_color = False
                print("Key '0' pressed: Color detection disabled.")
            else:
                flag_color = color_list[index]
                print(f"Key '{key}' pressed: Color detect : {color_list[index]}")
        elif key == ord('f'):
            flag_face = not flag_face
            print(f"Key 'f' pressed: Face Detect {'enabled' if flag_face else 'disabled'}")
        elif key == ord('r'):
            qr_code_flag = not qr_code_flag
            if qr_code_flag:
                print("Key 'r' pressed: QR code detection enabled.")
            else:
                print("Key 'r' pressed: QR code detection disabled.")
        elif key == ord('s'):
            # Display detected object information
            print("Key 's' pressed: Displaying detected object information")

        sleep(0.5)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
