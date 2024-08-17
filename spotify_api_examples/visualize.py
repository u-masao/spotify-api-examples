import asyncio
import json
import os
import sys
from pathlib import Path

import mlflow
import networkx as nx
import typer
from loguru import logger
from pyvis.network import Network
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


async def visualize():
    artists, artist_relations = await load_data()
    # print("==== artists raw")
    # print(json.dumps(artists, indent=4, ensure_ascii=False))
    # print("==== artist_relations raw")
    # print(json.dumps(artist_relations, indent=4, ensure_ascii=False))

    graph = nx.Graph()
    for artist in artists:
        graph.add_node(artist["id"])
    for artist_relation in artist_relations:
        graph.add_edge(artist_relation["from"], artist_relation["to"])

    # print("==== graph")
    # print(graph)
    nt = Network(height="800px", width="100%", notebook=False)
    nt.from_nx(graph)
    # print("==== network")
    # print(nt)
    nt.show("data/processed/graph.html", notebook=False)
    # nt.show("data/processed/graph.html")


async def load_data():
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
        artist = await db.select(artist_table)
        artist_relation = await db.select(artist_relation_table)

    return artist, artist_relation


app = typer.Typer()


@app.command()
def main(
    output_filepath: str = typer.Argument(..., help="出力ファイルへのパス"),
):

    # init log
    logger.info("Processing dataset...")
    mlflow.set_experiment("visualize")
    mlflow.start_run()

    cli_args = dict(
        output_filepath=output_filepath,
    )
    logger.info(f"args: {cli_args}")
    mlflow.log_params({f"args.{k}": v for k, v in cli_args.items()})

    # 処理
    asyncio.run(visualize())

    # ファイル出力
    results = []
    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(output_filepath, "w"), indent=4, ensure_ascii=False)

    # logging
    logger.success("Processing dataset complete.")


if __name__ == "__main__":
    logger.configure(handlers=[{"sink": sys.stderr, "backtrace": False, "diagnose": False}])
    app()
