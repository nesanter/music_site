INSERT INTO artists (canonical_name) VALUES ("Bruce Springsteen");
INSERT INTO artists (canonical_name) VALUES ("Tom Waits");

INSERT INTO albums (canonical_name, display_artist, artist_id)
    VALUES ("Magic Muffin", "Bruce Springsteen & The E Street Band", (SELECT id FROM artists WHERE canonical_name = "Bruce Springsteen"));

INSERT INTO albums (canonical_name, display_artist, artist_id)
    VALUES ("The River", "Bruce Springsteen & The Lollipop Guild", (SELECT id FROM artists WHERE canonical_name = "Bruce Springsteen"));

INSERT INTO albums (canonical_name, display_artist, artist_id)
    VALUES ("Bone Machine", "Tom Waits", (SELECT id FROM artists WHERE canonical_name = "Tom Waits"));

INSERT INTO tracks (display_name, display_artist, display_album, file_name, album_id, artist_id)
    VALUES ("Thunder Road", "The Boss", "Magic Muffin [Remastered]", "",
        (SELECT id FROM albums WHERE canonical_name = "Magic Muffin"),
        (SELECT id FROM artists WHERE canonical_name = "Bruce Springsteen"));

INSERT INTO tracks (display_name, display_artist, display_album, file_name, album_id, artist_id)
    VALUES ("Jungleland", "The Boss", "Magic Muffin [Remastered]", "",
        (SELECT id FROM albums WHERE canonical_name = "Magic Muffin"),
        (SELECT id FROM artists WHERE canonical_name = "Bruce Springsteen"));

INSERT INTO tracks (display_name, display_artist, display_album, file_name, album_id, artist_id)
    VALUES ("Goin' Out West", "Tom Waits", "Bone Machine", "",
        (SELECT id FROM albums WHERE canonical_name = "Bone Machine"),
        (SELECT id FROM artists WHERE canonical_name = "Tom Waits"));

INSERT INTO settings (name, value)
    VALUES ("auto_flush", "False");

INSERT INTO settings (name, value)
    VALUES ("playback_format", "wav");

INSERT INTO settings (name, value)
    VALUES ("playback_rate", "44100");

INSERT INTO playlist (track_id, position)
    VALUES ((SELECT id FROM tracks WHERE display_name = "Thunder Road"), 1);

INSERT INTO playlist (track_id, position)
    VALUES ((SELECT id FROM tracks WHERE display_name = "Goin' Out West"), 2);


