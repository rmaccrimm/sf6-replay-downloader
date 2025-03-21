import json
import os
from pathlib import Path

import defopt
import duckdb

# Full query unions rows where your are player 1 with those where you're player 2
_QUERY_PART = """--sql
SELECT  
    replay_id,
    player{me}_info.playing_character_name AS my_char,
    player{op}_info.playing_character_name AS op_char,            
    IF(player{me}_info.battle_input_type = 0, 'C', 'M') AS my_control,
    IF(player{op}_info.battle_input_type = 0, 'C', 'M') AS op_control,
    player{op}_info.player.fighter_id AS op_fighter_id,
    player{op}_info.player.short_id AS op_sid,    
    player{me}_info.master_rating AS my_mr,
    player{op}_info.master_rating AS op_mr,
    player{me}_info.master_rating_ranking AS my_mr_rank,
    player{op}_info.master_rating_ranking AS op_mr_rank,
    player{me}_info.league_point AS my_lp,
    player{op}_info.league_point AS op_lp,
    player{me}_info.league_rank AS my_rank,
    player{op}_info.league_rank AS op_rank,
    player{me}_info.master_league AS my_master_league,
    player{op}_info.master_league AS op_master_league,
    list_transform(player{me}_info.round_results, x -> if(x=0, 'LOSS', 'WIN')) AS round_results,
    -- Count the number of losses (0s) to determine if this was a win or not
    list_sum([not x for x in cast(player{me}_info.round_results as boolean[])])=2 as win,
    replay_battle_type_name AS battle_type,
    battle_version,
    to_timestamp(uploaded_at) as uploaded_at
from json_import
where player{me}_info.player.short_id = $1
"""

TRANSFORM_QUERY = (
    f"{_QUERY_PART.format(me=1, op=2)} UNION {_QUERY_PART.format(me=2, op=1)}"
)


def load_replays(conn: duckdb.DuckDBPyConnection, import_file: str, sid: int):
    conn.sql(
        f"""--sql
        CREATE TEMPORARY TABLE json_import AS 
            SELECT * FROM '{import_file}';
        """
    )
    try:
        # Just create the table directly from the query the first time the script is run
        conn.execute(
            f"""--sql
            CREATE TABLE replays AS 
                SELECT * FROM (
                    {TRANSFORM_QUERY}
                );
            """,
            [sid],
        )
    except duckdb.CatalogException:
        conn.execute(
            f"""--sql
            INSERT INTO replays BY NAME
                SELECT * 
                FROM (
                    {TRANSFORM_QUERY}
                )
                WHERE replay_id NOT IN (
                    SELECT DISTINCT replay_id
                    FROM replays
                );
            """,
            [sid],
        )
    conn.sql(
        """--sql
        DROP TABLE json_import;
        """
    )
    print(f"Loaded {import_file}")


def main(config_file: str, *import_files: str):
    with open(config_file) as f:
        args = json.loads(f.read())
        sid = int(args["PLAYER_SID"])
        data_dir = args["DATA_DIR"]

    db_file = os.path.join(data_dir, "sf.duckdb")
    with duckdb.connect(db_file) as conn:
        for import_file in import_files:
            load_replays(conn, import_file, sid)


if __name__ == "__main__":
    defopt.run(main)
