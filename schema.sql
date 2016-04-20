DROP TABLE IF EXISTS tracks;
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT,
    display_artist TEXT,
    display_album TEXT,
    filename TEXT,
    filetype TEXT,
    album_id INTEGER,
    artist_id INTEGER,
    FOREIGN KEY(album_id) REFERENCES albums(id),
    FOREIGN KEY(artist_id) REFERENCES artists(id)
);

DROP TABLE IF EXISTS albums;
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT,
    display_artist TEXT,
    artist_id INTEGER,
    FOREIGN KEY(artist_id) REFERENCES artists(id)
);

DROP TABLE IF EXISTS artists;
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL
);

DROP TABLE IF EXISTS track_orders;
CREATE TABLE track_orders (
    track_id INTEGER,
    album_id INTEGER,
    position INTEGER,
    FOREIGN KEY (track_id) REFERENCES tracks (id),
    FOREIGN KEY (album_id) REFERENCES albums (id)
);

DROP TABLE IF EXISTS playlist;
CREATE TABLE playlist (
    track_id INTEGER,
    position INTEGER,
    FOREIGN KEY (track_id) REFERENCES tracks (id)
);

DROP TABLE IF EXISTS settings;
CREATE TABLE settings (
    name TEXT,
    value TEXT
);




