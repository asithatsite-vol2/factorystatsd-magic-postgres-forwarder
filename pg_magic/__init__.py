import datetime
import logging
from pathlib import Path

import click

from .incoming import read_factorio
from .pg_conn import connection
from .pg_schema import (
    check_extensions, base_schema, check_view_columns, check_view_names,
    set_epoch
)
from .pg_data import add_samples, read_names


LOG = logging.getLogger(__name__)


def init(database_url):
    with connection(database_url) as conn:
        check_extensions(conn)
    # Installing extensions invalidates the connection

    with connection(database_url) as conn:
        base_schema(conn)


@click.command()
@click.option(
    '--script-output', envvar='SCRIPT_OUTPUT', 
    type=click.Path(file_okay=False, readable=True, path_type=Path),
)
@click.option('--database-url', envvar='DATABASE_URL')
def main(script_output, database_url):
    logging.basicConfig(level='DEBUG')

    LOG.info("Forwarder Startup")

    LOG.info("Initial database setup")
    init(database_url)

    with connection(database_url) as conn:
        stat_names = set(read_names(conn))
        for which, blob in read_factorio(script_output):
            match which:
                case 'meta':
                    # Check and update schema
                    all_names = sorted(
                        set(blob['item_names'])
                        | set(blob['virtual_signal_names'])
                        | set(blob['fluid_names'])
                    )
                    LOG.info("Got metadata with %i items", len(all_names))
                    # Reread
                    check_view_columns(conn, all_names)
                    check_view_names(conn, stat_names, all_names)

                case 'samples':
                    timestamp = blob['ticks'] / 60
                    set_epoch(conn, datetime.datetime.now() - datetime.timedelta(seconds=timestamp))
                    LOG.info("Got samples @ %i time with %i entries", timestamp, len(blob['entities']))
                    add_samples(conn, timestamp, blob['entities'])
                    check_view_names(conn, read_names(conn), all_names)
