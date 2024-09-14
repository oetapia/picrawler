import os


# Define the directory where the sound files are located
SOUND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sounds/source'))

# Sound file paths
intro = os.path.join(SOUND_DIR, 'intro.wav')
hoot = os.path.join(SOUND_DIR, 'hoot.wav')
success = os.path.join(SOUND_DIR, 'success.wav')
error = os.path.join(SOUND_DIR, 'error.wav')

def get_sound_path(sound_file):
    """
    Get the fully qualified path to the sound file.
    
    :param sound_file: The sound file (relative path).
    :return: The absolute path to the sound file.
    """
    return os.path.join(os.path.dirname(__file__), sound_file)

def play(sound_file, audio_manager):
    """
    Play the sound file using the provided AudioManager instance.
    
    :param sound_file: The relative path to the sound file in the library.
    :param audio_manager: An instance of AudioManager for sound playback.
    """
    full_sound_path = get_sound_path(sound_file)
    audio_manager.play_sound(full_sound_path)