# MeetingSummTool
This project is a Flask-based web application for transcribing, summarizing, and analyzing sentiment in meeting recordings. The app supports uploading audio and video files, extracting audio from videos, and storing files and summaries on Google Drive.

# Features

1.Audio/Video Upload: Supports MP4, MP3, and WAV files.
2.Audio Extraction: Extracts audio from video files (MP4 format).
3.Transcription: Uses OpenAI's Whisper API to transcribe audio into text.
4.Summarization: Generates a concise summary of the meeting transcript using GPT-4.
5.Sentiment Analysis: Analyzes the sentiment of the meeting and provides a report.
6.Google Drive Storage: Uploads meeting files and summaries to Google Drive.
7.Simple Web Interface: Upload files and view summaries directly in the browser.
# Prerequisites

Make sure you have the following installed:

1.Python 3.7+
2.Flask: For creating the web application.
3.OpenAI API Key: For transcription and summarization using GPT models.
4.Google Drive API Setup: To store files in Google Drive.
# Google Drive Setup
1.Create a Google Cloud Project: Go to Google Cloud Console and create a new project.
2.Enable Google Drive API: In the Google Cloud Console, navigate to the "API & Services" section and enable the Google Drive API for your project.
3.Create a Service Account:
4.Go to "IAM & Admin" > "Service Accounts".
5.Create a service account, download the JSON credentials file, and store it securely.
6.Create a Google Drive Folder: Create a folder in Google Drive where the uploaded files and summaries will be stored. Get the folder ID from the URL when the folder is opened 
# Next Steps 
1. Create a .env file and include the following credentials in it
OPENAI_API_KEY=your_openai_api_key
GOOGLE_DRIVE_CREDENTIALS_PATH=path_to_your_google_drive_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
# Install libraries
Go to the terminal and install all the required libraries
pip install openai pydub flask werkzeug python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
# Start the Flask App:
Run the python code to start the flask server
# Access the Web App:
Open your browser and go to http://127.0.0.1:5000/. You’ll see the file upload interface.(Default for the flask applcations)
# Upload Files:
Click on "Choose File" to upload a meeting recording . The app supports MP4, MP3, and WAV formats.
# Processing:
After you upload the file, the app will:

1.Extract audio from video files (if necessary).
2.Transcribe the audio using OpenAI's Whisper API.
3.Summarize the transcript using GPT-4.
4.Perform sentiment analysis on the transcript.
5.Upload both the audio file and summary to Google Drive.
# View the Summary:
After processing, the app will display the summary and sentiment analysis. You will also receive a link to access or download the files from Google Drive.
# Accessing Files from Google Drive:
The uploaded audio and summary files are saved in Google Drive. Links to the uploaded files are provided after processing.
# Google Drive Integration

The application uses the Google Drive API to upload files and summaries to a specified folder in Google Drive. The following steps are performed when a file is uploaded:

1.The audio or video file is uploaded to Google Drive.
2.The generated summary file is saved to Google Drive as a .txt file.
3.Public URLs to the files are generated and displayed to the user.
4.The folder ID where files will be uploaded can be specified in the .env file under GOOGLE_DRIVE_FOLDER_ID.

# Google Drive Authentication
The app uses service account credentials stored in the GOOGLE_DRIVE_CREDENTIALS_PATH (provided in the .env file) to authenticate requests to Google Drive.
Make sure the service account has the correct permissions to upload files to the specified folder.
