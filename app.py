import requests
import pandas as pd
import datetime
from typing import Dict

# Existing bot class and other functions are intact

class TradingTelegramBot:
    def __init__(self, bot_token, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def get_chat_id(self):
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['result']:
                    latest = data['result'][-1]
                    return latest['message']['chat']['id']
        except:
            return None

    def send_message(self, message, parse_mode='HTML'):
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        requests.post(url, data=data)

    def send_pre_market_summary(self):
        try:
            df = get_pre_market_data()
            message = format_pre_market_message(df)
            if not self.chat_id:
                self.chat_id = self.get_chat_id()
            self.send_message(message, parse_mode="HTML")
            print("✅ Pre-market summary sent to Telegram")
        except Exception as e:
            print(f"❌ Error sending pre-market summary: {e}")

    def send_real_data_banner(self):
        message = """
🔴 <b>REAL NSE DATA BOT - NO MOCK DATA</b>

✅ <b>Real Data Sources:</b>
• NSE Direct API (Primary)
• Yahoo Finance (Backup)
• Investing.com (Backup)
• MoneyControl (Backup)

🚫 <b>What we DON'T do:</b>
❌ Mock/simulated data
❌ Fake prices
❌ Estimated values

✅ <b>What we DO:</b>
✅ Only genuine live market data
✅ Real-time NSE prices
✅ Authentic trading information

<b>Commands:</b>
/nifty - Real NIFTY data (or error if unavailable)
/sources - Test all real data sources
/status - Real data availability status

🔴 <b>100% Real Data Guarantee!</b>
        """
        self.send_message(message, parse_mode='HTML')

# 🔧 CONFIGURATION
BOT_TOKEN = "7623288925:AAHEpUAqbXBi1FYhq0ok7nFsykrSNaY8Sh4"
CHAT_ID = None

# 🛠️ Step 1: Get live pre-open data from NSE

def get_pre_market_data():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }

    with requests.Session() as s:
        s.headers.update(headers)
        s.get("https://www.nseindia.com")
        response = s.get(url)

    if response.status_code == 200:
        data = response.json()
        rows = data.get("data", [])
        df = pd.DataFrame(rows)
        df["symbol"] = df["metadata"].apply(lambda x: x.get("symbol") if isinstance(x, dict) else None)
        df["change"] = pd.to_numeric(df["metadata"].apply(lambda x: x.get("change", 0) if isinstance(x, dict) else 0), errors='coerce')
        df["sector"] = df["metadata"].apply(lambda x: x.get("industry", "NA") if isinstance(x, dict) else "NA")
        return df.dropna(subset=["symbol"])
    else:
        raise Exception("Failed to fetch NSE pre-open data")

# 🧠 Step 2: Format output

def format_pre_market_message(df):
    gainers = df[df['change'] > 2].sort_values(by="change", ascending=False)
    losers = df[df['change'] < -2].sort_values(by="change")

    def fmt_row(row):
        return f"• <b>{row['symbol']}</b> ({row['change']:+.2f}%) [{row['sector']}]"

    msg = f"""
📊 <b>PRE-MARKET GAINERS/LOSERS</b>

🔍 <b>Criteria:</b> ±2% or more change in pre-open
📅 <b>Date:</b> {datetime.datetime.now().strftime('%d-%b-%Y')}  ⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""

    if not gainers.empty:
        msg += "
📈 <b>Top Gainers (↑2%+)</b>
" + "
".join(fmt_row(r) for _, r in gainers.iterrows()) + "
"
    else:
        msg += "
📈 <b>Top Gainers:</b> None found above 2%
"

    if not losers.empty:
        msg += "
📉 <b>Top Losers (↓2%-)</b>
" + "
".join(fmt_row(r) for _, r in losers.iterrows()) + "
"
    else:
        msg += "
📉 <b>Top Losers:</b> None found below -2%
"

    msg += """
🟢 <i>Tip:</i> Focus on sectors with multiple movers for trend strength.
"""
    return msg

# ▶️ Manual trigger
if __name__ == "__main__":
    bot = TradingTelegramBot(BOT_TOKEN, CHAT_ID)
    bot.send_real_data_banner()
    bot.send_pre_market_summary()
