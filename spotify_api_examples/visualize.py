import asyncio
import os
import sys

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


async def visualize(output_filepath: str):
    artists, artist_relations = await load_data()

    graph = nx.DiGraph()
    for artist in artists:
        graph.add_node(artist["id"], label=artist["name"], group=artist["level"])
    for artist_relation in artist_relations:
        graph.add_edge(artist_relation["from"], artist_relation["to"])

    nt = Network(height="900px", width="90%", directed=True)
    nt.from_nx(graph)
    nt.show_buttons()
    nt.write_html(output_filepath)


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
    asyncio.run(visualize(output_filepath))

    # logging
    logger.success("Processing dataset complete.")


if __name__ == "__main__":
    logger.configure(handlers=[{"sink": sys.stderr, "backtrace": False, "diagnose": False}])
    app()
