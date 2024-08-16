import json
import asyncio
import os
from pathlib import Path
from typing import Any, List

import mlflow
import surrealdb
import typer
from loguru import logger
from surrealdb import Surreal


async def demo():
    """Example of how to use the SurrealDB client."""
    async with Surreal("ws://localhost:8000/rpc") as db:
        await db.signin(
            {"user": os.environ["SURREALDB_USER"], "pass": os.environ["SURREALDB_PASS"]}
        )
        await db.use("test", "test")
        await db.create(
            "person",
            {
                "user": "me",
                "pass": "safe",
                "marketing": True,
                "tags": ["python", "documentation"],
            },
        )
        print(await db.select("person"))
        print(
            await db.update(
                "person",
                {"user": "you", "pass": "very_safe", "marketing": False, "tags": ["Awesome"]},
            )
        )
        print(await db.delete("person"))

        # You can also use the query method
        # doing all of the above and more in SurrealQl

        # In SurrealQL you can do a direct insert
        # and the table will be created if it doesn't exist
        await db.query(
            """
        insert into person {
            user: 'me',
            pass: 'very_safe',
            tags: ['python', 'documentation']
        };
        """
        )
        print(await db.query("select * from person"))

        print(
            await db.query(
                """
        update person content {
            user: 'you',
            pass: 'more_safe',
            tags: ['awesome']
        };
        """
            )
        )
        print(await db.query("delete person"))


# SurrealDB への接続
db = surrealdb.Surreal("ws://localhost:8000/rpc")


async def initialize_and_insert_data():
    # データベースにサインイン
    await db.signin({"user": os.environ["SURREALDB_USER"], "pass": os.environ["SURREALDB_PASS"]})
    # 名前空間とデータベースを選択
    await db.use("spotify", "artists")

    # コレクションの初期化
    await db.query("CREATE TABLE IF NOT EXISTS artist")

    # アーティストデータの挿入
    artist_data = [
        {"artist_id": "1", "name": "Artist A", "genre": "Pop", "related_artists": ["2", "3"]},
        {"artist_id": "2", "name": "Artist B", "genre": "Rock", "related_artists": ["1"]},
        {"artist_id": "3", "name": "Artist C", "genre": "Pop", "related_artists": ["1"]},
    ]

    for data in artist_data:
        await db.create("artist", data)


async def fetch_related_artists(artist_id):
    # 関連アーティストの取得
    result = await db.query(
        "SELECT * FROM artist WHERE artist_id IN $related_artists", {"related_artists": artist_id}
    )
    return result


# 非同期処理の実行
async def access_db():
    await initialize_and_insert_data()

    related_artists = await fetch_related_artists("1")
    print(related_artists)

    await db.close()


def upload_data_to_surrealdb(
    artists_info: List[Any],
):
    access_db()


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
    logger.info(f"{artists_info=}")

    # 処理
    results = upload_data_to_surrealdb(artists_info)
    asyncio.run(demo())

    # ファイル出力
    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(output_filepath, "w"), indent=4, ensure_ascii=False)

    # logging
    logger.success("Processing dataset complete.")


if __name__ == "__main__":
    app()
