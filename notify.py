from datetime import datetime

import apprise

from configload import config


class Notifier:
    def __init__(self, apprise_endpoints: list[str]):
        self.apobj = apprise.Apprise()
        if apprise_endpoints:
            [self.apobj.add(x) for x in apprise_endpoints]

    def notify(self, message: str):
        return self.apobj.notify(
            body=f"{message}"
            f'Datetime: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}',
            title="Dolores",
        )


notif = Notifier(config["apprise_endpoints"])
