class Source:
    playable: bool = False
    search_prefix: str
    source_name: str
    display_name: str


class YouTube(Source):
    playable = True
    search_prefix = "ytsearch:"
    source_name = "youtube"
    display_name = "YouTube"


class SoundCloud(Source):
    playable = True
    search_prefix = "scsearch:"
    source_name = "soundcloud"
    display_name = "SoundCloud"


class YouTubeMusic(Source):
    playable = True
    search_prefix = "ytmsearch:"
    source_name = "youtube"
    display_name = "YouTube Music"


class Deezer(Source):
    playable = True
    search_prefix = "dzsearch:"
    source_name = "deezer"
    display_name = "Deezer"


class Spotify(Source):
    playable = False
    search_prefix = "spsearch:"
    source_name = "spotify"
    display_name = "Spotify"
