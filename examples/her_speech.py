import pyttsx3

def test_tts_pyttsx3():
    try:
        # Initialize the TTS engine with a specific driver
        #engine = pyttsx3.init(driverName='sapi5')  # For Windows
        engine = pyttsx3.init(driverName='nsss')  # For macOS
        # engine = pyttsx3.init(driverName='espeak')  # For Linux
        
        # Set properties (optional)
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1)  # Volume level (0.0 to 1.0)
        
        # Text to be spoken
        text = "Hello, this is a test of text to speech using pyttsx3."
        
        # Convert text to speech
        engine.say(text)
        engine.runAndWait()
        print("pyttsx3 is working correctly.")
    except Exception as e:
        print(f"Error initializing pyttsx3: {e}")

if __name__ == "__main__":
    test_tts_pyttsx3()
