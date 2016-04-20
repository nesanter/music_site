
# music.py : music site Flask app
# music_site copyright (C) 2016 Noah Santer (santerkrupp@gmail.com)
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, stream_with_context
from contextlib import closing

import math, subprocess, re, os, itertools

DATABASE = '/tmp/music.db'
DEBUG = True
SECRET_KEY = 'devkey'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def init_db(load_td=False):
    with closing(connect_db()) as db:
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        if load_td:
            with app.open_resource("test-data.sql", mode="r") as f:
                db.cursor().executescript(f.read())
        db.commit()

def gen_lots():
    for i in range(1000):
        pd = parse_track_path('null-' + str(i), 'null-' + str(i) + '-' +str(i), 'null-0-' + str(i) + '-' + str(i) + '-' + str(i) + '.wav')
        update_db(pd)

def connect_db():
    return sqlite3.connect(app.config["DATABASE"])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def get_playlist():
    cur = g.db.execute('SELECT position, display_name, display_artist, display_album, id, album_id, artist_id FROM playlist INNER JOIN tracks ON track_id = tracks.id ORDER BY position ASC')
    return [dict(position=row[0], title=row[1], artist=row[2], album=row[3], track_id=row[4], album_id=row[5], artist_id=row[6]) for row in cur.fetchall()]

@app.route('/')
def show_home():
    return render_template('home.html', playlist=get_playlist())


@app.route('/search/<category>', methods=['POST'])
def search(category):
    pattern = request.form['search']
    track_matches = []
    if (category == 'track' or category == 'all'):
        cur = g.db.execute('SELECT id, display_name, display_artist, display_album, artist_id, album_id FROM tracks')
        for row in cur.fetchall():
            if re.search(pattern, row[1], flags=re.I) is not None or \
                    re.search(pattern, row[2], flags=re.I) is not None or \
                    re.search(pattern, row[3], flags=re.I) is not None:
                track_matches += [dict(track_id=row[0], name=row[1], display_artist=row[2], display_album=row[3], artist_id=row[4], album_id=row[5])]

    album_matches = []
    if (category == 'album' or category == 'all'):
        cur = g.db.execute('SELECT id, canonical_name, display_artist, artist_id FROM albums')
        for row in cur.fetchall():
            if re.search(pattern, row[1], flags=re.I) is not None or \
                    re.search(pattern, row[2], flags=re.I) is not None:
                album_matches += [dict(album_id=row[0], name=row[1], display_artist=row[2], artist_id=row[3])]

    artist_matches = []
    if (category == 'artist' or category == 'all'):
        cur = g.db.execute('SELECT id, canonical_name FROM artists')
        for row in cur.fetchall():
            if re.search(pattern, row[1], flags=re.I) is not None:
                artist_matches += [dict(artist_id=row[0], name=row[1])]

    return render_template('search_results.html', category=category, track_matches=track_matches, album_matches=album_matches, artist_matches=artist_matches)

@app.route('/artists/')
def show_artists():
    cur = g.db.execute('SELECT artists.id, artists.canonical_name, COUNT(albums.id) FROM artists INNER JOIN albums ON albums.artist_id = artists.id GROUP BY artists.id')
    entries = [dict(artist_id=row[0], name=row[1], n_albums=row[2]) for row in cur.fetchall()]
    
    return render_template('show_artists.html', playlist=get_playlist(), artists=entries)

@app.route('/albums/')
def show_albums():
    cur = g.db.execute('SELECT albums.id, albums.canonical_name, albums.artist_id, albums.display_artist, COUNT(tracks.id) FROM albums INNER JOIN tracks ON albums.id = tracks.album_id GROUP BY albums.id')
    entries = [dict(album_id=row[0], name=row[1], artist_id=row[2], display_artist=row[3], n_tracks=row[4]) for row in cur.fetchall()]

    return render_template('show_albums.html', playlist=get_playlist(), albums=entries)

@app.route('/tracks/from/<offset>')
def show_tracks(offset):
    cur = g.db.execute('SELECT id, display_name, display_artist, display_album, artist_id, album_id FROM tracks LIMIT 50 OFFSET (? - 1)', [offset])
    entries = [dict(track_id=row[0], name=row[1], display_artist=row[2], display_album=row[3], artist_id=row[4], album_id=row[5]) for row in cur.fetchall()]

    return render_template('show_tracks.html', playlist=get_playlist(), tracks=entries, next_offset=int(offset) + 50)

