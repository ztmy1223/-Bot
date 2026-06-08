import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import describe
from database import get_db_connection, SQL_QUERIES
from utils import GRADE_DIC

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="プレイヤー登録 Register as a player")
    @describe(name="ハンドルネーム/Handle name", grade="学年/Grade (1:B4, 2:M1, 3:M2, 4:D1, 5:D2, 6:D3, 7:Exchange student, 9:その他, 10:先生)")
    async def register(self, interaction: discord.Interaction, name: str, grade: int):
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(SQL_QUERIES['get_player'], (interaction.user.id,))
        if cursor.fetchone():
            await interaction.response.send_message("This user is already registered", ephemeral=True)
            cursor.close()
            db.close()
            return
            
        cursor.execute(SQL_QUERIES['get_player_fromname'], (name,))
        if cursor.fetchone():
            await interaction.response.send_message("This name is already registered", ephemeral=True)
            cursor.close()
            db.close()
            return
            
        if grade < 1 or grade > 10 or grade == 8:
            await interaction.response.send_message("This grade is invalid", ephemeral=True)
            cursor.close()
            db.close()
            return

        cursor.execute(SQL_QUERIES['add_player'], (interaction.user.id, name, grade))
        db.commit()
        
        guild = interaction.guild
        if guild:
            player_role = discord.utils.get(guild.roles, name="Player")
            if player_role:
                await interaction.user.add_roles(player_role)
            if grade in [1, 2, 3, 10]:
                grade_role = discord.utils.get(guild.roles, name=GRADE_DIC[grade])
                if grade_role:
                    await interaction.user.add_roles(grade_role)
            try:
                await interaction.user.edit(nick=name)
            except Exception:
                pass
        
        await interaction.response.send_message(f"Successfully registered as {name} ({GRADE_DIC[grade]})", ephemeral=True)
        cursor.close()
        db.close()

    @commands.command()
    @commands.has_role("Admin")
    async def rename(self, ctx, discord_id: int, new_name: str):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(SQL_QUERIES['get_player'], (discord_id,))
        if cursor.fetchone():
            cursor.execute(SQL_QUERIES['get_player_fromname'], (new_name,))
            if cursor.fetchone():
                await ctx.reply("This name is already taken")
                cursor.close()
                db.close()
                return
            cursor.execute(SQL_QUERIES['update_name'], (new_name, discord_id))
            db.commit()
            member = ctx.guild.get_member(discord_id) if ctx.guild else None
            if member:
                try:
                    await member.edit(nick=new_name)
                except Exception:
                    pass
                await ctx.reply(f"{member.mention} の名前を {new_name} に変更しました")
            else:
                await ctx.reply(f"ID: {discord_id} の名前をDB上で {new_name} に変更しました")
        else:
            await ctx.reply("This Discord account is not registered")
        cursor.close()
        db.close()

    @commands.command()
    @commands.has_role("Admin")
    async def regrade(self, ctx, discord_id: int, grade: int):
        if grade < 1 or grade > 10 or grade == 8:
            await ctx.reply("This grade is invalid")
            return
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(SQL_QUERIES['get_player'], (discord_id,))
        p = cursor.fetchone()
        if p:
            old_grade = p[3]
            cursor.execute(SQL_QUERIES['update_grade'], (grade, discord_id))
            db.commit()
            member = ctx.guild.get_member(discord_id) if ctx.guild else None
            if member:
                if old_grade in [1, 2, 3, 10]:
                    old_role = discord.utils.get(ctx.guild.roles, name=GRADE_DIC[old_grade])
                    if old_role: await member.remove_roles(old_role)
                if grade in [1, 2, 3, 10]:
                    new_role = discord.utils.get(ctx.guild.roles, name=GRADE_DIC[grade])
                    if new_role: await member.add_roles(new_role)
                await ctx.reply(f"{member.mention} の学年を {GRADE_DIC[grade]} に変更しました")
            else:
                await ctx.reply(f"DB上の学年を {GRADE_DIC[grade]} に変更しました")
        else:
            await ctx.reply("This Discord account is not registered")
        cursor.close()
        db.close()

    @commands.command()
    @commands.has_role("Admin")
    async def april(self, ctx):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(SQL_QUERIES['get_allplayer'])
        for p in cursor.fetchall():
            d_id, _, _, grade, _, _, _, _, _, _, _, _, _, _ = p
            if grade in [1, 2, 4, 5]:
                cursor.execute(SQL_QUERIES['update_grade'], (grade+1, d_id))
                member = ctx.guild.get_member(d_id) if ctx.guild else None
                if member:
                    old_role = discord.utils.get(ctx.guild.roles, name=GRADE_DIC[grade])
                    new_role = discord.utils.get(ctx.guild.roles, name=GRADE_DIC[grade+1])
                    if old_role: await member.remove_roles(old_role)
                    if new_role: await member.add_roles(new_role)
            elif grade in [3, 6]:
                cursor.execute(SQL_QUERIES['update_grade'], (9, d_id))
                member = ctx.guild.get_member(d_id) if ctx.guild else None
                if member and grade == 3:
                    old_role = discord.utils.get(ctx.guild.roles, name="M2")
                    if old_role: await member.remove_roles(old_role)
        db.commit()
        await ctx.reply("進級処理が完了しました．")
        cursor.close()
        db.close()

    @commands.command()
    @commands.has_role("Admin")
    async def name_check(self, ctx):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(SQL_QUERIES['get_allplayer'])
        for p in cursor.fetchall():
            d_id, name, _, _, _, _, _, _, _, _, _, _, _, _ = p
            member = ctx.guild.get_member(d_id) if ctx.guild else None
            if member and member.nick != name:
                try:
                    await member.edit(nick=name)
                except Exception:
                    pass
        await ctx.reply("ニックネームの同期が完了しました．")
        cursor.close()
        db.close()

async def setup(bot):
    await bot.add_cog(RegisterCog(bot))
