from flask import Flask, request, jsonify
import os
import openai
import requests
import csv
import zipfile
import io
import pytube
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set")

def extract_text_from_youtube(video_url, start_time=0, end_time=None):
    try:
        video_id = pytube.extract.video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        extracted_text = []
        for entry in transcript:
            if entry['start'] >= start_time and (end_time is None or entry['start'] <= end_time):
                extracted_text.append(entry['text'])
        return " ".join(extracted_text)
    except Exception as e:
        return str(e)

@app.route("/api/", methods=["POST"])
def process_question():
    question = request.form.get("question")
    file = request.files.get("file")
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    # Check if the question contains a YouTube link
    if "youtube.com" in question or "youtu.be" in question:
        video_url = question.split()[-1]  # Assume the last word is the YouTube link
        subtitles = extract_text_from_youtube(video_url)
        return jsonify({"answer": subtitles})
    
    # Handle file uploads (e.g., ZIP, CSV, XLSX)
    if file:
        if file.filename.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(file.read()), 'r') as z:
                for name in z.namelist():
                    if name.endswith(".csv"):
                        with z.open(name) as f:
                            csv_reader = csv.DictReader(io.TextIOWrapper(f))
                            for row in csv_reader:
                                return jsonify({"answer": row.get("answer", "Not found")})
        return jsonify({"error": "Unsupported file format"}), 400
    
    # Default response if no special processing
    return jsonify({"answer": "Processing question: " + question})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