@app.route('/artists/<artist_id>')
def show_artist(artist_id):
    cur = g.db.execute('SELECT canonical_name FROM artists WHERE id = ?', [artist_id])
    names = [row[0] for row in cur.fetchall()]

    if len(names) != 1:
        return render_template('error.html', playlist=[])

    cur = g.db.execute('SELECT id, canonical_name, display_artist FROM albums WHERE artist_id = ?', [artist_id])
    albums = [dict(album_id=row[0], name=row[1], display_artist=row[2]) for row in cur.fetchall()]

    cur = g.db.execute('SELECT id, display_name, album_id FROM tracks WHERE artist_id = ?', [artist_id])
    tracks = [dict(track_id=row[0], name=row[1], album_id=row[2]) for row in cur.fetchall()]

    return render_template('show_artist.html', playlist=get_playlist(), artist_id=artist_id, name=names[0], albums=albums, tracks=tracks)

@app.route('/albums/<album_id>')
def show_album(album_id):
    cur = g.db.execute('SELECT canonical_name, display_artist, artist_id FROM albums WHERE id = ?', [album_id])
    info = [dict(name=row[0], display_artist=row[1], artist_id=row[2]) for row in cur.fetchall()]
    
    if len(info) != 1:
        return render_template('error.html', playlist=[])

    cur = g.db.execute('SELECT id, display_name, display_album, display_artist FROM tracks WHERE album_id = ?', [album_id])
    tracks = [dict(track_id=row[0], display_name=row[1], display_album=row[2], display_artist=row[3]) for row in cur.fetchall()]

    return render_template('show_album.html', playlist=get_playlist(), album_id=album_id, name=info[0]['name'], display_artist=info[0]['display_artist'], artist_id=info[0]['artist_id'], tracks=tracks)

@app.route('/tracks/<track_id>')
def show_track(track_id):
    cur = g.db.execute('SELECT display_name, display_artist, display_album, artist_id, album_id FROM tracks WHERE id = ?', [track_id])
    info = [dict(name=row[0], display_artist=row[1], display_album=row[2], artist_id=row[3], album_id=row[4]) for row in cur.fetchall()]
    
    if len(info) != 1:
        return render_template('error.html', playlist=[])

    return render_template('show_track.html', playlist=get_playlist(), track_id=track_id, album_id=info[0]['album_id'], artist_id=info[0]['artist_id'], name=info[0]['name'], display_artist=info[0]['display_artist'], display_album=info[0]['display_album'])

@app.route('/stream/')
def stream_playlist():
    return redirect(url_for('stream_playlist_from', start=1))

@app.route('/stream/<start>')
def stream_playlist_from(start):
    def gen():
        cur = g.db.execute('SELECT track_id, filename, filetype FROM playlist INNER JOIN tracks ON tracks.id = track_id WHERE position >= ? ORDER BY position ASC', [start])
        playlist = [dict(track_id=row[0], filename=row[1], filetype=row[2]) for row in cur.fetchall()]

        fmt = 'wav'

        for tr in playlist:
            if tr['filetype'] == 'wav':
                # stream directly
                with app.open_resource(tr['filename'], 'rb') as f:
                    yield from f
            else:
                # use ffmpeg
                with subprocess.Popen(['ffmpeg', '-i', tr['filename'], '-ar', '44100', '-f', fmt, '-'], stdout=subprocess.PIPE) as p:
                    yield from p.stdout
                f = 's16le'
#        with open("/home/noah/voice-sample-8k.wav", mode='rb') as f:
#            yield from f
#        yield url_for('show_home')
#        with subprocess.Popen(['ffmpeg', '-i', '/home/noah/back-then.mp3', '-f', 'wav', '-'], stdout=subprocess.PIPE) as p:
#            yield from p.stdout


    return Response(stream_with_context(gen()), mimetype='audio/wav')

