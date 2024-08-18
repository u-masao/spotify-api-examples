import asyncio
import os
import sys

import mlflow
import networkx as nx
import numpy as np
import typer
from loguru import logger
from pyvis.network import Network
from surrealdb import Surreal


async def visualize(output_filepath: str):
    artists, artist_relations = await load_data()

    genre_group = 20
    artist_graph = nx.DiGraph()
    genre_graph = nx.Graph()

    for artist in artists:
        size = 10 * np.log10(artist.get("popularity", 10))  # 0 to 100
        # size = artist.get('followers', {'total':10})['total']
        artist_graph.add_node(artist["id"], label=artist["name"], group=artist["level"], size=size)
        genre_graph.add_node(artist["id"], label=artist["name"], group=artist["level"], size=size)
        for genre in artist.get("genres", []):
            genre_graph.add_node(genre, label=genre, group=genre_group)
            genre_graph.add_edge(genre, artist["id"])

    for artist_relation in artist_relations:
        artist_graph.add_edge(artist_relation["from"], artist_relation["to"])
        # genre_graph.add_edge(artist_relation["from"], artist_relation["to"])

    nt = Network(height="900px", width="90%", directed=True)
    nt.from_nx(artist_graph)
    nt.show_buttons()
    nt.write_html(output_filepath)

    nt = Network(height="900px", width="90%", directed=True)
    nt.from_nx(genre_graph)
    nt.show_buttons()
    nt.write_html("data/processed/genre.html")


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
