# ElasticacheMigration
Script to move data between Elasticache Redis clusters

## Setup

### Clone the repo

```bash
git clone git@github.com:joseapeinado/ElasticacheMigration.git
```

### Prepare the virtual env and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Profit!!

```bash
SRC_CLUSTER=src_cluster.spznk9.ng.0001.use1.cache.amazonaws.com
DST_CLUSTER=dst_cluster.spznk9.ng.0001.use1.cache.amazonaws.com

python3 migrate-redis.py $SRC_CLUSTER --src_port=6379 $DST_CLUSTER --dst_port 6379 --src_db 2 --dst_db 2
Connecting to Redis instances...
Counting keys to migrate...
19222 keys: 100% |###############################################################################################################################################################################################################################################| Time: 0:00:05
('Keys disappeared on source during scan:', 0)
('Keys already existing on destination:', 19195)
```

## Options
You cn check the available options with the `--help` flag

```bash
$ python3 migrate_keys.py --help
Usage: migrate_keys.py [OPTIONS] SRC_HOST DST_HOST

Options:
  --src_port INTEGER  Source port (default: 6379)
  --src_db INTEGER    Source db number (default: 0)
  --src_ssl           SSL connection to source? (default: False)
  --src_pass TEXT     Source password (default: None)
  --dst_port INTEGER  Destination port (default: 6379)
  --dst_db INTEGER    Destination db number (default: 0)
  --dst_ssl           SSL connection to destination? (default: False)
  --dst_pass TEXT     Destination password (default: None)
  --flush             Flush destination before migration? (default: False)
  --pattern TEXT      Pattern of key names to migrate (default: *)
  --replace           Replace existing keys in destination? (default: False)
  --help              Show this message and exit.
```