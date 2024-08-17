import json
from pathlib import Path

import mlflow
import spotipy
import typer
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


def load_input_data(input_filepath: str):
    return list(set(open(input_filepath, "r").read().strip().split("\n")))


app = typer.Typer()


@app.command()
def main(
    input_filepath: str = typer.Argument(
        ..., exists=True, readable=True, help="入力ファイルへのパス"
    ),
    output_filepath: str = typer.Argument(..., help="出力ファイルへのパス"),
    limit: int = typer.Option(0, min=0, help="データの読み込み制限行数"),
):

    # init log
    logger.info("Processing dataset...")
    mlflow.set_experiment("make_dataset")
    mlflow.start_run()

    cli_args = dict(
        input_filepath=input_filepath,
        output_filepath=output_filepath,
    )
    logger.info(f"args: {cli_args}")
    mlflow.log_params({f"args.{k}": v for k, v in cli_args.items()})

    # 認証なしのクライアントを取得
    sp = get_client_without_auth()
    # sp = get_client_with_auth()

    results = []

    # load input data
    favorits = load_input_data(input_filepath)

    if limit > 0:
        favorits = favorits[:limit]

    logger.info(f"{favorits=}")

    for query in favorits:
        # query 毎にループ
        artists = search(sp, query, limit=1, search_type="artist")
        results.append({"result": artists, "query": query, "level": 0})

        artist_name = artists["artists"]["items"][0]["name"]
        artist_id = artists["artists"]["items"][0]["id"]

        logger.info(f"{query=}")
        logger.info(f"{artist_name=}")
        logger.info(f"{artist_id=}")

        related_artists = sp.artist_related_artists(artist_id)
        results.append({"result": related_artists, "query": artist_id, "level": 1})
        logger.info(f"{related_artists=}")

    # ファイル出力
    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(output_filepath, "w"), indent=4, ensure_ascii=False)

    # logging
    mlflow.log_params({"output.length": len(results)})

    logger.success("Processing dataset complete.")


if __name__ == "__main__":
    app()