@app.route('/add/track/<track_id>')
def add_playlist(track_id):
    g.db.execute('INSERT INTO playlist (track_id, position) VALUES (?, (SELECT COUNT(track_id) FROM playlist) + 1)', [track_id])
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/add/album/<album_id>')
def add_album_playlist(album_id):
    cur = g.db.execute('SELECT id FROM tracks WHERE album_id = ?', [album_id])
    for track_id in [row[0] for row in cur.fetchall()]:
        g.db.execute('INSERT INTO playlist (track_id, position) VALUES (?, (SELECT COUNT(track_id) FROM playlist) + 1)', [track_id])
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/add/artist/<artist_id>')
def add_artist_playlist(artist_id):
    cur = g.db.execute('SELECT id FROM tracks WHERE artist_id = ?', [artist_id])
    for track_id in [row[0] for row in cur.fetchall()]:
        g.db.execute('INSERT INTO playlist (track_id, position) VALUES (?, (SELECT COUNT(track_id) FROM playlist) + 1)', [track_id])
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/raise/<position>')
def raise_playlist(position):
    if int(position) <= 1:
        return redirect(request.referrer or url_for('show_home'))

    g.db.execute('UPDATE playlist SET position = -4 WHERE position = ?',
        [position])
    g.db.execute('UPDATE playlist SET position = position + 1 WHERE position = ? - 1',
        [position])
    g.db.execute('UPDATE playlist SET position = ? - 1 WHERE position = -4',
        [position])

    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/top/<position>')
def top_playlist(position):
    g.db.execute('UPDATE playlist SET position = 0 WHERE position = ?',
            [position])
    g.db.execute('UPDATE playlist SET position = position + 1')
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/flush')
def flush_playlist():
    g.db.execute('DELETE FROM playlist')
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/remove/<position>')
def remove_playlist(position):
    g.db.execute('DELETE FROM playlist WHERE position = ?', [position])
    g.db.execute('UPDATE playlist SET position = position - 1 WHERE position > ?', [position])
    g.db.commit()
    return redirect(request.referrer or url_for('show_home'))

@app.route('/modify')
def modify_database():
    return render_template('modify_database.html')

@app.route('/modify/submit', methods=['POST'])
def modify_database_submit():

    s = request.form['modify'].split('\n')
    print(s)
    errors = False
    for ar, al, tr in itertools.zip_longest(*[iter(s)] * 3, fillvalue=''):
        if al == '' or tr == '':
            continue
        pd = parse_track_path(ar.strip(), al.strip(), tr.strip())
        if pd == False:
            errors = True
            continue
        update_db(pd)

    if errors:
        return render_template('error.html')

    return redirect(url_for('modify_database'))

# directory structure:
# /artist_id-canonical_name
#   /album_id-canonical_name-[display_artist]
#     /track_id-[disc_num:]track_num-display_name-[display_album]-[display_artist].extension

def renull_files(basedir):
    updates = []
    for de in os.scandir(basedir):
        if de.is_dir():
            ar_dir = de.name
            for de2 in os.scandir(de.path):
                if de2.is_dir():
                    al_dir = de2.name
                    for de3 in os.scandir(de2.path):
                        if de3.is_file():
                            tr_file = de3.name
                            pd = parse_track_path(ar_dir, al_dir, tr_file)
                            if pd is False:
                                print("failed to parse", ar_dir, al_dir, tr_file)
                            else:
                                pd['ar_id'] = 'null'
                                pd['al_id'] = 'null'
                                pd['tr_id'] = 'null'

                                arn, aln, trn = expand_parsed(pd)

                                if trn != tr_file:
                                    updates += [(os.path.join(basedir, ar_dir, al_dir, tr_file), os.path.join(basedir, ar_dir, al_dir, trn))]
                                    tr_file = trn

                                if aln != al_dir:
                                    updates += [(os.path.join(basedir, ar_dir, al_dir), os.path.join(basedir, ar_dir, aln))]
                                    al_dir = aln

                                if arn != ar_dir:
                                    updates += [(os.path.join(basedir, ar_dir), os.path.join(basedir, arn))]
                                    ar_dir = arn

    for old, new in updates:
        print(old, '->', new)
        os.rename(old, new)


def update_from_files(basedir):
    updates = []
    for de in os.scandir(basedir):
        if de.is_dir():
            ar_dir = de.name
            for de2 in os.scandir(de.path):
                if de2.is_dir():
                    al_dir = de2.name
                    for de3 in os.scandir(de2.path):
                        if de3.is_file():
                            tr_file = de3.name
                            pd = parse_track_path(ar_dir, al_dir, tr_file)
                            if pd is False:
                                print("failed to parse", ar_dir, al_dir, tr_file)
                            else:
                                arid, alid, trid = update_db(pd, basedir)
                                print(arid, alid, trid)
                                pd['ar_id'] = arid
                                pd['al_id'] = alid
                                pd['tr_id'] = trid

                                arn, aln, trn = expand_parsed(pd)

                                if trn != tr_file:
                                    updates += [(os.path.join(basedir, ar_dir, al_dir, tr_file), os.path.join(basedir, ar_dir, al_dir, trn))]
                                    tr_file = trn

                                if aln != al_dir:
                                    updates += [(os.path.join(basedir, ar_dir, al_dir), os.path.join(basedir, ar_dir, aln))]
                                    al_dir = aln

                                if arn != ar_dir:
                                    updates += [(os.path.join(basedir, ar_dir), os.path.join(basedir, arn))]
                                    ar_dir = arn

    for old, new in updates:
        print(old, '->', new)
        os.rename(old, new)

