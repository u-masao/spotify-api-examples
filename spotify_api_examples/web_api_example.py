import spotipy
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


def search_tracks(sp, query: str, limit: int = 20) -> None:
    results = sp.search(q=query, limit=limit)
    for idx, track in enumerate(results["tracks"]["items"]):
        print(idx, track["name"])
    return results


def get_current_user_saved_tracks(sp):
    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results["items"]):
        track = item["track"]
        print(idx, track["artists"][0]["name"], " – ", track["name"])
    return results


def main():
    sp_visitor = get_client_without_auth()
    sp = get_client_with_auth()
    results = search_tracks(sp_visitor, "Jeff Beck", limit=20)
    print(results)
    results = get_current_user_saved_tracks(sp)
    print(results)
    results = search_tracks(sp, "Jeff Beck", limit=20)
    print(results)


if __name__ == "__main__":
    main()
