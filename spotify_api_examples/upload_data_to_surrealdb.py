import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, List

import mlflow
import typer
from loguru import logger
from surrealdb import Surreal


async def create_artist_relation(db, relation_from, relation_to, table="artist_relation"):
    return await db.create(
        table,
        {
            "from": relation_from,
            "to": relation_to,
            "id": f"{relation_from}_{relation_to}",
        },
    )


async def upload_artists(artists):
    hostname = os.environ["SURREALDB_HOST"]
    port = os.environ["SURREALDB_PORT"]
    async with Surreal(f"ws://{hostname}:{port}/rpc") as db:
        await db.signin(
            {"user": os.environ["SURREALDB_USER"], "pass": os.environ["SURREALDB_PASS"]}
        )

        # set namespace and db
        await db.use("spotify", "spotify")

        artist_table = "artist"
        artist_relation_table = "artist_relation"

        # delete db
        await db.delete(artist_table)
        await db.delete(artist_relation_table)

        for artist in artists:
            if artist["level"] == 0:
                data = artist["result"]["artists"]["items"][0]
                artist_id = data["id"]
                logger.info(f"upload: {artist_id=}")
                await db.create(artist_table, data)
            if artist["level"] == 1:
                for related_artists in artist["result"]["artists"]:
                    artist_id = related_artists["id"]
                    logger.info(f"upload: {artist_id=}")
                    await db.create(artist_table, related_artists)

        # result = await db.select("artist")
        # print(json.dumps(result, indent=4, ensure_ascii=False))
        # print(await db.query("select name from artist"))
        # print(await db.query("select name from artist:7zsxdMsODmHKTbTB00t9wS"))

        for artist in artists:
            if artist["level"] == 1:
                relation_from = artist["query"]
                for related_artists in artist["result"]["artists"]:
                    relation_to = related_artists["id"]
                    await create_artist_relation(
                        db, relation_from, relation_to, artist_relation_table
                    )

        # result = await db.select("artist_relation")
        # print(json.dumps(result, indent=4, ensure_ascii=False))
        # search_id = "artist_relation:7xIfi0ePXzLGlYO5lFjnvu_58YNdEUQRt7LNccL1icwYL"
        # print(await db.query(f"select * from {search_id}"))


def upload_data_to_surrealdb(
    artists_info: List[Any],
):
    asyncio.run(upload_artists(artists_info))


def load_input_data(input_filepath: str):
    return json.load(open(input_filepath, "r"))


app = typer.Typer()


@app.command()
def main(
    input_filepath: str = typer.Argument(
        ..., exists=True, readable=True, help="入力ファイルへのパス"
    ),
    output_filepath: str = typer.Argument(..., help="出力ファイルへのパス"),
):

    # init log
    logger.info("Processing dataset...")
    mlflow.set_experiment("upload_data")
    mlflow.start_run()

    cli_args = dict(
        input_filepath=input_filepath,
        output_filepath=output_filepath,
    )
    logger.info(f"args: {cli_args}")
    mlflow.log_params({f"args.{k}": v for k, v in cli_args.items()})

    # load input data
    artists_info = load_input_data(input_filepath)

    # 処理
    results = upload_data_to_surrealdb(artists_info)

    # ファイル出力
    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(output_filepath, "w"), indent=4, ensure_ascii=False)

    # logging
    logger.success("Processing dataset complete.")


if __name__ == "__main__":
    logger.configure(handlers=[{"sink": sys.stderr, "backtrace": False, "diagnose": False}])
    app()
