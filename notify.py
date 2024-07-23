import os
import sys
from datetime import datetime

try:
    import apprise
except ImportError:
    apprise = None


class Notifier:

    def __init__(self, apprise_endpoints: list[str] = None):
        self.apobj = None
        if apprise and apprise_endpoints:
            self.apobj = apprise.Apprise()
            [self.apobj.add(x) for x in apprise_endpoints]

    def notify(self, message: str):
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        full_message = f"{message}\nDatetime: {timestamp}"

        if self.apobj:
            return self.apobj.notify(
                body=full_message,
                title="Dolores",
            )
        else:
            print(full_message, file=sys.stderr)
            return False


# Initialize Notifier with APPRISE_ENDPOINTS if available
apprise_endpoints = os.environ.get("APPRISE_ENDPOINTS")
if apprise_endpoints:
    apprise_endpoints = apprise_endpoints.split(",")
notif = Notifier(apprise_endpoints)
