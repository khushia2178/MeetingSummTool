import os
from dotenv import load_dotenv
import openai
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv('.env')

app = Flask(__name__)

UPLOAD_FOLDER = 'input uploads'
SUMMARY_FOLDER = 'meeting summaries'
ALLOWED_EXTENSIONS = {'mp4', 'mp3', 'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SUMMARY_FOLDER'] = SUMMARY_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

openai.api_key = os.getenv('OPENAI_API_KEY')

def authenticate_google_drive():
    credentials, _ = google.auth.load_credentials_from_file(os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH'))
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

# Function to upload file to Google Drive
def upload_file_to_drive(file_path, filename):
    try:
        drive_service = authenticate_google_drive()
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID') # Define drive folder ID 
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/octet-stream')
        
        # Upload the file to Google Drive
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file['webViewLink'] 
    except Exception as e:
        print(f"Error uploading file to Google Drive: {e}")
        return None

def save_summary_to_drive(summary, filename):
    try:
        drive_service = authenticate_google_drive()
        
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        summary_path = os.path.join(app.config['SUMMARY_FOLDER'], f"{filename}_summary.txt")
        with open(summary_path, 'w') as file:
            file.write("=== Meeting Summary ===\n")
            file.write(summary + "\n\n")
            file.write("=== Sentiment Analysis ===\n")
            file.write("Sentiment data...\n")
        
        file_metadata = {
            'name': f"{filename}_summary.txt",
            'parents': [folder_id]
        }
        media = MediaFileUpload(summary_path, mimetype='text/plain')
        
        summary_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return summary_file['webViewLink']
    except Exception as e:
        print(f"Error saving summary to Google Drive: {e}")
        return None
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio(video_path):
    try:
        video = AudioSegment.from_file(video_path, format="mp4")
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_audio.wav')
        video.export(audio_path, format="wav")
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_path):
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript['text']
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def generate_summary(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes meeting recordings."},
                {"role": "user", "content": f"Summarize the following meeting transcript in less than 100 words or 10 bullet points:\n{text}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

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
            file_url = upload_file_to_drive(file_path, filename)
            if not file_url:
                return "Error uploading the file to Google Drive.", 400

            if filename.endswith('.mp4'):
                audio_path = extract_audio(file_path)
                if not audio_path:
                    return "Error extracting audio from the video file.", 400
            else:
                audio_path = file_path

            transcript = transcribe_audio(audio_path)
            if not transcript:
                return "Error transcribing the audio file.", 400

            summary = generate_summary(transcript)
            if not summary:
                return "Error generating the summary.", 400

            summary_url = save_summary_to_drive(summary, filename)
            if not summary_url:
                return "Error saving the summary to Google Drive.", 400

            return render_template('output.html', summary=summary, summary_url=summary_url, file_url=file_url)
    return render_template('input.html')

if __name__ == '_main_':
    app.run(debug=True)