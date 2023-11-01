# What's in my Playlist?

#### Video Demo: https://www.youtube.com/watch?v=vK6nzOEp3q0&ab_channel=RuslanKireev

#### Description:
This project allows users to curate a playlist based on the 'What's In My Bag?' series from Amoeba's YouTube channel, capturing the most popular track from each guest's pick. The project automates data extraction from YouTube, specifically from the 'What's in My Bag?' playlists, and interfaces with Spotify to generate new playlists based on the artists' selections. This offers an exciting way to explore and curate music by leveraging data from these two popular platforms.

## Files and Functions Overview

### Youtube Part

#### `get_all_playlists(youtube, channel_id)`
- Connects to the YouTube API and fetches all playlists for a given channel ID.
- Filters out playlists based on the title containing "What's".
- Returns a list of playlist information.

#### `get_videos(youtube, playlist_id)`
- Retrieves all videos from a specific YouTube playlist.
- Returns a list of videos.

#### `clean_text(text)`
- Processes and cleans the given text.
- Removes special characters and makes the text lowercase.
- Returns the cleaned text.

#### `get_artists_picks(choosen_artist, unique_videos)`
- Filters out videos based on the chosen artist's name.
- Extracts relevant data (e.g., artist name, album name, album format) from the video descriptions.
- Returns the final list of picks for the chosen artist.

### Spotify Part

#### `get_token()`
- Fetches an authentication token from Spotify for API access.
- Returns the access token.

#### `get_auth_headers(token)`
- Formats the authentication headers needed for Spotify API requests using the given token.
- Returns the formatted headers.

#### `clean_album_name(name)`
- Cleans up the album name by removing non-essential words, phrases, and special characters.
- Returns the cleaned album name.

#### `search_for_album(token, artist_name, album_name)`
- Searches Spotify for a specific album by a given artist.
- Uses fuzzy matching techniques to ensure accurate results even with slight discrepancies.
- Returns a dictionary with the found albums or None if not found.

#### `most_popular_track(token, album_id)`
- Fetches the most popular track from a given album on Spotify.
- Returns the ID of the most popular track.

### Playlist Creation

#### `connect()`
- Establishes a connection to Spotify using the spotipy library.
- Returns the connection object.

#### `create_public_playlist_spotipy(user_id, playlist_name, description)`
- Creates a new public playlist on Spotify using the provided name and description.
- Returns the newly created playlist's ID.

#### `add_tracks_to_playlist(user_id, playlist_id, tracks)`
- Adds a list of tracks to the specified Spotify playlist.
- Returns a success message with the number of tracks added.

### Main Execution

The script concludes with a `main()` execution point, where all the functions integrate to automate the whole process.

## Design Choices and Debated Decisions

### `get_artists_picks(choosen_artist, unique_videos)`

This function is responsible for extracting artist picks from YouTube video descriptions and it works in the following stages:

#### Stage 1: Data Filtering
The function begins by filtering videos where the `choosen_artist` appears in the video title. It does this using the `clean_text` function to normalize text.

#### Stage 2: Text Parsing
Each filtered video's description is split into lines and parsed for artist picks using regular expressions.

#### Stage 3: Regular Expression Matching
A regular expression is used to match artist names, albums, and album formats (e.g., `(LP)`, `(CD)`, `(CASSETTE)`, or dimensions for vinyl). The captured groups from the regular expression provide the artist name, album, and album format for each pick.

### Debated Decision: Use of Regular Expressions
The decision to use regular expressions to identify album markers like `(LP)` or `(CD)` is based on observations from several decades of episodes. While this approach works for the vast majority of cases, it does have limitations. For example, an episode featuring 'Car Seat Headrest' did not include these album format markers, leading to misses in the data extraction.

### Future Considerations
While the function has proven effective, there are instances where it may not work as expected due to variations in video description formats. Future improvements may include additional parsing logic to handle cases where typical album format markers are not present.

### `search_for_album(token, artist_name, album_name)`

This function serves as a sophisticated, multi-stage algorithm for identifying the Spotify album that matches a given `artist_name` and `album_name`. The algorithm is designed to be robust and works in several key stages:

#### Stage 1: Exact Matching
The function starts by searching for an exact match between the supplied `artist_name` and `album_name`. If an exact match is found, the search ends, and the function returns the Spotify ID of the album, along with the artist and album names as they appear on Spotify.

#### Stage 2: Advanced Artist Identification
If an exact match is not found, the function progresses to a more advanced artist identification process. It will attempt to break down the `artist_name` into individual artists—useful for collaborations like "Artist1 & Artist2"—and gather their respective Spotify IDs.

#### Stage 3: Album Retrieval
For each artist ID, the function fetches the list of all albums associated with that artist from Spotify. This list serves as the basis for the next stage of the algorithm.

#### Stage 4: Fuzzy Matching
Utilizing the FuzzyWuzzy library, the function calculates 'fuzz ratios' to measure the similarity between the given `album_name` and those fetched from Spotify. It selects the album with the highest similarity score, provided it exceeds a predetermined threshold.

#### Stage 5: Substring Matching
As a last resort, if no satisfactory fuzz ratio is found, the function employs substring matching to look for possible matches.

#### Stage 6: Handling No Matches
If no matches are found through all these stages, the function returns `None` for that specific `artist_name` and `album_name` pair in the result dictionary.

### Limitations and Future Work
While designed to be as robust as possible, there are occasions where the function may return an incorrect match. The key challenge lies in balancing the strictness of the matching algorithm: too strict, and you risk missing valid matches; too lenient, and you risk false positives. Future work aims to refine this balance for more accurate results.



