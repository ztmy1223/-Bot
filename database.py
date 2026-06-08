import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """MySQLへの接続を確立して返す"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "sql12.freesqldatabase.com"),
        user=os.getenv("DB_USER", "sql12620828"),
        password=os.getenv("DB_PASSWORD", "YOUR_DB_PASSWORD_HERE"),
        database=os.getenv("DB_NAME", "sql12620828"),
        use_pure=True
    )

# SQLクエリの定数化 (テーブル名を mybot_ に変更して匿名化)
SQL_QUERIES = {
    'add_player': 'INSERT INTO mybot_players (discordID, name, grade) VALUES (%s,%s,%s)',
    'get_player': 'SELECT * FROM mybot_players WHERE discordID = %s;',
    'get_player_fromname': 'SELECT * FROM mybot_players WHERE name = %s;',
    'get_player_fromid': 'SELECT * FROM mybot_players WHERE playerID = %s;',
    'delete_player': 'DELETE FROM mybot_players WHERE name = %s;',
    'update_player': 'INSERT INTO mybot_players (playerID, hits, rate, score, lastplayed) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE hits=%s, rate=%s, score=%s, lastplayed=%s;',
    'update_top': 'UPDATE mybot_players SET top=%s WHERE playerID=%s;',
    'update_second': 'UPDATE mybot_players SET second=%s WHERE playerID=%s;',
    'update_third': 'UPDATE mybot_players SET third=%s WHERE playerID=%s;',
    'update_last': 'UPDATE mybot_players SET last=%s WHERE playerID=%s;',
    'update_mostwin': 'UPDATE mybot_players SET mostwin=%s WHERE playerID=%s;',
    'update_mostlose': 'UPDATE mybot_players SET mostlose=%s WHERE playerID=%s;',
    'get_allplayer': 'SELECT * FROM mybot_players',
    'add_match': 'INSERT INTO mybot_matches (date, players, ranks, scores, points, rates, ratemove) VALUES (%s,%s,%s,%s,%s,%s,%s)',
    'get_allmatches': 'SELECT * FROM mybot_matches',
    'update_name': 'UPDATE mybot_players SET name=%s WHERE discordID=%s;',
    'update_grade': 'UPDATE mybot_players SET grade=%s WHERE discordID=%s;'
}
