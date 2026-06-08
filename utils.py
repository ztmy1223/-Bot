import os
import time
import numpy as np
import matplotlib.pyplot as plt
from database import get_db_connection, SQL_QUERIES

def plot_rate_history(rate_history):
    x = np.arange(0, len(rate_history))
    y = rate_history
    bg_color = '#0b2340'
    axes_bg = '#0b2340'
    
    band1_max = 1399
    band2_min, band2_max = 1400, 1499
    band3_min, band3_max = 1500, 1599
    band4_min, band4_max = 1600, 1699
    band5_min, band5_max = 1700, 1799
    band6_min, band6_max = 1800, 1899

    fig, ax = plt.subplots(figsize=(6, 4), facecolor=bg_color)
    ax.set_facecolor(axes_bg)
    
    ax.axhspan(-1e9, band1_max, facecolor='#95f068', alpha=0.35)
    ax.axhspan(band2_min, band2_max, facecolor='#01a144', alpha=0.35)
    ax.axhspan(band3_min, band3_max, facecolor='#f1c40f', alpha=0.35)
    ax.axhspan(band4_min, band4_max, facecolor='#a84300', alpha=0.25)
    ax.axhspan(band5_min, band5_max, facecolor='#eb3b9e', alpha=0.25)
    ax.axhspan(band6_min, band6_max, facecolor='#1e2cf5', alpha=0.25)
    ax.axhspan(1900, 1e9, facecolor='#6d0323', alpha=0.18)
    
    ax.plot(x, y, color='white', linewidth=1.8, zorder=5)

    def color_for_mmr(mmr):
        if mmr <= band1_max: return '#95f068'
        if band2_min <= mmr <= band2_max: return '#01a144'
        if band3_min <= mmr <= band3_max: return '#f1c40f'
        if band4_min <= mmr <= band4_max: return '#a84300'
        if band5_min <= mmr <= band5_max: return '#eb3b9e'
        if band6_min <= mmr <= band6_max: return '#1e2cf5'
        return '#6d0323'

    point_colors = [color_for_mmr(round(val)) for val in y]
    ax.scatter(x, y, c=point_colors, s=20, edgecolors='none', zorder=6)
    ax.grid(which='major', linestyle=':', color='white', alpha=0.5)
    ax.tick_params(colors='white', labelcolor='white')
    ax.set_ylabel('Rate', color='white')
    if len(x) > 0:
        ax.set_xlim(min(x), max(x))
    ax.set_ylim(min(y) - 50, max(y) + 50)
    
    for ytick in ax.get_yticks():
        ax.axhline(ytick, color='white', linestyle=':', linewidth=0.6, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), 'rate_history.png')
    plt.savefig(output_path, dpi=150, facecolor=bg_color)
    plt.close()

async def update_ranking_channels(bot):
    """チャンネルのランキングメッセージを更新する共通関数"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(SQL_QUERIES['get_allplayer'])
        allplayers = cursor.fetchall()
        
        rate_list = [(p[2], p[5], p[4]) for p in allplayers]
        score_list = [(p[2], p[6], p[4]) for p in allplayers]
        
        rate_list.sort(key=lambda x: x[1], reverse=True)
        score_list.sort(key=lambda x: x[1], reverse=True)
        
        t = time.time()
        
        # Rateランキング更新
        content = "【Rate】\n"
        r = 1
        for name, rate, hits in rate_list:
            if hits != 0:
                content += f"\n{r}位: {round(rate)} {name}"
                r += 1
        channel = bot.get_channel(1420112767716823131)
        if channel:
            message = await channel.fetch_message(1421729021619601460)
            if message:
                await message.edit(content=content + f"\n\nLast updated: <t:{int(t)}:F>")
        
        # Pointsランキング更新
        content2 = "【Points】\n"
        r = 1
        for name, score, hits in score_list:
            if hits != 0:
                sign = '+' if score > 0 else ""
                content2 += f"\n{r}位: {sign}{score} {name}"
                r += 1
        channel2 = bot.get_channel(1420112767716823131)
        if channel2:
            message2 = await channel2.fetch_message(1421871497047445585)
            if message2:
                await message2.edit(content=content2 + f"\n\nLast updated: <t:{int(t)}:F>")
        
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error updating ranking channels: {e}")

# 辞書データの共通化
ROLE_DIC = {13: "初心", 14: "雀士", 15: "雀傑", 16: "雀豪", 17: "雀聖", 18: "魂天", 19: "天鳳位"}
ROLE_NAME_DIC = {
    "初心": "<:novice:1420799354750636133>", 
    "雀士": "<:adept:1420799239297962138>", 
    "雀傑": "<:expert:1420799273015967825>", 
    "雀豪": "<:master:1420799288287690797>", 
    "雀聖": "<:saint:1420799208881127524>", 
    "魂天": "<:celestial:1420799254657499146>", 
    "天鳳位": "<:tenhoui:1420810547791790170>"
}
GRADE_DIC = {1: "B4", 2: "M1", 3: "M2", 4: "D1", 5: "D2", 6: "D3", 7: "留学生", 9: "その他", 10: "先生"}
