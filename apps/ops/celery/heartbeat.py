import os
import tempfile
from pathlib import Path

from celery.signals import heartbeat_sent, worker_ready, worker_shutdown


def get_heartbeat_dir():
    """获取心跳文件目录，支持 Windows 兼容"""
    # 优先使用环境变量中的 TMPDIR（在 main.py 中设置）
    tmpdir = os.environ.get('TMPDIR') or os.environ.get('TEMP') or tempfile.gettempdir()
    heartbeat_dir = Path(tmpdir) / 'maxkb_worker'
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    return heartbeat_dir


@heartbeat_sent.connect
def heartbeat(sender, **kwargs):
    worker_name = sender.eventer.hostname.split('@')[0]
    heartbeat_path = get_heartbeat_dir() / 'worker_heartbeat_{}'.format(worker_name)
    try:
        heartbeat_path.touch()
    except Exception:
        pass


@worker_ready.connect
def worker_ready(sender, **kwargs):
    worker_name = sender.hostname.split('@')[0]
    ready_path = get_heartbeat_dir() / 'worker_ready_{}'.format(worker_name)
    try:
        ready_path.touch()
    except Exception:
        pass


@worker_shutdown.connect
def worker_shutdown(sender, **kwargs):
    worker_name = sender.hostname.split('@')[0]
    for signal in ['ready', 'heartbeat']:
        path = get_heartbeat_dir() / 'worker_{}_{}'.format(signal, worker_name)
        path.unlink(missing_ok=True)
