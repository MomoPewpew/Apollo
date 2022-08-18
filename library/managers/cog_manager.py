from discord.ext.commands import Cog
from xmlrpc.client import Boolean

class Cog_manager(object):
    def __init__(self, cogs) -> None:
        self.cogs = cogs
        for cog in self.cogs:
            setattr(self, cog, False)

    def ready_up(self, cog: Cog) -> None:
        setattr(self, cog, True)
        print(f"  {cog} cog ready")

    def all_ready(self) -> Boolean:
        return all([getattr(self, cog) for cog in self.cogs])