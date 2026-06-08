import discord
from discord.ext import commands
import time
import random
from database import get_db_connection, SQL_QUERIES
from utils import update_ranking_channels, ROLE_DIC, ROLE_NAME_DIC

class MatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = True

    @commands.command()
    @commands.has_any_role("Admin", "Staff")
    async def submit(self, ctx, p1: str, s1: int, p2: str, s2: int, p3: str, s3: int, p4: str, s4: int):
        if not self.cooldown:
            return
        self.cooldown = False
        t = int(time.time())
        working = await ctx.reply("Working...")

        db = get_db_connection()
        cursor = db.cursor()

        players = [p1, p2, p3, p4]
        scores = [s1, s2, s3, s4]

        if len(set(players)) != 4:
            await ctx.reply("Error: Same player names detected")
            self.cooldown = True
            cursor.close()
            db.close()
            return

        if sum(scores) != 100000:
            await ctx.reply("Error: Sum of scores is not 100000")
            self.cooldown = True
            cursor.close()
            db.close()
            return

        p_data = []
        for p in players:
            cursor.execute(SQL_QUERIES['get_player_fromname'], (p,))
            res = cursor.fetchone()
            if not res:
                await ctx.reply(f"Error: {p} is not registered")
                self.cooldown = True
                cursor.close()
                db.close()
                return
            p_data.append(res)

        ranked_indices = sorted(range(4), key=lambda k: scores[k], reverse=True)
        
        p_ids = [p_data[i][0] for i in range(4)]
        p_rates = [p_data[i][5] for i in range(4)]
        
        raw_pts = [(scores[i] - 25000) / 1000 for i in range(4)]
        
        uma_oka = [0]*4
        uma_oka[ranked_indices[0]] = 35.0
        uma_oka[ranked_indices[1]] = 5.0
        uma_oka[ranked_indices[2]] = -5.0
        uma_oka[ranked_indices[3]] = -15.0
        
        final_pts = [round(raw_pts[i] + uma_oka[i], 1) for i in range(4)]
        
        avg_rate = sum(p_rates) / 4
        rate_moves = [0.0]*4
        base_moves = [4.0, 1.0, -1.0, -4.0]
        
        for r in range(4):
            idx = ranked_indices[r]
            diff = p_rates[idx] - avg_rate
            move = base_moves[r] - (diff / 100)
            rate_moves[idx] = round(move, 2)

        str_players = " ".join(map(str, [p_data[i][0] for i in range(4)]))
        str_ranks = " ".join(map(str, [p_ids.index(p_ids[ranked_indices[r]]) for r in range(4)]))
        str_scores = " ".join(map(str, scores))
        str_points = " ".join(map(str, final_pts))
        str_rates = " ".join(map(str, [round(r) for r in p_rates]))
        str_ratemove = " ".join(map(str, rate_moves))

        cursor.execute(SQL_QUERIES['add_match'], (t, str_players, str_ranks, str_scores, str_points, str_rates, str_ratemove))

        for i in range(4):
            p_res = p_data[i]
            p_id = p_res[0]
            new_hits = p_res[4] + 1
            new_rate = p_res[5] + rate_moves[i]
            new_score = p_res[6] + final_pts[i]
            
            cursor.execute(SQL_QUERIES['update_player'], (p_id, new_hits, new_rate, new_score, t, new_hits, new_rate, new_score, t))
            
            r_pos = ranked_indices.index(i)
            if r_pos == 0: cursor.execute(SQL_QUERIES['update_top'], (p_res[7]+1, p_id))
            elif r_pos == 1: cursor.execute(SQL_QUERIES['update_second'], (p_res[8]+1, p_id))
            elif r_pos == 2: cursor.execute(SQL_QUERIES['update_third'], (p_res[9]+1, p_id))
            elif r_pos == 3: cursor.execute(SQL_QUERIES['update_last'], (p_res[10]+1, p_id))

        cursor.execute(SQL_QUERIES['get_allmatches'])
        all_matches = cursor.fetchall()
        
        for idx_p in range(4):
            cur_pid = p_ids[idx_p]
            win_count = {}
            lose_count = {}
            
            for m in all_matches:
                m_pids = list(map(int, m[2].split()))
                if cur_pid in m_pids:
                    m_ranks = list(map(int, m[3].split()))
                    cur_rank = m_ranks[m_pids.index(cur_pid)]
                    
                    for o_pid in m_pids:
                        if o_pid == cur_pid: continue
                        o_rank = m_ranks[m_pids.index(o_pid)]
                        if cur_rank > o_rank:
                            win_count[o_pid] = win_count.get(o_pid, 0) + 1
                        elif cur_rank < o_rank:
                            lose_count[o_pid] = lose_count.get(o_pid, 0) + 1
            
            m_win_id = max(win_count, key=win_count.get) if win_count else 0
            m_lose_id = max(lose_count, key=lose_count.get) if lose_count else 0
            
            cursor.execute(SQL_QUERIES['update_mostwin'], (m_win_id, cur_pid))
            cursor.execute(SQL_QUERIES['update_mostlose'], (m_lose_id, cur_pid))

        db.commit()

        announce_channel = bot.get_channel(1420112767716823131)
        embed = discord.Embed(title="【対局結果】", color=0x00ff00)
        
        medals = ["🥇", "🥈", "🥉", "📉"]
        for r in range(4):
            idx = ranked_indices[r]
            p_res = p_data[idx]
            d_id = p_res[1]
            old_rate = p_res[5]
            new_rate = old_rate + rate_moves[idx]
            
            sign = '+' if rate_moves[idx] > 0 else ""
            embed.add_field(
                name=f"{medals[r]} {r+1}位: {p_res[2]}",
                value=f"{scores[idx]}点 ({final_pts[idx]}pt)\nRate: {round(old_rate)} → {round(new_rate)} ({sign}{rate_moves[idx]})",
                inline=False
            )
            
            old_role_idx = max(13, int(old_rate // 100))
            new_role_idx = max(13, int(new_rate // 100))
            
            if old_role_idx != new_role_idx and announce_channel:
                guild = ctx.guild
                member = guild.get_member(d_id) if guild else None
                if member:
                    old_r_name = ROLE_DIC.get(old_role_idx)
                    new_r_name = ROLE_DIC.get(new_role_idx)
                    old_role_obj = discord.utils.get(guild.roles, name=old_r_name)
                    new_role_obj = discord.utils.get(guild.roles, name=new_r_name)
                    
                    if old_role_obj: await member.remove_roles(old_role_obj)
                    if new_role_obj: await member.add_roles(new_role_obj)
                    
                    if new_role_idx > old_role_idx:
                        await announce_channel.send(f"【昇格】{member.mention} が **{ROLE_NAME_DIC[new_r_name]}{new_r_name}** に昇格しました！🎉")
                    else:
                        await announce_channel.send(f"【降格】{member.mention} が **{ROLE_NAME_DIC[new_r_name]}{new_r_name}** に降格しました．")

        await ctx.reply(embed=embed)
        await update_ranking_channels(self.bot)
        await working.delete()
        
        cursor.close()
        db.close()
        self.cooldown = True

    @discord.app_commands.command(name="set", description="対局を設定し、参加者を募集します")
    async def set_match(self, interaction: discord.Interaction, date: str):
        await interaction.response.defer()
        embed = discord.Embed(title="【対局者募集】", color=0x00ff00)
        embed.add_field(name="日時/Date", value=date)
        embed.set_footer(text="React with ✅ to join, ❌ to decline")
        
        msg = await interaction.followup.send(content="<@&1420032188425965678>", embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    @discord.app_commands.context_menu(name="対局作成")
    async def create_match(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer()
        users_list = []
        for r in message.reactions:
            if r.emoji == "✅":
                async for u in r.users():
                    if not u.bot:
                        users_list.append(u)
                        
        if len(users_list) < 4:
            await interaction.followup.send(content="参加者が足りません（4人以上必要です）", ephemeral=True)
            return
            
        random.shuffle(users_list)
        
        if len(users_list) == 4:
            embed = discord.Embed(title="【対局作成（1卓）】", color=0x00ff00)
            embed.add_field(name="東家", value=users_list[0].mention, inline=False)
            embed.add_field(name="南家", value=users_list[1].mention, inline=False)
            embed.add_field(name="西家", value=users_list[2].mention, inline=False)
            embed.add_field(name="北家", value=users_list[3].mention, inline=False)
            b4 = await interaction.followup.send(embed=embed)
            
            n0 = users_list[0].nick if users_list[0].nick else users_list[0].name
            n1 = users_list[1].nick if users_list[1].nick else users_list[1].name
            n2 = users_list[2].nick if users_list[2].nick else users_list[2].name
            n3 = users_list[3].nick if users_list[3].nick else users_list[3].name
            
            await b4.reply(f"!submit\n{n0} 0\n{n1} 0\n{n2} 0\n{n3} 0")
        elif 4 < len(users_list) <= 8:
            embed = discord.Embed(title="【対局作成（2卓）】", color=0x00ff00)
            embed.add_field(name="ーー 1卓 ーー", value=" ", inline=False)
            embed.add_field(name="東家", value=users_list[0].mention, inline=False)
            embed.add_field(name="南家", value=users_list[1].mention, inline=False)
            embed.add_field(name="西家", value=users_list[2].mention, inline=False)
            embed.add_field(name="北家", value=users_list[3].mention, inline=False)
            
            embed.add_field(name="ーー 2卓 ーー", value=" ", inline=False)
            embed.add_field(name="東家", value=users_list[4].mention, inline=False)
            embed.add_field(name="南家", value=users_list[5].mention, inline=False)
            if len(users_list) > 6: embed.add_field(name="西家", value=users_list[6].mention, inline=False)
            if len(users_list) > 7: embed.add_field(name="北家", value=users_list[7].mention, inline=False)
            
            b8 = await interaction.followup.send(embed=embed)
            
            n0 = users_list[4].nick if users_list[4].nick else users_list[4].name
            n1 = users_list[5].nick if users_list[5].nick else users_list[5].name
            n2 = users_list[6].nick if users_list[6].nick else users_list[6].name
            n3 = users_list[7].nick if users_list[7].nick else users_list[7].name
            
            await b8.reply(f"!submit\n{n0} 0\n{n1} 0\n{n2} 0\n{n3} 0")
        else:
            await interaction.followup.send(content="参加者が多すぎます（最大8人まで）", ephemeral=True)

async def setup(bot):
    cog = MatchCog(bot)
    bot.tree.add_command(cog.create_match)
    await bot.add_cog(cog)
