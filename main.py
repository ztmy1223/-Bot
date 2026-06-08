import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

Intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!", 
    intents=Intents,
    allowed_mentions=discord.AllowedMentions(everyone=True)
)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"Mahjong Bot 準備完了: {bot.user}")
    
    # Cogs の自動読み込み
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(cog_name)
                    print(f"Loaded extension: {cog_name}")
                except Exception as e:
                    print(f"Failed to load extension {cog_name}: {e}")

    # スラッシュコマンドの同期
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました．")
    except Exception as e:
        print(f"同期エラー: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.CommandNotFound, commands.MissingRole)):
        return
    raise error

# ボットの起動
token = os.getenv("DISCORD_BOT_TOKEN")
if token and token != "YOUR_DISCORD_BOT_TOKEN_HERE":
    bot.run(token)
else:
    print("エラー: .envファイルに有効なDISCORD_BOT_TOKENを設定してください。")
