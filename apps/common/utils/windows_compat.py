# Windows compatibility: add missing Unix-only attributes
import os
import signal

if not hasattr(os, 'getuid'):
    os.getuid = lambda: 0

if not hasattr(os, 'getgid'):
    os.getgid = lambda: 0

if not hasattr(os, 'getppid'):
    os.getppid = lambda: 0

if not hasattr(signal, 'SIGHUP'):
    signal.SIGHUP = 1

if not hasattr(signal, 'SIGTERM'):
    signal.SIGTERM = 15
