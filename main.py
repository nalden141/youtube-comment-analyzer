import streamlit as st
import requests
import re
from PIL import Image
from io import BytesIO
from transformers import pipeline
import pickle
import googleapiclient.discovery

with open('distilbert-base-uncased-finetuned-sst-2-english.pkl', 'rb') as f:
    classifier = pickle.load(f)

if 'all_comments' not in st.session_state:
    st.session_state['all_comments'] = []

st.title('YouTube Comments Analyzer')

st.write("""
    Welcome to the YouTube Comments Analyzer! This app allows you to analyze the sentiment of comments
    from a YouTube video. To get started, please follow these steps:

    1. **Obtain a YouTube Data API Key**: 
        - Create a Google account if you don't have one already.

        - Go to the Google Cloud Console: https://console.cloud.google.com/

        - You might need to agree to terms and conditions.

        - If this is your first time using the Console, create a new project by clicking "Create project". Give your project a descriptive name.

        - From the project dashboard, navigate to "APIs & Services" then "Library".

        - Search for "YouTube Data API v3" and select it. Click "Enable" to activate the API for your project.

        - Once enabled, go to "Credentials" then "Create Credentials" and select "API key".

        - Your API key will be displayed. Copy it and keep it secure, as anyone with this key can access the YouTube Data API through your project.
    2. **Enter Your API Key**:
        - Once you have your API key, enter it in the text box below.

    3. **Enter YouTube Video URL**:
        - Paste the URL of the YouTube video whose comments you want to analyze in the text box below.

    4. **Select Sorting Option**:
        - You can choose to sort comments by sentiment (positive or negative) using the dropdown box.

    5. **Analyze Comments**:
        - Click on the "Analyze Comments" button to fetch and analyze comments from the provided video URL.

    """)

api_key = st.text_input('Enter your YouTube Data API Key', value='', type='password')
video_url = st.text_input('Enter YouTube video URL')

# Function to fetch video thumbnail URL
def get_video_thumbnail_url(video_id):
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        return thumbnail_url
    else:
        # If maxresdefault.jpg is not available, use another thumbnail
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

# Add select box for sorting
sort_option = st.selectbox("Sort Comments by Sentiment:", ["None", "Positive", "Negative"])

# Function to fetch comments from YouTube video
def fetch_youtube_comments(video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()
    comments = []
    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)
    return comments

def get_video_id(video_url):
    # Extract video ID from YouTube URL
    match = re.search(r"v=([a-zA-Z0-9-_]+)", video_url)
    if match:
        return match.group(1)
    else:
        return None

def classify_comment(classifier, comment):
    result = classifier(comment)[0]['label']
    return result
def display_comments(comments):
    total_comments = len(comments)
    positive_comments = sum(1 for c in comments if c['classification'] == 'POSITIVE')
    negative_comments = sum(1 for c in comments if c['classification'] == 'NEGATIVE')
    st.write(f"Total Comments: {total_comments}")
    st.write(f"Positive Comments: {positive_comments} ({(positive_comments/total_comments)*100:.2f}%)")
    st.write(f"Negative Comments: {negative_comments} ({(negative_comments/total_comments)*100:.2f}%)")

    for idx, comment in enumerate(comments):
        st.write(f"Comment {idx+1}: {comment['comment']}")
        st.write(f"Classification: {comment['classification']}")


if st.button("Analyze Comments"):
    video_id = get_video_id(video_url)
    if video_id:
        # Display video thumbnail
        thumbnail_url = get_video_thumbnail_url(video_id)
        st.image(thumbnail_url, caption='YouTube Video Thumbnail', use_column_width=True)

        comments = fetch_youtube_comments(video_id)
        for comment in comments:
            comment_dic = {'comment': comment, 'classification': classify_comment(classifier, comment)}
            st.session_state['all_comments'].append(comment_dic)

        # Filter comments based on selected option
        filtered_comments = st.session_state['all_comments']
        if sort_option == "Positive":
            filtered_comments = [c for c in filtered_comments if c['classification'] == 'POSITIVE']
        elif sort_option == "Negative":
            filtered_comments = [c for c in filtered_comments if c['classification'] == 'NEGATIVE']

        display_comments(filtered_comments)
    else:
        st.error("Invalid YouTube video URL. Please enter a valid URL.")
