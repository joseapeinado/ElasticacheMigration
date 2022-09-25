"""
Forked and heavily adappted from:
https://gist.github.com/kitwalker12/517d99c3835975ad4d1718d28a63553e
Copies all keys from the source Redis host to the destination Redis host.
Useful to migrate Redis instances where commands like SLAVEOF and MIGRATE are
restricted (e.g. on Amazon ElastiCache).
The script scans through the keyspace of the given database number and uses
a pipeline of DUMP and RESTORE commands to migrate the keys.
Requires Redis 2.8.0 or higher.
Python requirements:
click
progressbar
redis
"""
import click
from progressbar import ProgressBar
from progressbar.widgets import Bar, ETA, Percentage
import redis
from redis.exceptions import ResponseError
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0


def _copy_keys(keys, src_pipe, dst, replace, non_existing, already_existing):
    # We execute the source pipeline.
    src_result = src_pipe.execute()
    # We create the matching destination pipeline.
    dst_pipe = dst.pipeline()
    for key, ttl, data in zip(keys, src_result[::2], src_result[1::2]):
        if data != None:
            dst_pipe.restore(key, ttl if ttl > 0 else 0, data, replace=replace)
        else:
            non_existing += 1
    # We execute the destination pipeline.
    dst_result = dst_pipe.execute(False)
    # We analyze the results of the destination pipeline execution.
    for key, result in zip(keys, dst_result):
        if result != b'OK':
            e = result
            if (
                hasattr(e, 'args')
                and e.args[0] in (
                    'BUSYKEY Target key name already exists.',
                    'Target key name is busy.'
                )
            ):
                already_existing += 1
            else:
                print("Key failed:", key, repr(data), repr(result))
                raise e
    return non_existing, already_existing


@click.command()
@click.argument('src_host')
@click.option('--src_port', default=DEFAULT_REDIS_PORT, help='Source port (default: %d)' % DEFAULT_REDIS_PORT)
@click.option('--src_db', default=DEFAULT_REDIS_DB, help='Source db number (default: %d)' % DEFAULT_REDIS_DB)
@click.option('--src_ssl', default=False, is_flag=True, help='SSL connection to source? (default: False)')
@click.option('--src_pass', default=None, help='Source password (default: None)')
@click.argument('dst_host')
@click.option('--dst_port', default=DEFAULT_REDIS_PORT, help='Destination port (default: %d)' % DEFAULT_REDIS_PORT)
@click.option('--dst_db', default=DEFAULT_REDIS_DB, help='Destination db number (default: %d)' % DEFAULT_REDIS_DB)
@click.option('--dst_ssl', default=False, is_flag=True, help='SSL connection to destination? (default: False)')
@click.option('--dst_pass', default=None, help='Destination password (default: None)')
@click.option('--flush', default=False, is_flag=True, help='Flush destination before migration? (default: False)')
@click.option('--pattern', default='*', help='Pattern of key names to migrate (default: *)')
@click.option('--replace', default=False, is_flag=True, help='Replace existing keys in destination? (default: False)')
def migrate(
    src_host, src_port, src_pass, src_ssl, src_db,
    dst_host, dst_port, dst_pass, dst_ssl, dst_db,
    pattern, flush, replace
):
    print("Connecting to Redis instances...")
    src = redis.StrictRedis(host=src_host, port=src_port,
                            ssl=src_ssl, db=src_db, password=src_pass)
    dst = redis.StrictRedis(host=dst_host, port=dst_port,
                            ssl=dst_ssl, db=dst_db, password=dst_pass)
    # Flush destination database?
    if flush:
        dst.flushdb()
    print("Counting keys to migrate...")
    num_keys = len(src.keys(pattern))
    if num_keys == 0:
        print("No keys found, exiting.")
        return
    progress_widgets = ['%d keys: ' %
                        num_keys, Percentage(), ' ', Bar(), ' ', ETA()]
    progress_bar = ProgressBar(
        widgets=progress_widgets, maxval=num_keys).start()
    BATCH_SIZE = 100
    cursor = 0
    non_existing = 0
    already_existing = 0
    keys = []
    src_pipe = src.pipeline()
    # We loop over the keys matching the specified pattern:
    for key in src.scan_iter(match=pattern):
        cursor += 1
        keys.append(key)
        src_pipe.pttl(key)
        src_pipe.dump(key)
        # We have iterated enough for a migration batch.
        if cursor % BATCH_SIZE == 0:
            # We copy that batch of keys...
            non_existing, already_existing = _copy_keys(
                keys, src_pipe, dst, replace, non_existing, already_existing)
            # ... and we reset the source containers to continue iterating.
            keys = []
            src_pipe = src.pipeline()
        progress_bar.update(min(num_keys, cursor))
    # Iteration is now over, we need to restore the last partial batch.
    non_existing, already_existing = _copy_keys(
        keys, src_pipe, dst, replace, non_existing, already_existing)
    progress_bar.finish()
    print("Keys disappeared on source during scan:", non_existing)
    print("Keys already existing on destination:", already_existing)


if __name__ == '__main__':
    migrate()
