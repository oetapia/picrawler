from picrawler import Picrawler
from time import sleep, time, strftime, localtime
from robot_hat import Music,TTS
from vilib import Vilib
import readchar
import random
import threading
import board
import busio
import adafruit_ssd1306
import os 
import base64
import requests
from dotenv import load_dotenv
import re


# Load environment variables from the .env file
load_dotenv()

USERNAME = os.getlogin()
PICTURE_PATH = f"/home/{USERNAME}/Pictures/"

# Sound effect file
audio_effect = '/home/pi/picrawler/examples/sounds/hoot.wav'

# OpenAI API Key
api_key = os.getenv('OpenAIAPI')


crawler = Picrawler()


music = Music()
tts = TTS()

# Initialize I2C and the OLED display
i2c = busio.I2C(board.SCL, board.SDA)

# Try to initialize the OLED display
try:
    display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
    oled_present = True
except Exception as e:
    print("OLED display not detected or initialization failed.")
    oled_present = False

# If OLED is present, clear the display
if oled_present:
    display.fill(0)  # 0 is black
    display.show()


manual = '''
Press keys on keyboard to control Picrawler!
    w: Forward
    a: Turn left
    s: Backward
    d: Turn right
    p: Take photo
    o: Send to analysis
    space: Say the target again
    Ctrl^C: Quit
'''

color = "red"
color_list=["red","orange","yellow","green","blue","purple"]
#color_list=["red"]
key_dict = {
    'w': 'forward',
    's': 'backward',
    'a': 'turn_left',
    'd': 'turn_right',
}



def take_photo(photo_type):
    print("taking photo")
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime(time()))
    name = 'photo_%s' % _time  # Do not add .jpg here
    photo_path = os.path.join(PICTURE_PATH, name + '.jpg')
    
    if photo_type == "local":
        success = Vilib.take_photo(name, PICTURE_PATH)
        if success:
            print('Photo saved as %s' % photo_path)
            return photo_path
        else:
            print("Failed to save photo.")
            return None

    elif photo_type == "upload":
        success = Vilib.take_photo(name, PICTURE_PATH)  # Use the same method, but handle upload
        if success:
            print("Photo captured successfully.")
            with open(photo_path, 'rb') as image_file:
                photo_data = image_file.read()  # Read the image data into memory
            
            os.remove(photo_path)  # Optionally delete the temporary file after reading
            return photo_data
        else:
            print("Failed to capture photo.")
            return None

    else:
        print("Invalid photo type specified.")
        return None

# Function to encode the image
def encode_image(frame):
    # Encode the image bytes to base64
    encoded_image = base64.b64encode(frame)
    return encoded_image.decode('utf-8')

def upload_image(image):
    print("analyzing image")
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
            "text": "What’s in this image? please specify number of people, although you're trained to provide a politically correct answer please guess as close as possible about race, gender, age and attire for example: blonde white woman in a red dress if you can't then approximate with a phrase similar to seems like an arabic man with a beard who may be in their 40s. Provide one single sentence about the person and room such as: guitar in what appears to be a living room. The first word needs to have brackets [guitar] if you can't find a good word then use [not clear]"
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

def renew_color_detect():
    global color
    color = random.choice(color_list)
    Vilib.color_detect(color)
    music.sound_play_threading(audio_effect)
    sleep(0.05)   
    tts.say("Hoot says find  " + color)
    if oled_present:
            # Update the OLED display with the current servo being reset
            display.fill(0)  # Clear the display
            display.text("Hoot says find " + color, 0, 0, 1)  # Display which color
            display.show()


def display_text_multiline(text, y_start=16, line_height=10):
    max_line_length = 20  # Adjust based on your font and display width
    lines = [text[i:i + max_line_length] for i in range(0, len(text), max_line_length)]
    
    if oled_present:
        display.fill(0)  # Clear the display
        display.text("Detected", 0, 0, 1)  # Display "QR" on the first line
        y = y_start
        for line in lines:
            display.text(line, 0, y, 1)  # Display each line at the appropriate y position
            y += line_height  # Move to the next line position
            if y + line_height > 64:  # Stop if we exceed the display height
                break
        display.show()


