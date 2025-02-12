# With cloud integration used api for the storage purpose.
# Create a bucket name for when working with GCP or firebase GCP also offers google drive api for using it's storage feature.
# Here we will integrate the same.
# Install some extra libraries like googleouathclient and add path to the .json file.
# Add the folder ID whatever would be the summary and analysis of the meeting would be uploaded to the folder at the same time the execution is completed.
import os
from dotenv import load_dotenv
import openai
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv('.env')

app = Flask(__name__)

# Initalize your folders.
UPLOAD_FOLDER = 'input_uploads'
SUMMARY_FOLDER = 'meeting_summaries'
ALLOWED_EXTENSIONS = {'mp4', 'mp3', 'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SUMMARY_FOLDER'] = SUMMARY_FOLDER

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# Grt the openai API key from the . env file you can also set it manually but in that case don't include the loadenv .
openai.api_key = os.getenv('OPENAI_API_KEY')

# Setup for the storage configration.
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your Google Drive API credentials JSON file

def authenticate_google_drive():
    """Authenticate and return the Google Drive service."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

def upload_to_drive(file_path, folder_id=None):
    """Upload a file to Google Drive."""
    service = authenticate_google_drive()
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id] if folder_id else []
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# Initalize all the important functions.
#  Add the allowed extensions first.
# Extract audio from the video files.
# Pydub will help in this but it has to be configured with ffmpeg for handling the .mp4 files,
def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio(video_path):
    """Extract audio from a video file."""
    try:
        video = AudioSegment.from_file(video_path, format="mp4")
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_audio.wav')
        video.export(audio_path, format="wav")
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None
# Transcribe the audio files uses the whisper model for the same which is provided below.
def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper."""
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript['text']
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None
# The summary should be generated in either 100 words or ten bullet points.
# Below we have initailzed it.
def generate_summary(text):
    """Generate a summary using OpenAI GPT."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes meeting recordings."},
                {"role": "user", "content": f"Summarize the following meeting transcript in less than 100 words or 10 bullet points:\n{text}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None
# The text output should also include the sentiment analysis whether it is positive, negative or neutral.
def analyze_sentiment(text):
    """Analyze sentiment using OpenAI GPT."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes sentiment."},
                {"role": "user", "content": f"Analyze the sentiment of the following text and provide a brief report:\n{text}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return None
# Save the summary so that it hould be accessible in the future.
def save_summary(summary, sentiment, filename):
    """Save the summary and sentiment to a file."""
    try:
        summary_path = os.path.join(app.config['SUMMARY_FOLDER'], f"{filename}_summary.txt")
        with open(summary_path, 'w') as file:
            file.write("=== Meeting Summary ===\n")
            file.write(summary + "\n\n")
            file.write("=== Sentiment Analysis ===\n")
            file.write(sentiment + "\n")
        return summary_path
    except Exception as e:
        print(f"Error saving summary: {e}")
        return None

# Intialize the flask routes.
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Get Google Drive folder ID from the form
            drive_folder_id = request.form.get('drive_folder_id')

            # Upload the file to Google Drive (if folder ID is provided)
            if drive_folder_id:
                file_id = upload_to_drive(file_path, drive_folder_id)
                print(f"File uploaded to Google Drive with ID: {file_id}")

            # Extract audio if the file is a video
            if filename.endswith('.mp4'):
                audio_path = extract_audio(file_path)
                if not audio_path:
                    return "Error extracting audio from the video file.", 400
            else:
                audio_path = file_path

            # Transcribe audio
            transcript = transcribe_audio(audio_path)
            if not transcript:
                return "Error transcribing the audio file.", 400

            # Generate summary
            summary = generate_summary(transcript)
            if not summary:
                return "Error generating the summary.", 400

            # Analyze sentiment
            sentiment = analyze_sentiment(transcript)
            if not sentiment:
                return "Error analyzing sentiment.", 400

            # Save summary and sentiment
            summary_path = save_summary(summary, sentiment, filename)
            if not summary_path:
                return "Error saving the summary.", 400

            # Upload the summary file to Google Drive (if folder ID is provided)
            if drive_folder_id:
                summary_file_id = upload_to_drive(summary_path, drive_folder_id)
                print(f"Summary file uploaded to Google Drive with ID: {summary_file_id}")

            # Render the merged HTML template with results
            return render_template('index.html', summary=summary, sentiment=sentiment, show_results=True)

    # Render the merged HTML template without results
    return render_template('index.html', show_results=False)

if __name__ == '_main_':
    # Initalizing the port and the host is optional you can also provide the loal host in this case.
    app.run(debug=True, host='0.0.1', port='5500')

