import os
import subprocess
from robot_hat import Music, TTS

class AudioManager:
    def __init__(self, use_robot_hat=False):
        self.output_device = 'headphones'  # Default to Headphones
        self.use_robot_hat = use_robot_hat
        if self.use_robot_hat:
            self.music = Music()
            self.tts = TTS()

    def set_output_device(self, device):
        valid_devices = {
            'hdmi0': 'plughw:0,0',  # vc4hdmi0
            'hdmi1': 'plughw:1,0',  # vc4hdmi1
            'headphones': 'plughw:2,0',  # bcm2835 Headphones
            'hifiberry': 'plughw:3,0',  # snd_rpi_hifiberry_dac
            'usb': 'plughw:4,0',  # USB Audio
            'robot_hat': 'robot_hat'
        }
        
        if device not in valid_devices:
            raise ValueError(f"Invalid device. Choose from {list(valid_devices.keys())}")

        self.output_device = valid_devices[device]

    def play_sound(self, sound_path):
        # Use absolute path to avoid issues with relative paths
        absolute_path = os.path.abspath(sound_path)

        if self.output_device == 'robot_hat':
            self._play_sound_robot_hat(absolute_path)
        elif self.output_device in ['plughw:0,0', 'plughw:1,0', 'plughw:2,0', 'plughw:3,0', 'plughw:4,0']:
            command = ['aplay', '-D', self.output_device, absolute_path]
        else:
            raise ValueError("Unknown output device")

        try:
            if self.output_device != 'robot_hat':
                subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while playing sound: {e}")

    def _play_sound_robot_hat(self, sound_path):
        self.music.play(sound_path)

    def speak_text(self, text):
        if not self.use_robot_hat:
            raise RuntimeError("Robot HAT is not enabled.")
        self.tts.say(text)

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
    audio_manager.play_sound(sound_path)

    # Optionally, use the PiCrawler Robot HAT to speak text
    if use_robot_hat:
        text_to_speak = "Hello from PiCrawler!"
        audio_manager.speak_text(text_to_speak)
