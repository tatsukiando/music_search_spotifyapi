import pymongo
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import requests
from requests.exceptions import HTTPError
import pandas as pd

def create_mongodb_connection():
    user = 'user'
    pwd = 'password'
    client = pymongo.MongoClient('mongodb://'+user+':'+pwd+'host')
    db = client['cliant']
    return db


client_id = 'client_id'
client_secret = 'client_secret'

# 認証情報を設定
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

playlist_url = 'https://open.spotify.com/playlist/65urlYdgCwciiEhgYMZKkS?go=1&sp_cid=8ff63fef170d1f73db9b002250914fe1&utm_source=embed_player_p&utm_medium=desktop&nd=1&dlsi=b386674e8275424b'
playlist_id = playlist_url.split('/')[-1].split('?')[0]  #プレイリストIDを取得

# プレイリストの楽曲一覧を取得
results = sp.playlist(playlist_id)

tracks = []
artists = []
ids = []
urls = []

for item in results['tracks']['items']:
    track = item['track']
    tracks.append(track['name'])
    ids.append(track['id'])
    urls.append(track['preview_url'])
    artists.append(', '.join([artist['name'] for artist in track['artists']]))

# データフレームを作成
id_2000s = pd.DataFrame({
    'Track': tracks,
    'Artist': artists,
    'ID': ids,
    'preview_url':urls
})

track_list = []

# プレイリストにある100曲分のデータを取得

for i in range(1,60):
    while True:
        try:
            # idをtrack_idに格納して、楽曲データを取得
            track_id = id_2000s['ID'][i]
            track = sp.audio_features(track_id)
            break
        except spotipy.SpotifyException as err:
            # Spotify APIから429エラー（リクエストが多すぎる）が返された場合
            if err.http_status == 429:
                # 再試行までの待機時間を取得（デフォルトは1秒）
                retry_after = int(err.headers.get('Retry-After', 1))
                # 指定された時間だけ待機
                time.sleep(retry_after)

    # 取得した楽曲データをリストに格納
    add={
        'features':{
            'acousticness': float(track[0]['acousticness']),
            'danceability': float(track[0]['danceability']),
            'energy': float(track[0]['energy']),
            'instrumentalness': float(track[0]['instrumentalness']),
            'liveness': float(track[0]['liveness']),
            'loudness': (float(track[0]['loudness'])+100.0)/100.0,
            'mode': float(track[0]['mode']),
            'speechiness': float(track[0]['speechiness']),
            'tempo': 1.0-1.0/float(track[0]['tempo']),
            'valence': float(track[0]['valence'])
            },
        'info':{
            'name': id_2000s['Track'][i],
            'artist': id_2000s['Artist'][i],
            'url':id_2000s['preview_url'][i]
            }
        }
    if add['features']['tempo']>=1:
        print(add)
    if add['info']['url']==None:
        add['info']['url']='None'
    track_list.append(add)
#print(track_list)
#db = create_mongodb_connection()
#result_tmp=db.dbname.insert_many(track_list)
