"""
Dealing with postgres in a data capacity.
"""
import logging
from typing import Iterable

from psycopg.sql import SQL

from .pg_conn import fetch

LOG = logging.getLogger(__name__)


def _flatten_signals(data: dict) -> dict:
    """
    Goes from

        [{"signal":{"type":"item","name":"uranium-rounds-magazine"},"count":102400}]}, ...]

    to

        {"uranium-rounds-magazine": "102400"}
    """

    return {
        signal['signal']['name']: str(signal['count'])
        for signal in data
    }


def add_samples(conn, time: int, entities: list[dict]):
    """
    Adds the given samples to the data set.
    """
    # FIXME: actual schema
    with conn.cursor() as cur, cur.copy(
        SQL("COPY __raw__ (stamp, name, tags, surface_index, color, data) FROM STDIN")
    ) as copy:
        for ent in entities:
            if ent['settings']['tags']:
                tags = {
                    left: right if eq else None 
                    for left, eq, right in [
                        tag.partition('=')
                        for tag in ent['settings']['tags'].split(',')
                    ]
                }
            else:
                tags = {}
            if 'red_signals' in ent:
                copy.write_row((
                    time,
                    ent['settings']['name'],
                    tags,
                    ent.get('surface_index', None),
                    "red",
                    _flatten_signals(ent['red_signals'])
                ))

            if 'green_signals' in ent:
                # LOG.debug("entity %r", ent)
                # LOG.debug("tags %r", tags)
                # LOG.debug("signals %r", _flatten_signals(ent['green_signals']))
                copy.write_row((
                    time,
                    ent['settings']['name'],
                    tags,
                    ent.get('surface_index', None),
                    "green",
                    _flatten_signals(ent['green_signals'])
                ))


def read_names(conn) -> Iterable[str]:
    """
    Reads all existing stat names.
    """
    with conn.cursor() as cur:
        cur.execute(SQL("SELECT DISTINCT name FROM __raw__"))
        for row in fetch(cur):
            yield row.name
