from audio_manager import AudioManager

def play_audio(audio_manager, file_path):
    try:
        audio_manager.play_sound(file_path)
    except Exception as e:
        print(f"An error occurred: {e}")

def speak_text(audio_manager, text):
    try:
        audio_manager.speak_text_espeak(text)
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == '__main__':
    # Initialize the audio manager
    use_robot_hat = input("Use Robot HAT for audio? (yes/no): ").strip().lower() == 'yes'
    audio_manager = AudioManager(use_robot_hat=use_robot_hat)

    # Set the output device
    output_choice = input("Select audio output device ('hdmi0', 'hdmi1', 'headphones', 'hifiberry', 'usb', 'robot_hat'): ").strip().lower()
    audio_manager.set_output_device(output_choice)

    # Play a sound
    sound_path = './components/sounds/source/intro.wav'  # Update with your actual path if necessary
    play_audio(audio_manager, sound_path)

    # Optionally, use espeak to speak text
    text_to_speak = "Hello from PiCrawler!"
    speak_text(audio_manager, text_to_speak)
