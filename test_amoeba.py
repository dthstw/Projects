from amoeba import clean_album_name, clean_text, get_all_playlists
from unittest.mock import patch, Mock
import datetime
import re
import pytest



def test_clean_text():
    assert clean_text("TEST Text") == "test text"
    assert clean_text("a & b") == "a and b"
    assert clean_text("play/play") == "playplay"
   

def test_clean_album_name():
    assert clean_album_name("Live At CBGB 1982: Remastered") == "Live At CBGB"
    assert clean_album_name("a & b Special Edition") == "a and b"
    
    


def test_get_all_playlists():
    mock_response = {
        "items": [
            {"id": "1", "snippet": {"title": "What's In My Playlist"}},
            {"id": "2", "snippet": {"title": "Test"}},
        ],
        "nextPageToken": None
    }
    
    mock_list = Mock()
    mock_list.execute.return_value = mock_response
    mock_playlists = Mock()
    mock_playlists.list.return_value = mock_list
    mock_youtube = Mock()
    mock_youtube.playlists.return_value = mock_playlists

    with patch('amoeba.youtube', return_value=mock_youtube):
        assert get_all_playlists(mock_youtube, "test_channel_id") == ["1"]
