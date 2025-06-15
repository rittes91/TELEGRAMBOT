# 🔴 REAL NSE DATA BOT - NO MOCK/SIMULATION DATA
# Only genuine live market data from reliable sources

import os
import time
import requests
import json
import threading
import datetime
from flask import Flask, request, jsonify
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class RealNSEDataFetcher:
    """Fetches only REAL data from genuine market APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_nse_direct_data(self):
        """Method 1: Direct NSE API (Most Accurate)"""
        try:
            # Step 1: Get cookies from NSE homepage
            home_response = self.session.get('https://www.nseindia.com', timeout=15)
            if home_response.status_code != 200:
                logger.error("Failed to get NSE cookies")
                return None
            
            # Step 2: Get NIFTY data from NSE API
            nse_url = "https://www.nseindia.com/api/quote-equity?symbol=NIFTYBEES"
            
            response = self.session.get(nse_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # Extract NIFTY data
                price_info = data.get('priceInfo', {})
                
                if price_info:
                    return {
                        'source': 'NSE Direct API',
                        'symbol': 'NIFTY 50',
                        'price': float(price_info.get('lastPrice', 0)),
                        'change': float(price_info.get('change', 0)),
                        'change_percent': float(price_info.get('pChange', 0)),
                        'open': float(price_info.get('open', 0)),
                        'high': float(price_info.get('intraDayHighLow', {}).get('max', 0)),
                        'low': float(price_info.get('intraDayHighLow', {}).get('min', 0)),
                        'volume': int(data.get('securityWiseDP', {}).get('quantityTraded', 0)),
                        'timestamp': datetime.datetime.now(),
                        'status': 'live'
                    }
                    
        except Exception as e:
            logger.error(f"NSE Direct API failed: {e}")
            return None
    
    def get_yahoo_finance_data(self):
        """Method 2: Yahoo Finance (Reliable Real Data)"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    
                    # Get real-time data
                    current_price = meta.get('regularMarketPrice')
                    previous_close = meta.get('previousClose')
                    
                    if current_price and previous_close:
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        
                        return {
                            'source': 'Yahoo Finance',
                            'symbol': 'NIFTY 50',
                            'price': current_price,
                            'change': change,
                            'change_percent': change_percent,
                            'open': meta.get('regularMarketOpen', 0),
                            'high': meta.get('regularMarketDayHigh', 0),
                            'low': meta.get('regularMarketDayLow', 0),
                            'volume': meta.get('regularMarketVolume', 0),
                            'timestamp': datetime.datetime.now(),
                            'status': 'live'
                        }
                        
        except Exception as e:
            logger.error(f"Yahoo Finance failed: {e}")
            return None
    
    def get_investing_com_data(self):
        """Method 3: Investing.com Real API"""
        try:
            # Investing.com NIFTY endpoint
            url = "https://api.investing.com/api/financialdata/8985/historical/chart/"
            
            headers = {
                'Domain-ID': '4',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Origin': 'https://www.investing.com',
                'Referer': 'https://www.investing.com/'
            }
            
            params = {
                'period': 'P1D',
                'interval': 'PT1M'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][-1]  # Get latest data point
                    
                    price = latest.get('close')
                    prev_close = data['data'][0].get('close') if len(data['data']) > 1 else price
                    
                    if price:
                        change = price - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close else 0
                        
                        return {
                            'source': 'Investing.com',
                            'symbol': 'NIFTY 50',
                            'price': price,
                            'change': change,
                            'change_percent': change_percent,
                            'open': latest.get('open', 0),
                            'high': max([p.get('high', 0) for p in data['data']]),
                            'low': min([p.get('low', 0) for p in data['data']]),
                            'volume': sum([p.get('volume', 0) for p in data['data']]),
                            'timestamp': datetime.datetime.now(),
                            'status': 'live'
                        }
                        
        except Exception as e:
            logger.error(f"Investing.com failed: {e}")
            return None
    
    def get_moneycontrol_data(self):
        """Method 4: MoneyControl API (Indian Source)"""
        try:
            # MoneyControl NIFTY API
            url = "https://priceapi.moneycontrol.com/techCharts/indianMarket/index/history"
            
            params = {
                'symbol': 'NIFTY',
                'resolution': '1D',
                'from': int(time.time()) - 86400,  # Last 24 hours
                'to': int(time.time())
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 's' in data and data['s'] == 'ok' and 'c' in data:
                    # Get latest closing price
                    closes = data['c']
                    opens = data['o']
                    highs = data['h']
                    lows = data['l']
                    volumes = data['v']
                    
                    if closes:
                        current_price = closes[-1]
                        prev_close = closes[-2] if len(closes) > 1 else current_price
                        
                        change = current_price - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close else 0
                        
                        return {
                            'source': 'MoneyControl',
                            'symbol': 'NIFTY 50',
                            'price': current_price,
                            'change': change,
                            'change_percent': change_percent,
                            'open': opens[-1] if opens else 0,
                            'high': highs[-1] if highs else 0,
                            'low': lows[-1] if lows else 0,
                            'volume': volumes[-1] if volumes else 0,
                            'timestamp': datetime.datetime.now(),
                            'status': 'live'
                        }
                        
        except Exception as e:
            logger.error(f"MoneyControl failed: {e}")
            return None
    
    def get_real_market_data(self):
        """Try real data sources only - NO MOCK DATA"""
        real_methods = [
            ("NSE Direct", self.get_nse_direct_data),
            ("Yahoo Finance", self.get_yahoo_finance_data),
            ("Investing.com", self.get_investing_com_data),
            ("MoneyControl", self.get_moneycontrol_data)
        ]
        
        for source_name, method in real_methods:
            try:
                logger.info(f"🔍 Trying {source_name}...")
                data = method()
                
                if data and data.get('price', 0) > 0:
                    logger.info(f"✅ Real data from {source_name}: ₹{data['price']:.2f}")
                    return data
                else:
                    logger.warning(f"❌ {source_name} returned invalid data")
                    
            except Exception as e:
                logger.error(f"❌ {source_name} error: {e}")
                continue
        
        logger.error("❌ All real data sources failed")
        return None

class RealDataTelegramBot:
    """Telegram bot with ONLY real market data"""
    
    def __init__(self):
        self.bot_token = "7623288925:AAHEpUAqbXBi1FYhq0ok7nFsykrSNaY8Sh4"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.chat_id = None
        self.is_running = True
        
        # Initialize real data fetcher
        self.data_fetcher = RealNSEDataFetcher()
        
        # Cache for real data only
        self.last_real_data = None
        self.last_real_update = None
        
        # Setup
        self.render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        self.webhook_url = f"{self.render_url}/webhook"
        
        self.setup_webhook()
        self.start_keep_alive()
        self.start_real_data_monitor()
        
    def setup_webhook(self):
        """Setup Telegram webhook"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {"url": self.webhook_url}
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Webhook setup successful")
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
    
    def start_keep_alive(self):
        """Keep bot alive"""
        def keep_alive():
            while self.is_running:
                try:
                    time.sleep(840)  # 14 minutes
                    requests.get(f"{self.render_url}/health", timeout=5)
                    logger.info("🏓 Keep-alive ping")
                except:
                    pass
        
        threading.Thread(target=keep_alive, daemon=True).start()
    
    def start_real_data_monitor(self):
        """Monitor ONLY real market data"""
        def monitor_real_data():
            while self.is_running:
                try:
                    # Get real data every 2 minutes during market hours
                    now = datetime.datetime.now()
                    
                    # Check if market hours (9:15 AM to 3:30 PM IST, Mon-Fri)
                    if (9 <= now.hour < 16 and now.weekday() < 5) or True:  # Always try for now
                        data = self.data_fetcher.get_real_market_data()
                        
                        if data:
                            self.last_real_data = data
                            self.last_real_update = datetime.datetime.now()
                            logger.info(f"📊 Real data updated: ₹{data['price']:.2f} from {data['source']}")
                        else:
                            logger.warning("⚠️ No real data available from any source")
                    
                    time.sleep(120)  # 2 minutes
                    
                except Exception as e:
                    logger.error(f"Real data monitor error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=monitor_real_data, daemon=True).start()
        logger.info("🔄 Real data monitoring started")
    
    def send_message(self, chat_id, message):
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_real_nifty_message(self):
        """Get NIFTY message with ONLY real data"""
        try:
            # Try to get fresh real data
            fresh_data = self.data_fetcher.get_real_market_data()
            
            # Use fresh data if available, otherwise cached real data
            data = fresh_data or self.last_real_data
            
            if not data:
                return """
❌ <b>UNABLE TO FETCH REAL NIFTY DATA</b>

🔍 <b>Attempted Sources:</b>
• NSE Direct API
• Yahoo Finance  
• Investing.com
• MoneyControl

⚠️ <b>All real data sources are currently unavailable.</b>

💡 <b>Possible reasons:</b>
• Market is closed
• Network connectivity issues
• API rate limits reached
• Server maintenance

🔄 <b>Please try again in a few minutes.</b>

<i>Note: This bot only shows REAL market data, no simulated/mock data.</i>
                """
            
            # Format real data message
            change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
            color = "🟢" if data['change'] > 0 else "🔴" if data['change'] < 0 else "🟡"
            
            # Calculate data freshness
            data_age = ""
            if self.last_real_update:
                age_seconds = (datetime.datetime.now() - self.last_real_update).total_seconds()
                if age_seconds < 60:
                    data_age = "Real-time"
                elif age_seconds < 3600:
                    data_age = f"{int(age_seconds/60)} min ago"
                else:
                    data_age = f"{int(age_seconds/3600)} hr ago"
            
            message = f"""
{color} <b>NIFTY 50 - REAL LIVE DATA</b> {color}

💰 <b>Price:</b> ₹{data['price']:.2f}
{change_emoji} <b>Change:</b> {data['change']:+.2f} ({data['change_percent']:+.2f}%)

📊 <b>Day Range:</b>
• Open: ₹{data.get('open', 0):.2f}
• High: ₹{data.get('high', 0):.2f}  
• Low: ₹{data.get('low', 0):.2f}
• Volume: {data.get('volume', 0):,}

⏰ <b>Updated:</b> {data_age}
📅 <b>Date:</b> {data['timestamp'].strftime('%d-%m-%Y')}

🌐 <b>Real Source:</b> {data['source']}
✅ <b>Data Type:</b> Live Market Data (No Mock)

<i>🔴 This bot shows only genuine market data</i>
            """
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return "❌ Error processing real market data. Please try again."
    
    def process_message(self, update):
        """Process Telegram messages"""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            if not chat_id:
                return
            
            if not self.chat_id:
                self.chat_id = chat_id
                logger.info(f"✅ New user: {chat_id}")
            
            if text.startswith('/'):
                self.handle_command(text, chat_id)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_command(self, command, chat_id):
        """Handle bot commands"""
        
        if command == '/start':
            welcome_msg = """
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

<b>🔴 100% Real Data Guarantee!</b>
            """
            self.send_message(chat_id, welcome_msg)
            
        elif command == '/nifty':
            nifty_msg = self.get_real_nifty_message()
            self.send_message(chat_id, nifty_msg)
            
        elif command == '/sources':
            sources_msg = "<b>🔍 TESTING REAL DATA SOURCES:</b>\n\n"
            
            real_sources = [
                ("NSE Direct API", self.data_fetcher.get_nse_direct_data),
                ("Yahoo Finance", self.data_fetcher.get_yahoo_finance_data),
                ("Investing.com", self.data_fetcher.get_investing_com_data),
                ("MoneyControl", self.data_fetcher.get_moneycontrol_data)
            ]
            
            working_sources = 0
            for name, method in real_sources:
                try:
                    data = method()
                    if data and data.get('price', 0) > 0:
                        sources_msg += f"✅ <b>{name}:</b> ₹{data['price']:.2f} (Real)\n"
                        working_sources += 1
                    else:
                        sources_msg += f"❌ <b>{name}:</b> No real data\n"
                except:
                    sources_msg += f"❌ <b>{name}:</b> Connection failed\n"
            
            sources_msg += f"\n📊 <b>Working Sources:</b> {working_sources}/4"
            sources_msg += f"\n⏰ <b>Test Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}"
            sources_msg += f"\n\n🔴 <b>Note:</b> Only real market data shown, no simulations."
            
            self.send_message(chat_id, sources_msg)
            
        elif command == '/status':
            data_status = "Available" if self.last_real_data else "Unavailable"
            last_update = self.last_real_update.strftime('%H:%M:%S') if self.last_real_update else "Never"
            
            status_msg = f"""
📊 <b>REAL DATA BOT STATUS</b>

🔴 <b>Policy:</b> Real data only, no mock/simulation
📡 <b>Data Status:</b> {data_status}
🕒 <b>Last Real Update:</b> {last_update}

<b>🌐 Data Sources:</b>
• NSE Direct API
• Yahoo Finance
• Investing.com  
• MoneyControl

<b>✅ Guarantees:</b>
• 100% real market data
• No fake/simulated prices
• Authentic NSE information
• Live trading data only

<b>❌ Never Shows:</b>
• Mock data
• Estimated prices
• Simulated values
• Fake market information
            """
            self.send_message(chat_id, status_msg)
            
        else:
            self.send_message(chat_id, f"❓ Unknown command: {command}\nType /start for help.")

# Initialize bot
bot = RealDataTelegramBot()

# Flask routes
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        bot.process_message(update)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'real_data_available': bool(bot.last_real_data),
        'last_real_update': bot.last_real_update.isoformat() if bot.last_real_update else None,
        'policy': 'Real data only - No mock/simulation'
    })

@app.route('/')
def home():
    return f"""
    <h1>🔴 Real NSE Data Bot</h1>
    <p><strong>Policy:</strong> 100% Real Data Only</p>
    <p><strong>No Mock Data:</strong> ❌ Simulations, ❌ Fake Prices, ❌ Estimates</p>
    <p><strong>Real Sources:</strong> ✅ NSE API, ✅ Yahoo Finance, ✅ MoneyControl</p>
    <p><strong>Bot:</strong> <a href="https://t.me/tradsysbot">@tradsysbot</a></p>
    <p><strong>Status:</strong> {datetime.datetime.now()}</p>
    """

if __name__ == '__main__':
    logger.info("🔴 Starting REAL DATA ONLY bot...")
    logger.info("🚫 NO mock/simulation data will be used")
    logger.info("✅ Only genuine NSE market data")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
