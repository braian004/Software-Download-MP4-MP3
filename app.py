# app.py

# from flask import Flask, render_template, request
# from download import get_stream_options, download_video

# app = Flask(__name__)

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     message = ""
#     error = ""
#     options = []
#     video_url = ""
#     if request.method == 'POST':
#         video_url = request.form['video_url']
#         try:
#             if 'selection' in request.form:
#                 selection = int(request.form['selection'])
#                 file_name = download_video(video_url, selection)
#                 message = f"Download successful! File saved as {file_name}"
#             else:
#                 options = get_stream_options(video_url)
#                 message = "Choose a video quality to download"
#         except Exception as e:
#             error = "An error occurred: " + str(e)
#     return render_template('index.html', message=message, error=error, options=options, video_url=video_url)

# if __name__ == '__main__':
#     app.run(debug=True)
from flask import Flask, render_template, request
from download import get_stream_options, run_download_video

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    error = ""
    options = []
    video_url = ""
    if request.method == 'POST':
        video_url = request.form['video_url']
        try:
            if 'selection' in request.form:
                selection = int(request.form['selection'])
                file_name = run_download_video(video_url, selection)
                message = f"Download successful! File saved as {file_name}"
            else:
                options = get_stream_options(video_url)
                message = "Choose a video quality to download"
        except Exception as e:
            error = "An error occurred: " + str(e)
    return render_template('index.html', message=message, error=error, options=options, video_url=video_url)

if __name__ == '__main__':
    app.run(debug=True)
