from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import os
import logging

maxkb_logger = logging.getLogger('max_kb')


class DailyTimedRotatingFileHandler(TimedRotatingFileHandler):
    def rotator(self, source, dest):
        """ Override the original method to rotate the log file daily."""
        dest = self._get_rotate_dest_filename(source)
        if os.path.exists(source):
            # Skip if another process already rotated (file gone or dest exists)
            if os.path.exists(dest):
                return
            try:
                os.rename(source, dest)
            except PermissionError:
                # On Windows, another process may still hold a handle after rename
                # by this process. Re-check: if dest exists, rotation succeeded.
                if os.path.exists(dest):
                    return
                raise

    @staticmethod
    def _get_rotate_dest_filename(source):
        date_yesterday = (
            datetime.now() - timedelta(days=1)
        ).strftime('%Y-%m-%d')
        path = [
            os.path.dirname(source),
            date_yesterday,
            os.path.basename(source)
        ]
        filename = os.path.join(*path)
        os.makedirs(os.path.dirname(filename), 0o700, exist_ok=True)
        return filename
