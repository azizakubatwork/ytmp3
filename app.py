from flask import Flask, render_template, request, redirect, url_for
from pydub import AudioSegment
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import yt_dlp
import requests
from urllib.parse import urlparse, parse_qs

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

def extract_video_id(url):
    query = urlparse(url)
    video_id = None

    if query.hostname == 'youtu.be':
        video_id = query.path[1:]
    elif query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if query.path == '/watch':
            video_id = parse_qs(query.query).get('v', [None])[0]
        elif query.path[:7] == '/embed/':
            video_id = query.path.split('/')[2]
        elif query.path[:3] == '/v/':
            video_id = query.path.split('/')[2]

    return video_id

def get_session_cookies():
    email = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")

    # Your code to obtain session cookies using requests
    # Example (for educational purposes, not a complete solution):
    login_url = "https://accounts.google.com/ServiceLogin/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin"
    login_data = {"email": email, "password": password, "continue": "https://www.youtube.com/"}
    session = requests.Session()
    session.post(login_url, data=login_data)

    return session.cookies.get_dict()

def is_age_restricted(yt_html):
    return 'age-restricted' in yt_html

def download_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path + '.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/')
def index():
    return render_template('index_file.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_content = uploaded_file.read().decode('utf-8')
            soup = BeautifulSoup(file_content, 'html.parser')
            youtube_links = [a.get('href') for a in soup.find_all('a') if a.get('href') and 'youtube.com' in a['href']]

            # Obtain session cookies
            cookies = get_session_cookies()

            for link in youtube_links:
                try:
                    video_id = extract_video_id(link)
                    if video_id:
                        yt_url = f'https://www.youtube.com/watch?v={video_id}'
                        
                        # Download the webpage with cookies
                        response = requests.get(yt_url, cookies=cookies)
                        yt_html = response.text

                        if not is_age_restricted(yt_html):
                            output_path = f'downloads/{video_id}'
                            download_audio(yt_url, output_path)
                except Exception as e:
                    print(f"An error occurred for link {link}: {str(e)}")

            return redirect(url_for('index'))
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
