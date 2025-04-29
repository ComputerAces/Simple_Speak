# Simple_Speak/main.py

import os
import datetime
import logging
import json
from tts import TTSHandler # Import the handler class
from playsound import playsound # Keep playsound for playback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_DIR = "cache"
CONFIG_FILE = "config.json"

def ensure_cache_dir():
    """Ensures the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
            logging.info(f"Created cache directory: {CACHE_DIR}")
        except OSError as e:
            logging.error(f"Error creating cache directory {CACHE_DIR}: {e}")
            return False
    return True

def load_config():
    """Loads configuration from config.json."""
    default_config = {"speaker_id": None, "voice_file": None}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure keys exist, default to None if missing
                if "speaker_id" not in config:
                    config["speaker_id"] = None
                if "voice_file" not in config:
                    config["voice_file"] = None
                # Basic validation: check if voice_file exists if specified
                if config["voice_file"] and not os.path.exists(config["voice_file"]):
                     logging.warning(f"Voice file specified in {CONFIG_FILE} not found: {config['voice_file']}. It will be ignored.")
                     config["voice_file"] = None # Ignore non-existent file
                return config
        except json.JSONDecodeError:
            logging.error(f"Error decoding {CONFIG_FILE}. Using default configuration.")
            return default_config
        except Exception as e:
            logging.error(f"Error loading {CONFIG_FILE}: {e}. Using default configuration.")
            return default_config
    else:
        logging.info(f"{CONFIG_FILE} not found. Using default configuration.")
        return default_config

def play_audio(file_path):
    """Plays the audio file at the specified path."""
    if os.path.exists(file_path):
        try:
            logging.info(f"Playing audio file: {file_path}")
            playsound(file_path)
            logging.info("Playback finished.")
        except Exception as e:
            # playsound can be finicky, especially with paths or permissions
            logging.error(f"Error playing audio file {file_path}: {e}", exc_info=True)
            print(f"Error: Could not play audio file '{file_path}'. Check logs.")
    else:
        logging.error(f"Audio file not found for playback: {file_path}")
        print(f"Error: Audio file '{file_path}' not found.")


def main():
    """Main application loop."""
    if not ensure_cache_dir():
        print("Failed to create cache directory. Exiting.")
        return

    print("Initializing TTS Handler (this might take a while)...")
    try:
        tts_handler = TTSHandler() # Initialize the handler
    except Exception as e:
         # Catch potential init errors shown in TTSHandler's __init__
         print(f"FATAL: Failed to initialize TTS Handler: {e}")
         print("Please check your outetts installation, model downloads, and configurations.")
         return # Exit if handler cannot be initialized

    # Check if initialization actually succeeded within the handler
    if not tts_handler.interface:
         print("FATAL: TTS Interface could not be initialized (check logs for details). Exiting.")
         return


    print("\nSimple Speak App (using OuteTTS)")
    print("Type 'quit' or 'exit' to stop.")

    config = load_config() # Load config once at the start

    while True:
        try:
            text_input = input("\nEnter text to synthesize: ")
            if text_input.lower() in ['quit', 'exit']:
                break
            if not text_input:
                print("Please enter some text.")
                continue

            # Generate filename with date and time (use .wav extension)
            now = datetime.datetime.now()
            filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav" # Use .wav
            output_path = os.path.join(CACHE_DIR, filename)

            # Synthesize speech using the handler
            logging.info(f"Synthesizing text: '{text_input}'")
            # Pass relevant config values to speak method
            success = tts_handler.speak(
                text=text_input,
                output_file=output_path,
                speaker_id=config.get("speaker_id"),
                voice_file=config.get("voice_file") # Will be None if not found or invalid
            )

            if success:
                # Play the generated audio
                play_audio(output_path)
            else:
                print("Sorry, failed to generate audio for the text (check logs).")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            print("An unexpected error occurred. Check logs.")

if __name__ == "__main__":
    main()