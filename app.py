import os
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
from flask import Flask, render_template, request, jsonify

# 初始化 Flask
app = Flask(__name__,
            template_folder=os.path.join(os.getcwd(), 'templates'),
            static_folder=os.path.join(os.getcwd(), 'static'))

# 授权相关
LICENSE_FILE = "license.key"
SECRET_KEY = b'crpVRIStUGJ2B2AtARXqNyIV7RQ-pZsu_wDhlIsz5IA='
fernet = Fernet(SECRET_KEY)

# 数据库路径
db_path = os.path.join(os.getcwd(), "data.db")

# 初始化数据库
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cards TEXT,
            ez_player_score REAL,
            ez_banker_score REAL,
            ez_prediction TEXT,
            amp_player_score REAL,
            amp_banker_score REAL,
            amp_prediction TEXT,
            roadmap TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 授权检查相关函数
def read_license():
    if not os.path.exists(LICENSE_FILE):
        print("找不到授權文件，請聯繫供應商獲得授權！")
        sys.exit()

    try:
        with open(LICENSE_FILE, "rb") as f:
            encrypted_data = f.read()
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        expiration_date = datetime.strptime(decrypted_data, "%Y-%m-%d")
        return expiration_date
    except Exception as e:
        print(f"授權無效或者損壞：{e}")
        sys.exit()

def get_expiration_date():
    expiration_date = read_license()
    return expiration_date.strftime("%Y-%m-%d")

def check_expiration():
    expiration_date = read_license()
    if datetime.now() > expiration_date:
        print("授權已過期，請聯繫供應商獲取新的授權！")
        sys.exit()
    print(f"授權有效，將於 {expiration_date.date()} 到期。")

# 演算法逻辑
ez_card_values = {
    '1': 1, '2': 1, '3': 1,
    '4': 2,
    '5': -1, '6': -2, '7': -1, '8': -1,
    '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0,
    'Z': None  # 未补牌
}

amp_card_values = {
    '1': 1, '2': 1, '3': 1,
    '4': 2, '5': 2,
    '6': 3, '7': 3, '8': 3,
    '9': 4,
    '10': 0, 'J': 0, 'Q': 0, 'K': 0,
    'Z': None
}

roadmap = []

@app.route("/")
def index():
    expiration_date = get_expiration_date()
    return render_template("index.html", expiration_date=expiration_date)

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    cards = data.get("cards")  # 获取牌组
    if len(cards) != 6:
        return jsonify({"error": "请输入正确的 6 张牌（格式如：4 7 8 J K Z）。"}), 400

    try:
        ez_converted_cards = [ez_card_values[card.upper()] for card in cards]
        amp_converted_cards = [amp_card_values[card.upper()] for card in cards]
    except KeyError:
        return jsonify({"error": "输入的牌中包含无效的数值！请检查"}), 400

    # EZ演算法计算
    ez_player_score = sum(ez_converted_cards[:2]) + (ez_converted_cards[4] or 0)
    ez_banker_score = sum(ez_converted_cards[2:4]) + (ez_converted_cards[5] or 0)
    ez_total_score = ez_banker_score - ez_player_score  # 计算总分差
    ez_prediction = "莊" if ez_total_score > 0 else "閒"  # 根据正负判断

    # 计算胜率
    ez_player_rate = abs(ez_player_score) / (abs(ez_player_score) + abs(ez_banker_score)) * 100 if (ez_player_score + ez_banker_score) != 0 else 50
    ez_banker_rate = 100 - ez_player_rate

    # AMP演算法计算
    def calculate_amp_points(cards, third_card):
        total = sum(cards[:2])
        if third_card is not None:
            total += third_card
        return total

    amp_player_score = calculate_amp_points(amp_converted_cards[:2], amp_converted_cards[4])
    amp_banker_score = calculate_amp_points(amp_converted_cards[2:4], amp_converted_cards[5])
    amp_prediction = "閒" if amp_player_score > amp_banker_score else "莊"

    amp_player_rate = abs(amp_player_score) / (abs(amp_player_score) + abs(amp_banker_score)) * 100 if (amp_player_score + amp_banker_score) != 0 else 50
    amp_banker_rate = 100 - amp_player_rate

    # 保存到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (timestamp, cards, ez_player_score, ez_banker_score, ez_prediction,
                                 amp_player_score, amp_banker_score, amp_prediction, roadmap)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        " ".join(cards),
        ez_player_score,
        ez_banker_score,
        ez_prediction,
        amp_player_score,
        amp_banker_score,
        amp_prediction,
        str(roadmap)
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "ez_player_score": ez_player_score,
        "ez_banker_score": ez_banker_score,
        "ez_prediction": ez_prediction,
        "ez_player_rate": round(ez_player_rate, 2),
        "ez_banker_rate": round(ez_banker_rate, 2),
        "amp_player_score": amp_player_score,
        "amp_banker_score": amp_banker_score,
        "amp_prediction": amp_prediction,
        "amp_player_rate": round(amp_player_rate, 2),
        "amp_banker_rate": round(amp_banker_rate, 2)
    })

if __name__ == "__main__":
    check_expiration()
    from waitress import serve
    serve(app, host="127.0.0.1", port=5000)