def expand_parsed(parsed):
    artist = str(parsed['ar_id']) + '-' + parsed['ar_can_name']
    album = str(parsed['al_id']) + '-' + parsed['al_can_name'] + '-' + parsed['al_disp_ar']
    track = str(parsed['tr_id']) + '-' + parsed['tr_num'] + '-' + parsed['tr_can_name'] + '-' + parsed['tr_disp_al'] + '-' + parsed['tr_disp_ar'] + '.' + parsed['tr_ext']

    return artist, album, track

def parse_track_path(artist_name, album_name, track_name):

    artist = re.split('([0-9]+|null)-(.*)', artist_name)
    if len(artist) == 1:
        return False

    _, ar_id, ar_can_name, _ = artist

    album = re.split('([0-9]+|null)-(.*)-(.*)', album_name)
    if len(album) == 1:
        return False

    _, al_id, al_can_name, al_disp_ar, _ = album

    track = re.split('([0-9]+|null)-([0-9:]+)-(.*)-(.*)-(.*)\.(.*)', track_name)
    if len(track) == 1:
        return False

    _, tr_id, tr_num, tr_can_name, tr_disp_al, tr_disp_ar, tr_ext, _ = track

    return dict(
            ar_id=ar_id,
            ar_can_name=ar_can_name,
            al_id=al_id,
            al_can_name=al_can_name,
            al_disp_ar=al_disp_ar,
            tr_id=tr_id,
            tr_num=tr_num,
            tr_can_name=tr_can_name,
            tr_disp_al=tr_disp_al,
            tr_disp_ar=tr_disp_ar,
            tr_ext=tr_ext
        )

def update_db(parsed, basedir=''):
    with closing(connect_db()) as db:
        if parsed['ar_id'] == 'null':
            db.execute('INSERT INTO artists (canonical_name) VALUES (?)', [parsed['ar_can_name']])
            cur = db.execute('SELECT LAST_INSERT_ROWID()')
            ar_id = [row[0] for row in cur.fetchall()][0]
        else:
            db.execute('INSERT OR REPLACE INTO artists (id, canonical_name) VALUES (?, ?)', [parsed['ar_id'], parsed['ar_can_name']])
            ar_id = parsed['ar_id']

        if parsed['al_id'] == 'null':
            db.execute('INSERT INTO albums (canonical_name, display_artist, artist_id) VALUES (?, ?, ?)', 
                    [parsed['al_can_name'], parsed['al_disp_ar'], ar_id])
            cur = db.execute('SELECT LAST_INSERT_ROWID()')
            al_id = [row[0] for row in cur.fetchall()][0]
        else:
            db.execute('INSERT OR REPLACE INTO albums (id, canonical_name, display_artist, artist_id) VALUES (?, ?, ?, ?)', 
                    [parsed['al_id'], parsed['al_can_name'], parsed['al_disp_ar'], ar_id])
            al_id = parsed['al_id']

        if parsed['tr_id'] == 'null':
            db.execute('INSERT INTO tracks (display_name, display_artist, display_album, album_id, artist_id, filetype) VALUES (?, ?, ?, ?, ?, ?)',
                    [parsed['tr_can_name'], parsed['tr_disp_ar'], parsed['tr_disp_al'], al_id, ar_id, parsed['tr_ext']])
            cur = db.execute('SELECT LAST_INSERT_ROWID()')
            tr_id = [row[0] for row in cur.fetchall()][0]
            parsed['tr_id'] = tr_id
        else:
            db.execute('INSERT OR REPLACE INTO tracks (id, display_name, display_artist, display_album, album_id, artist_id, filetype) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    [parsed['tr_id'], parsed['tr_can_name'], parsed['tr_disp_ar'], parsed['tr_disp_al'], al_id, ar_id, parsed['tr_ext']])
            tr_id = parsed['tr_id']

        fname = os.path.join(basedir, *expand_parsed(parsed))

        db.execute('UPDATE tracks SET filename = ? WHERE id = ?', [fname, parsed['tr_id']])



        db.commit()
        return (ar_id, al_id, tr_id)

if __name__ == "__main__":
    app.run()
