import os
import discord
from discord.ext import commands
import deepl

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("DEEPL_API_KEY", "YOUR_DEEPL_API_KEY_HERE")
        self.translator = deepl.Translator(api_key) if api_key != "YOUR_DEEPL_API_KEY_HERE" else None

    async def _translate(self, ctx, target_lang):
        if not self.translator:
            await ctx.reply("Error: DeepL API key is not configured.")
            return
        try:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            result = self.translator.translate_text(message.content, target_lang=target_lang)
            await message.reply(result.text, mention_author=False)
        except Exception as e:
            await ctx.reply(f"Translation error: {e}")

    @commands.command()
    async def en(self, ctx):
        await self._translate(ctx, 'EN-US')

    @commands.command()
    async def jp(self, ctx):
        await self._translate(ctx, 'JA')

    @commands.command()
    async def zh(self, ctx):
        await self._translate(ctx, 'ZH-HANS')

async def setup(bot):
    await bot.add_cog(TranslateCog(bot))
