import time
import speech_recognition as sr
from transformers import pipeline

# Initialize the ASR pipeline (using Facebook's Wav2Vec2 model)
asr_pipeline = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-large-960h")

# Initialize a text generation pipeline (using GPT-2 as an example) for answering questions
text_generator = pipeline("text-generation", model="gpt2")

# Set up the speech recognizer and microphone input
recognizer = sr.Recognizer()
mic = sr.Microphone()

def process_command(command_text):
    """
    Process the recognized command text:
    - If it ends with a '?', assume it's a question and generate an answer.
    - Otherwise, check for specific command keywords.
    """
    if command_text.strip().endswith('?'):
        print("Detected question. Generating answer...")
        # Generate an answer (this is a demo; for more complex queries, consider using a dedicated Q&A model)
        response = text_generator("Question: " + command_text + " Answer:", max_length=50)
        answer = response[0]['generated_text']
        print("Answer:", answer)
    else:
        # Check for specific commands (customize these keywords as needed)
        lower_text = command_text.lower()
        if "change environment" in lower_text:
            print("Executing command: Changing environment!")
            # Insert code here to modify your 3D environment
        elif "play video" in lower_text:
            print("Executing command: Playing video!")
            # Insert code here to control video/MP4 playback
        else:
            print("Command not recognized. Please try again.")

def callback(recognizer, audio):
    """
    This callback is executed in the background each time audio is detected.
    """
    try:
        # Get the audio data and save it to a temporary file
        audio_data = audio.get_wav_data()
        with open("temp.wav", "wb") as f:
            f.write(audio_data)
        
        # Use the ASR pipeline to convert audio to text 
        result = asr_pipeline("temp.wav")
        command_text = result["text"]
        print("Recognized:", command_text)
        
        # Process the recognized command
        process_command(command_text)
    except Exception as e:
        print("Error processing command:", str(e))

print("Calibrating microphone for ambient noise...")
with mic as source:
    recognizer.adjust_for_ambient_noise(source)
    print("Listening for commands continuously...")

# Start background listening. This returns a function that, when called, will stop the background listening.
stop_listening = recognizer.listen_in_background(mic, callback)

# Keep the program running indefinitely.
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    stop_listening()
    print("Stopped listening.")
