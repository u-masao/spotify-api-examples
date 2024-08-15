import click
import spotipy
from loguru import logger
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


def get_client_without_auth():
    ccm = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=ccm)
    return sp


def get_client_with_auth():
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            redirect_uri="http://localhost:3000/",
            scope="user-library-read",
        )
    )
    return sp


def search(sp, query: str, limit: int = 20, search_type="track") -> None:
    results = sp.search(q=query, limit=limit, type=search_type)
    return results


def get_current_user_saved_tracks(sp):
    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results["items"]):
        track = item["track"]
        print(idx, track["artists"][0]["name"], " – ", track["name"])
    return results


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
def main(**kwargs):

    sp_visitor = get_client_without_auth()
    sp = get_client_with_auth()

    results = search(sp_visitor, "Jeff Beck", limit=20)
    print(results)
    results = get_current_user_saved_tracks(sp)
    print(results)
    results = search(sp, "Jeff Beck", limit=20)
    print(results)

    favorits = open(kwargs["input_filepath"], "r").read().strip().split("\n")
    print(favorits)
    for query in favorits:
        results = search(sp, query, limit=1, search_type="artist")
        artist_name = results["artists"]["items"][0]["name"]
        artist_id = results["artists"]["items"][0]["id"]

        logger.debug(results)
        logger.info(f"{query=}")
        logger.info(f"{artist_name=}")
        logger.info(f"{artist_id=}")

        related_artists = sp.artist_related_artists(artist_id)
        logger.info(f"{related_artists=}")


if __name__ == "__main__":
    main()
