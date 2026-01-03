# Copyright (c) 2026 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

import psycopg
from psycopg import sql
from psycopg_pool import ConnectionPool
from typing import List, Tuple, Optional

class GoogleOSINTDB:
    """
    PostgreSQL helper class with connection pooling and batch inserts.
    """

    def __init__(self, dbname, user, password, host="localhost", port=5432, minconn=1, maxconn=5):
        conninfo = (
            f"dbname={dbname} user={user} password={password} "
            f"host={host} port={port}"
        )
        self.pool = ConnectionPool(
            conninfo=conninfo,
            min_size=minconn,
            max_size=maxconn,
            open=True,
        )
        if not self.pool:
            raise Exception("Failed to create Postgres connection pool.")

    def execute_query(self, query: str, params: Optional[Tuple] = None):
        conn = self.pool.getconn()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()

    def batch_insert(self, table: str, columns: List[str], values: List[Tuple]):
        """
        Efficient batch insert using executemany (psycopg v3).
        """
        if not values:
            return
        
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        )
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, values)
                conn.commit()

    def close_pool(self):
        self.pool.close()
