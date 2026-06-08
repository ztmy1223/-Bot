import os
import discord
from discord.ext import commands
from database import get_db_connection, SQL_QUERIES
from utils import plot_rate_history, ROLE_DIC, update_ranking_channels

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="stats", description="成績確認 Check your stats")
    async def stats(self, interaction: discord.Interaction, name: str = "@"):
        player = interaction.user.nick if name == "@" else name
        if not player:
            player = interaction.user.name
            
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(SQL_QUERIES['get_player_fromname'], (player,))
        result = cursor.fetchone()
        if not result:
            await interaction.response.send_message("This player is not registered", ephemeral=True)
            cursor.close()
            db.close()
            return

        await interaction.response.defer()
        
        player_id, discord_id, _, grade, hits, rate, score, r_top, r_second, r_third, r_last, m_win, m_lose, last_p = result
        
        if hits != 0:
            top = r_top / hits * 100
            second = r_second / hits * 100
            third = r_third / hits * 100
            last = r_last / hits * 100
            average = round((1*r_top + 2*r_second + 3*r_third + 4*r_last) / hits, 2)
            
            cursor.execute(SQL_QUERIES['get_player_fromid'], (m_win,))
            w = cursor.fetchone()
            mostwin = w[2] if w else "None"
            
            cursor.execute(SQL_QUERIES['get_player_fromid'], (m_lose,))
            l = cursor.fetchone()
            mostlose = l[2] if l else "None"
            
            lastplayed = f"<t:{last_p}:d>"
        else:
            rate, score, top, second, third, last = 1500, 0, 0, 0, 0, 0
            average = mostwin = mostlose = lastplayed = "None"

        rate_history = []
        cursor.execute(SQL_QUERIES['get_allmatches'])
        for match in cursor.fetchall():
            m_players = list(map(int, match[2].split()))
            if player_id in m_players:
                idx = m_players.index(player_id)
                rate_history.append(list(map(float, match[6].split()))[idx])
        rate_history.append(rate)

        role = max(13, int(rate // 100))
        role_colors = {13:0x95f068, 14:0x01a144, 15:0xf1c40f, 16:0xa84300, 17:0xeb3b9e, 18:0x1e2cf5, 19:0x6d0323}
        role_color = 0x9cacad if hits == 0 else role_colors.get(role, 0x9cacad)

        embed = discord.Embed(title=f"{player}", color=role_color)
        embed.add_field(name="Rank", value="Unranked" if hits == 0 else ROLE_DIC.get(role, "Unknown"))
        embed.add_field(name="Rate", value=str(round(rate)))
        sign = '+' if score > 0 else ""
        embed.add_field(name="Points", value=f"{sign}{score}")
        embed.add_field(name="Matches", value=str(hits))
        embed.add_field(name="Avg Rank", value=str(average))
        embed.add_field(name="Last Played", value=lastplayed)
        embed.add_field(name="1st", value=f"{round(top,1)}%" if hits!=0 else "0.0%")
        embed.add_field(name="2nd", value=f"{round(second,1)}%" if hits!=0 else "0.0%")
        embed.add_field(name="3rd", value=f"{round(third,1)}%" if hits!=0 else "0.0%")
        embed.add_field(name="4th", value=f"{round(last,1)}%" if hits!=0 else "0.0%")
        embed.add_field(name="Nemesis", value=mostwin)
        embed.add_field(name="Prey", value=mostlose)

        base_dir = os.path.dirname(os.path.dirname(__file__))
        files_to_send = []
        logo_path = os.path.join(base_dir, "rank_600", "logo.png")
        if os.path.exists(logo_path):
            file3 = discord.File(logo_path, filename="logo.png")
            embed.set_footer(text="麻雀連盟 My Mahjong League", icon_url="attachment://logo.png")
            files_to_send.append(file3)
        else:
            embed.set_footer(text="麻雀連盟 My Mahjong League")

        if hits != 0:
            plot_rate_history(rate_history)
            history_path = os.path.join(base_dir, "rate_history.png")
            if os.path.exists(history_path):
                file2 = discord.File(history_path, filename="rate_history.png")
                embed.set_image(url="attachment://rate_history.png")
                files_to_send.append(file2)
            
            rank_files = {13:"4m_novice.png", 14:"4m_adept.png", 15:"4m_expert.png", 16:"4m_master.png", 17:"4m_saint.png", 18:"4m_celestial.png", 19:"4m_tenhoui.png"}
            rank_img = rank_files.get(role, "4m_novice.png")
            rank_path = os.path.join(base_dir, "rank_600", rank_img)
            if os.path.exists(rank_path):
                file = discord.File(rank_path, filename="rank.png")
                embed.set_thumbnail(url="attachment://rank.png")
                files_to_send.append(file)
            
        await interaction.followup.send(files=files_to_send, embed=embed)
        cursor.close()
        db.close()

    @discord.app_commands.command(name="ur", description="ランキングを手動更新")
    async def ur(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await update_ranking_channels(self.bot)
        await interaction.followup.send("Successfully updated the ranking", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
