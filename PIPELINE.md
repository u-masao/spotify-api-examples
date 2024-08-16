```mermaid
flowchart TD
	node1["data/raw/favorite_artists.txt.dvc"]
	node2["make_dataset"]
	node3["upload_data_to_surrealdb"]
	node1-->node2
	node2-->node3
```
