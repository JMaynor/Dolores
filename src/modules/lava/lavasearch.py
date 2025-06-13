from typing import Any

from lavalink import AudioTrack


class SearchResultItem:
    def __init__(
        self,
        title: str | None = None,
        author: str | None = None,
        uri: str | None = None,
        artwork_url: str | None = None,
        item_type: str | None = None,
    ) -> None:
        """
        Initialize a SearchResultItem instance.
        """
        self.title = title
        self.author = author
        self.uri = uri
        self.artwork_url = artwork_url
        self.item_type = item_type

    @classmethod
    def from_dict(cls, mapping: dict) -> "SearchResultItem":
        """
        Create a SearchResultItem instance from a dictionary.

        Args:
            mapping (dict): The dictionary containing item data.

        Returns:
            SearchResultItem: The created SearchResultItem instance.
        """
        plugin_info = mapping.get("pluginInfo", {})
        return cls(
            title=mapping.get("info", {}).get("name"),
            author=plugin_info.get("author"),
            uri=plugin_info.get("url"),
            artwork_url=plugin_info.get("artworkUrl"),
            item_type=plugin_info.get("type"),
        )


class LavasearchResult:
    def __init__(
        self,
        raw: Any,
        tracks: list[dict] | None = None,
        albums: list[dict] | None = None,
        artists: list[dict] | None = None,
        playlists: list[dict] | None = None,
        texts: list[str] | None = None,
        plugin: Any | None = None,
    ) -> None:
        """
        Initialize a LavasearchResult instance.
        """
        self.raw = raw
        self.tracks: list[AudioTrack] = [
            AudioTrack.from_dict(raw_track) for raw_track in (tracks or [])
        ]
        self.albums: list[SearchResultItem] = [
            SearchResultItem.from_dict(raw_item) for raw_item in (albums or [])
        ]
        self.artists: list[SearchResultItem] = [
            SearchResultItem.from_dict(raw_item) for raw_item in (artists or [])
        ]
        self.playlists: list[SearchResultItem] = [
            SearchResultItem.from_dict(raw_item) for raw_item in (playlists or [])
        ]
        self.texts: list[str] = texts or []
        self.plugin = plugin

    @classmethod
    def from_dict(cls, mapping: dict) -> "LavasearchResult":
        """
        Create a LavasearchResult instance from a dictionary.

        Args:
            mapping (dict): The dictionary containing search result data.

        Returns:
            LavasearchResult: The created LavasearchResult instance.
        """
        return cls(
            raw=mapping,
            tracks=mapping.get("tracks"),
            albums=mapping.get("albums"),
            artists=mapping.get("artists"),
            playlists=mapping.get("playlists"),
            texts=mapping.get("texts"),
            plugin=mapping.get("plugin"),
        )
