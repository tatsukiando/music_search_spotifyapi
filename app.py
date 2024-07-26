import json
from datetime import datetime
import secrets
from flask import Flask, render_template, request, session, redirect, url_for
from bson.objectid import ObjectId
import redis
import pymongo
from scipy.spatial.distance import cosine

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

def create_mongodb_connection():
    user = 'user'
    pwd = 'password'
    client = pymongo.MongoClient('mongodb://'+user+':'+pwd+'server')
    db = client['cliant']
    return db

def create_redis_connection():
    conn = redis.Redis(host='host', port=portnum, db=dbnum, password='password', charset="utf-8", decode_responses=True)
    return conn

@app.route("/",methods=['GET','POST'])
def index(): #  [1]
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        features = {
            'acousticness': float(request.form['acousticness']),
            'danceability': float(request.form['danceability']),
            'energy': float(request.form['energy']),
            'instrumentalness': float(request.form['instrumentalness']),
            'liveness': float(request.form['liveness']),
            'loudness': float(request.form['loudness']),
            'mode': int(request.form['mode']),
            'speechiness': float(request.form['speechiness']),
            'tempo': float(request.form['tempo']),
            'valence': float(request.form['valence'])
        }
    
        results = calculate_similarity(features,int(request.form['num']))
        return render_template('index.html', results=results)
    return render_template('index.html')

def calculate_similarity(input_features,num):
    db = create_mongodb_connection()
    songs = db.dbname.find()
    similarities = []
    for song in songs:
        
        similarity = 1 - cosine(list(input_features.values()), list(song['features'].values()))
        song['similarity'] = similarity
        similarities.append(song)

    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    show_num=min(60,num)
    return [song['info'] for song in similarities[:show_num]]

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register", methods=["POST"])
def register():
    user_name = request.form['user_name']
    if user_name:
        session['user'] = user_name
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    track_info = {
        'name': request.form['name'],
        'url': request.form['url'],
        'artist': request.form['artist']
    }
    track_info_json = json.dumps(track_info)
    conn = create_redis_connection()
    conn.sadd(session['user']+'playlist', track_info_json)
    return render_template('add.html')

@app.route('/playlist',methods=['GET','POST'])
def show_playlist():
    if request.method == 'POST' and request.form.get('del')=="1":
        info = {
        'name': request.form['name'],
        'url': request.form['url'],
        'artist': request.form['artist']
    }
        info_json = json.dumps(info)
        conn = create_redis_connection()
        playlist_data = conn.srem(session['user']+'playlist',info_json)
        return redirect(url_for('show_playlist'))
    conn = create_redis_connection()
    playlist_data = conn.smembers(session['user']+'playlist')
    tracks = [json.loads(track) for track in playlist_data]
    return render_template('playlist.html', tracks=tracks)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=portnum)
