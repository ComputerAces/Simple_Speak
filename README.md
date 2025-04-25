# Simple Speak App

A simple command-line TTS app using `outetts` to synthesize speech from text, supporting various voices/cloning, saving WAV, and playback.

## Features

* **Text-to-Speech:** Converts text input into speech using the `outetts` library[cite: 2].
* **Voice Options:**
    * Use default `outetts` voices.
    * Specify a built-in speaker ID (e.g., "EN-FEMALE-1-NEUTRAL").
    * Clone a voice from a provided WAV/MP3 audio file.
* **Audio Output:** Saves synthesized speech as `.wav` files in a `cache` directory[cite: 2].
* **Playback:** Automatically plays the generated audio file using `playsound`[cite: 2].
* **Configuration:** Customize the default speaker ID or voice cloning file via `config.json`[cite: 1, 2].

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
2.  **Install dependencies:**
    Make sure you have Python 3 installed. Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *Note:* The first time you run the application, the `outetts` library may need to download model files, which can take some time.

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  **Enter text:** When prompted, type the text you want to synthesize and press Enter[cite: 2].
3.  **Listen:** The application will generate the audio, save it to the `cache` directory, and play it back[cite: 2].
4.  **Exit:** Type `quit` or `exit` and press Enter to stop the application[cite: 2].

## Configuration

You can configure the default voice settings by creating a `config.json` file in the root directory of the project[cite: 2].

**Example `config.json`:**

```json
{
  "speaker_id": "EN-FEMALE-1-NEUTRAL",
  "voice_file": null
}