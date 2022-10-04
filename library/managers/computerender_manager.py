import os
import shutil
from urllib import parse
from urllib.request import Request, urlopen
import discord

from ..cogs import txt2img, tag
from .. import bot
from ..db import db
from PIL import Image

class Computerender_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot
    
    async def function_computerender(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool
    ) -> None:
        await self.respond(interaction, "txt2img", prompt, 10)

        if batch:
            pass
        else:
            img = await self.computerender_single(prompt, height, width, seed, scale, steps, plms)

            path = os.path.join("./out/", f"instance_-1")
            if not os.path.exists(path):
                os.mkdir(path)
            
            for fileName in os.listdir(path):
                file_path = os.path.join(path, fileName)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            baseFileName = prompt[:min(len(prompt), 50)].replace(" ", "_").replace("\\", "_").replace("/", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
            fileName = f"{baseFileName}-{seed}.png"
            file_path = f"{path}/{fileName}"

            img.save(file_path, "png")
            
            embed = discord.Embed(title="Stable Diffusion txt2img", color=0x2f3136)
            file = discord.File(file_path, filename=fileName)
            embed.set_image(url=f"attachment://{fileName}")

            model = "Stable Diffusion 1.4"

            embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `{model}`"

            view = txt2img.View_txt2img_single(self.bot, prompt, height, width, seed, scale, steps, plms, model)

            user = interaction.user
            userID = user.id
            channelID = interaction.channel.id
            userIDTemp = self.bot.user_manager.get_user_id(user)

            if (self.bot.user_manager.is_user_privacy_mode(userIDTemp)):
                await user.send(f"Here is the output for your task.",embed=embed, file=file)
            else:
                if file == None:
                    await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for your task.",embed=embed, view=view)
                else:
                    message = await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for your task.",embed=embed, file=file, view=view)

                    image_url = message.embeds[0].image.url

                    if view is not None:
                        for child in view.children:
                            if (hasattr(child, "img_url")):
                                child.img_url = image_url

    async def respond(self, interaction: discord.Interaction, promptType: str, promptString: str, queue_estimate: int) -> None:
        returnString1 = f"Your task will be processed and should be done in `{queue_estimate} seconds`."

        returnString = returnString1

        userID = self.bot.user_manager.get_user_id(interaction.user)
        if (promptType is not None and promptString is not None and not self.bot.user_manager.is_user_privacy_mode(userID)):
            promptTags = self.bot.user_manager.get_tags_active_csv(userID)
            if promptID := self.bot.prompt_manager.get_promptID(userID, promptString) is not None:
                tagsOld = db.field("SELECT promptTags FROM prompts WHERE promptID = ?",
                    promptID
                )

                if tagsOld != promptTags:
                    db.execute("UPDATE prompts SET promptTags = ? WHERE promptID = ?",
                        promptTags,
                        promptID
                    )
                    returnString += f"\nThe prompt `{promptString}` has been updated to match the tags `" + promptTags[1:-1] + "`"
                
                await interaction.response.send_message(content=returnString, ephemeral=True)
            else:
                if db.field("SELECT promptID FROM prompts WHERE promptID = 1") == None:
                    promptID = 1
                else:
                    promptID = db.field("SELECT MAX(promptID) FROM prompts") + 1

                self.bot.prompt_manager.add_prompt(promptType, promptString, userID)

                if (promptTags == ","):
                    returnString += f"\nThe prompt `{promptString}` was saved to your history but you had no active tags."
                else:
                    returnString += f"\nThe prompt `{promptString}` was saved to your history under the tags `" + promptTags[1:-1] + "`"
                
                returnString += "\nIf you would like to delete this prompt from your history then press the `Forget` button."

                await interaction.response.send_message(content=returnString, view=tag.View_forget_prompt(self.bot.prompt_manager, promptID, returnString1), ephemeral=True)
        else:
            await interaction.response.send_message(content=returnString, ephemeral=True)

    async def computerender_single(self,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool
    ) -> Image:
        prompt = parse.quote(prompt)
        url = f"https://api.computerender.com/generate/{prompt}?seed={seed}&w={width}&h={height}&guidance={scale}&iterations={steps}"
        req = Request(url)
        req.add_header("Authorization", f"X-API-Key {self.bot.COMPUTERENDERKEY}")
        print(f"Fetching computerender img at {url}")
        return Image.open(urlopen(req))