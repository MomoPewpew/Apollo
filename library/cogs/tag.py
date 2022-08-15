from discord.ext.commands import Cog

COG_NAME = "tag"

class Tag(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(COG_NAME)

def setup(bot):
    bot.add_cog(Tag(bot))