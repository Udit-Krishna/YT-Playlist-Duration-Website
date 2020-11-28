import os
import re
from googleapiclient.discovery import build
from datetime import timedelta
from flask import Flask, request, render_template


def playlist_length(api_key, playlist_link):

    link_split = playlist_link.split('=')
    playlist_id = link_split[1]

    youtube = build('youtube', 'v3', developerKey=api_key)

    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')

    total_seconds = 0
    nextPageToken = None

    while True:
        playlist_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )

        playlist_response = playlist_request.execute()

        video_ids = []

        for item in playlist_response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        video_request = youtube.videos().list(
            part='contentDetails',
            id=','.join(video_ids)
        )

        video_response = video_request.execute()

        for item in video_response['items']:
            duration = item['contentDetails']['duration']

            hours = hours_pattern.search(duration)
            minutes = minutes_pattern.search(duration)
            seconds = seconds_pattern.search(duration)

            hours = int(hours.group(1)) if hours else 0
            minutes = int(minutes.group(1)) if minutes else 0
            seconds = int(seconds.group(1)) if seconds else 0

            video_seconds = timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds
            ).total_seconds()

            total_seconds += video_seconds

        nextPageToken = playlist_response.get('nextPageToken')

        if not nextPageToken:
            break

    total_seconds = int(total_seconds)

    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return hours, minutes, seconds


api_key = os.environ.get('YT_API_KEY')


app = Flask(__name__, static_url_path='/static')


@app.route('/', methods=['POST', 'GET'])
def send():
    if request.method == 'POST':
        pl_link = request.form['link']

        if pl_link == '':
            return render_template('error.html')

        try:
            hours, minutes, seconds = playlist_length(api_key, pl_link)
            return render_template('result.html', hours=hours, minutes=minutes, seconds=seconds)

        except Exception:
            return render_template('error.html')

    return render_template('main.html')


if __name__ == "__main__":
    app.run()
