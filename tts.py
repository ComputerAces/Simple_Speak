# Simple_Speak/tts.py

import outetts
import os
import logging

# Configure logging
# Note: main.py also configures logging, the most restrictive level will apply.
# Consider centralizing logging config if needed.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TTSHandler:
    """
    Handles Text-to-Speech generation using OuteAI TTS models.
    Initializes the model interface upon creation.
    """
    # --- ADDED: Define a default voice ID ---
    # This should be a valid ID from the outetts library if known,
    # otherwise, the library might have its own internal default.
    # Check outetts documentation for available default speaker IDs.
    # Using a plausible placeholder here:
    DEFAULT_VOICE = "EN-FEMALE-1-NEUTRAL"
    # -----------------------------------------

    def __init__(self, model_size=outetts.Models.VERSION_1_0_SIZE_1B,
                 backend=outetts.Backend.LLAMACPP, # llama.cpp recommended for best results
                 quantization=outetts.LlamaCppQuantization.FP16): # FP16 is a common choice
        """
        Initializes the OuteTTS interface. Downloads models if necessary.
        """
        logging.info(f"Initializing OuteTTS Interface (Model: {model_size}, Backend: {backend}, Quant: {quantization})...")
        logging.info("This may take some time on the first run as models might be downloaded.")
        self.interface = None # Initialize interface to None
        try:
            self.config = outetts.ModelConfig.auto_config(
                model=model_size,
                backend=backend,
                quantization=quantization # Specify quantization only for llama.cpp
            )
            # If using HF backend, quantization should not be specified here
            # self.config = outetts.ModelConfig.auto_config(
            #     model=model_size,
            #     backend=outetts.Backend.HF
            # )

            self.interface = outetts.Interface(config=self.config)
            logging.info("OuteTTS Interface initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize OuteTTS Interface: {e}", exc_info=True)
            # Set self.interface to None explicitly on failure
            self.interface = None
            # Optional: re-raise if initialization failure should stop the app
            # raise

        # Define the recommended sampler configuration only if interface initialized
        if self.interface:
            self.sampler_config = outetts.SamplerConfig(
                temperature=0.4,
                repetition_penalty=1.1,
                repetition_range=64, # Crucial: Windowed repetition penalty
                top_k=40,
                top_p=0.9,
                min_p=0.05
            )
            logging.info(f"Using Sampler Config: {self.sampler_config}")
        else:
            self.sampler_config = None # No sampler config if interface failed


    # --- speak METHOD (As Provided - requires DEFAULT_VOICE defined above) ---
    def speak(self,
              text: str,
              output_file: str,
              speaker_id: str = None, # ID for built-in voices
              voice_file: str = None   # Path for cloning
             ) -> bool:
        """
        Generates speech from text using the initialized OuteTTS interface.
        Prioritizes voice_file for cloning.
        If speaker_id is provided, attempts to load that specific speaker ID.
        Falls back to attempting to load self.DEFAULT_VOICE if initial load fails
        or if no speaker_id/voice_file is provided.

        Args:
            text (str): The text content to synthesize.
            output_file (str): Path to save the generated WAV audio file.
            speaker_id (str, optional): ID of a built-in speaker (e.g., "EN-FEMALE-1-NEUTRAL").
                                        Defaults to None.
            voice_file (str, optional): Path to a WAV/MP3 file for voice cloning.
                                        Takes precedence over speaker_id. Defaults to None.

        Returns:
            bool: True if speech generation was successful, False otherwise.
        """
        if not self.interface:
            logging.error("OuteTTS Interface is not initialized. Cannot generate speech.")
            return False
        if not self.sampler_config:
            logging.error("OuteTTS Sampler Config is not set (likely due to init failure). Cannot generate speech.")
            return False
        if not text:
            logging.warning("Input text is empty. No audio generated.")
            # Return False as no file generated
            return False
        if not output_file:
             logging.error("Output file path not specified.")
             return False

        # Ensure output directory exists
        try:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logging.info(f"Created output directory for TTS: {output_dir}")
        except Exception as e:
             logging.error(f"Error creating directory for {output_file}: {e}")
             return False

        speaker = None # Initialize speaker object
        speaker_source = "Unknown"
        final_speaker_id_to_load = None # Track which ID we will actually try to load

        try:
            # 1. Prioritize voice cloning file
            if voice_file and os.path.exists(voice_file):
                logging.info(f"Attempting voice cloning from: {voice_file}")
                try:
                     speaker = self.interface.create_speaker(voice_file)
                     speaker_source = f"Cloned File ({os.path.basename(voice_file)})"
                     logging.info("Speaker profile created successfully from file.")
                     # If cloning succeeds, speaker is set, we skip ID loading below
                except Exception as e:
                    logging.error(f"Error creating speaker profile from {voice_file}: {e}. Trying speaker ID or default...")
                    speaker = None # Reset speaker if cloning failed

            # 2. If no clone used, determine which speaker ID to load
            if speaker is None: # Only proceed if cloning wasn't used or failed
                 if speaker_id:
                      # Use the provided speaker ID
                      final_speaker_id_to_load = speaker_id
                      speaker_source = f"Provided ID ({speaker_id})"
                      logging.info(f"Attempting to load provided speaker ID: {final_speaker_id_to_load}")
                 else:
                      # No file and no ID provided, use the class default
                      final_speaker_id_to_load = self.DEFAULT_VOICE
                      speaker_source = f"Class Default ID ({final_speaker_id_to_load})"
                      logging.info(f"No speaker ID or voice file provided. Attempting to load class default: {final_speaker_id_to_load}")

                 # 3. Attempt to load the determined speaker ID
                 if final_speaker_id_to_load:
                      try:
                           speaker = self.interface.load_default_speaker(final_speaker_id_to_load)
                           logging.info(f"Successfully loaded speaker: {speaker_source}")
                      except Exception as e:
                           logging.error(f"CRITICAL: Failed to load speaker ID '{final_speaker_id_to_load}' using load_default_speaker: {e}")
                           # Log specific error if it's the main default voice failing
                           if final_speaker_id_to_load == self.DEFAULT_VOICE:
                                logging.critical(f"Failure loading the primary DEFAULT_VOICE ('{self.DEFAULT_VOICE}'). Check outetts installation and model data.")
                           speaker = None # Ensure speaker is None if loading failed
                           speaker_source = f"Failed Load ({final_speaker_id_to_load})"
                 else:
                      # This case should not happen based on logic above, but as safety:
                      logging.error("Could not determine a speaker ID to load.")
                      speaker = None


            # 4. Check if we have a valid speaker object before proceeding
            if speaker is None:
                logging.error(f"Failed to obtain a valid speaker profile (Source attempted: {speaker_source}). Cannot generate speech.")
                return False # Exit if no speaker profile could be loaded or created

            # 5. Configure generation
            generation_config = outetts.GenerationConfig(
                text=text,
                generation_type=outetts.GenerationType.CHUNKED,
                speaker=speaker, # Pass the loaded or created speaker object
                sampler_config=self.sampler_config,
            )
            logging.info(f"Generating speech using speaker source: [{speaker_source}] for text: '{text[:50]}...'")

            # 6. Generate audio
            output_audio = self.interface.generate(config=generation_config)

            # 7. Save the audio
            output_audio.save(output_file)
            logging.info(f"Speech generated and saved to: {output_file}")
            return True

        except Exception as e:
            logging.error(f"An unexpected error occurred during speech generation: {e}", exc_info=True)
            return False

# Example of how to use the class (optional, for direct testing)
# if __name__ == "__main__":
#     print("Testing TTSHandler...")
#     try:
#         # Initialization might take time and download models
#         handler = TTSHandler()
#         if handler.interface: # Proceed only if initialization was successful
#             # Test default voice
#             success1 = handler.speak("Hello, this is a test using the default voice.", output_file="test_default.wav")
#             print(f"Default voice test successful: {success1}")

#             # Test with a voice file (replace with an actual path if you have one)
#             # Make sure you have a short audio file (e.g., 10 seconds) at this path
#             test_voice = "path/to/your/sample_voice.wav" # <-- IMPORTANT: CHANGE THIS PATH
#             if os.path.exists(test_voice):
#                  success2 = handler.speak("Testing voice cloning with a provided audio file.", voice_file=test_voice, output_file="test_cloned.wav")
#                  print(f"Cloned voice test successful: {success2}")
#             else:
#                  print(f"Skipping cloned voice test: Voice file not found at '{test_voice}'")
#         else:
#             print("TTSHandler initialization failed. Cannot run tests.")

#     except Exception as e:
#         print(f"TTSHandler test failed during setup or execution: {e}")