key = None
lock = threading.Lock()



def key_scan_thread():
    global key
    while True:
        key_temp = readchar.readkey()
        with lock:
            key = key_temp.lower()
            if key == ' ':
                key = 'space'
            elif key == 'q':
                key = 'quit'
                break
            elif key == 'y':
                key = 'skip'
        sleep(0.01)

def main():
    global key
    action = None
    Vilib.camera_start(vflip=False,hflip=False)
    Vilib.display(local=False,web=True)
    Vilib.qrcode_detect_switch(True)
    sleep(0.8)
    speed = 80
    print(manual)

    sleep(1)
    _key_t = threading.Thread(target=key_scan_thread)
    _key_t.setDaemon(True)
    _key_t.start()


    tts.say("Lets play find the color")
    if oled_present:
        display.fill(0)  # Clear the display
        display.text("Find the color.", 0, 0, 1)
        display.show()
    sleep(0.05)   
    renew_color_detect()
    last_qr_data = ""  # Track the last detected QR code


    while True:


        if Vilib.detect_obj_parameter['color_n']!=0 and Vilib.detect_obj_parameter['color_w']>100:
            tts.say("awesome!")
            if oled_present:
                display.fill(0)  # Clear the display
                display.text("You found " + color , 0, 0, 1)
                display.show()
            sleep(0.05)   
            tts.say("you found " + color)
            sleep(0.05)   
            renew_color_detect()

        with lock:
            if key != None and key in ('wsad'):
                action = key_dict[str(key)]
                key =  None
            elif key == 'space':
                music.sound_play_threading(audio_effect)
                sleep(0.05)   
                tts.say("Try to find " + color)
                if oled_present:
                    display.fill(0)  # Clear the display
                    display.text("Try to find "+ color , 0, 0, 1)
                    display.show()
                key =  None
            elif key == 'skip':
                    renew_color_detect()  # Skip the current color and choose a new one
                    key = None
            elif key == 'o':
                print("Key 'o' pressed: Taking photo and sending to analysis.")
                photo = take_photo("upload")
                base64_image = encode_image(photo)
                response = upload_image(base64_image)
                analysis = process_response(response)
                safe_string = analysis.replace("'", "")
                brackets_content = re.search(r'\[(.*?)\]', safe_string)
                # Extract the content from the match object or default to an empty string
                brackets_content = brackets_content.group(1) if brackets_content else ""
                brackets_cleaned = re.sub(r'\[.*?\]', '', brackets_content)
                clean_string = re.sub(r'\[.*?\]', '', safe_string)
                print(clean_string)
                print(brackets_content)
                if oled_present:
                    # Update the OLED display with the current servo being reset
                    display_text_multiline(brackets_cleaned)  # Display single word describing scene
                tts.say("Hoot saw " + clean_string)
                key =  None
            elif key == 'quit':
                _key_t.join()
                Vilib.camera_close()
                print("\n\rQuit") 
                break 
            elif key == '6':
                # QR code detection and announcement
                current_qr_data = Vilib.detect_obj_parameter['qr_data']

                if current_qr_data == None and Vilib.detect_obj_parameter['color_n'] == 0:
                    print("Nothing to see here: ", current_qr_data)
                else:
                    if current_qr_data != last_qr_data:
                        last_qr_data = current_qr_data
                        music.sound_play_threading(audio_effect)
                        print("QR Code detected:", current_qr_data)
                        tts.say("I found a QR code that says: " + current_qr_data)       
                        if oled_present:
                            # Update the OLED display with the current servo being reset
                            display_text_multiline(current_qr_data)  # Display QR data on OLED

                key = None  # Reset key after processing

        if action != None:
            crawler.do_action(action,1,speed)  
            action = None
        sleep(0.05)          
     

# Ensure thread termination in `main()`
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTerminated by user.")
    finally:
        # Cleanup code if needed
        Vilib.camera_close()
        print("Cleanup completed.")