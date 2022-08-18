from code import interact
import discord
from discord import app_commands
from discord.ext.commands import Cog

COG_NAME = "dream"

class Dream(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Turn a text prompt into an image with Stable Diffusion"
    )
    async def command_dream(
        self, interaction: discord.Interaction,
        prompt: str=""
    ) -> None:
        await self.function_dream(
            interaction,
            prompt
        )

    async def function_dream(self, interaction: discord.Interaction, prompt: str) -> None:
        estimated_time = 5

        ##TODO: Make actual instruction
        instructions = "Test instructions"

        self.bot.task_manager.add_task("image", interaction.user.id, interaction.channel.id, instructions, estimated_time)

        self.bot.prompt_manager.add_prompt("textToImage", prompt, self.bot.user_manager.get_user_id(interaction.user))

        ##TODO: Make random response fetcher, based on whether the GPU server is on
        ##TODO: Move this away from this function and to task manager
        responsStr = (
            "Daedalus is firing up the furnace right as we speak. Estimated time: "
            + (self.bot.task_manager.get_queue_estimate() + 20)
            + "\nYour prompt has been saved under the tags " +
            self.bot.user_manager.get_tags_active_csv[1:-1] +
            ". Press the button below to remove it from your history."
        )
        await interaction.response.send_message(responsStr, ephemeral=True)

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Dream(bot))