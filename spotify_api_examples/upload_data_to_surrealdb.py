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


async def create_artist_relation(
    db, relation_from, relation_to, table="artist_relation", target_table="artist"
):
    return await db.create(
        table,
        {
            "from": f"{target_table}:{relation_from}",
            "to": f"{target_table}:{relation_to}",
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

        await db.create(
            artist_table,
            {
                "id": "root",
            },
        )
        for artist in artists:
            level = artist["level"]
            if level == 0:
                data = artist["result"]["artists"]["items"][0]
                artist_id = data["id"]
                name = data["name"]
                logger.info(f"upload: {level=} {artist_id=} {name=}")
                await db.create(artist_table, data)
                await create_artist_relation(db, "root", artist_id, artist_relation_table)
            if level == 1:
                relation_from = artist["query"]
                for related_artist in artist["result"]["artists"]:
                    artist_id = related_artist["id"]
                    name = related_artist["name"]
                    logger.info(f"upload: {level=} {artist_id=} {name=}")
                    await db.create(artist_table, related_artist)
                    await create_artist_relation(
                        db, relation_from, artist_id, artist_relation_table
                    )


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
