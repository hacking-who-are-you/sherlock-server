class Sherlock:
    def __init__(self, url: str):
        self.url = url

    async def run(self) -> str:
        raise NotImplementedError()
