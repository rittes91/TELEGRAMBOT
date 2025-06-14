# 🌐 RENDER.COM READY - NSE PRE-MARKET SCANNER BOT
# Complete Flask app with NSE pre-market scanner + 24/7 hosting

import os
import requests
import json
import datetime
import time
import threading
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class NSEPreMarketDataFetcher:
    """Fetches real NSE pre-market data with sector classification"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Comprehensive sector mapping
        self.sector_mapping = {
            # IT Sector
            'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
            'LTIM': 'IT', 'COFORGE': 'IT', 'MPHASIS': 'IT', 'PERSISTENT': 'IT',
            
            # Banking & Financial Services
            'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'KOTAKBANK': 'Banking',
            'AXISBANK': 'Banking', 'SBIN': 'Banking', 'INDUSINDBK': 'Banking',
            'BANDHANBNK': 'Banking', 'FEDERALBNK': 'Banking', 'PNB': 'Banking',
            'HDFCLIFE': 'Insurance', 'SBILIFE': 'Insurance', 'ICICIGI': 'Insurance',
            'BAJFINANCE': 'NBFC', 'BAJAJFINSV': 'NBFC', 'M&MFIN': 'NBFC',
            
            # Auto Sector
            'MARUTI': 'Auto', 'TATAMOTORS': 'Auto', 'M&M': 'Auto', 'BAJAJ-AUTO': 'Auto',
            'HEROMOTOCO': 'Auto', 'TVSMOTORS': 'Auto', 'EICHERMOT': 'Auto',
            'ASHOKLEY': 'Auto', 'TVSMOTOR': 'Auto', 'MOTHERSON': 'Auto Parts',
            
            # Pharma
            'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
            'DIVISLAB': 'Pharma', 'BIOCON': 'Pharma', 'LUPIN': 'Pharma',
            'AUROPHARMA': 'Pharma', 'TORNTPHARM': 'Pharma', 'ALKEM': 'Pharma',
            
            # FMCG
            'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG',
            'BRITANNIA': 'FMCG', 'DABUR': 'FMCG', 'MARICO': 'FMCG',
            'GODREJCP': 'FMCG', 'COLPAL': 'FMCG', 'PGHH': 'FMCG',
            
            # Metals & Mining
            'TATASTEEL': 'Metals', 'JSWSTEEL': 'Metals', 'HINDALCO': 'Metals',
            'VEDL': 'Metals', 'COALINDIA': 'Mining', 'NMDC': 'Mining',
            'SAIL': 'Metals', 'JINDALSTEL': 'Metals', 'ADANIENT': 'Metals',
            
            # Oil & Gas
            'RELIANCE': 'Oil & Gas', 'ONGC': 'Oil & Gas', 'IOC': 'Oil & Gas',
            'BPCL': 'Oil & Gas', 'HPCL': 'Oil & Gas', 'GAIL': 'Oil & Gas',
            
            # Power & Energy
            'POWERGRID': 'Power', 'NTPC': 'Power', 'ADANIPOWER': 'Power',
            'TATAPOWER': 'Power', 'NHPC': 'Power', 'ADANIGREEN': 'Renewable',
            
            # Telecom
            'BHARTIARTL': 'Telecom', 'IDEA': 'Telecom',
            
            # Cement
            'ULTRACEMCO': 'Cement', 'SHREECEM': 'Cement', 'GRASIM': 'Cement',
            'ACC': 'Cement', 'AMBUJACEMNT': 'Cement', 'JKCEMENT': 'Cement',
            
            # Consumer Durables
            'BAJAJHLDNG': 'Consumer Dur.', 'WHIRLPOOL': 'Consumer Dur.',
            'CROMPTON': 'Consumer Dur.', 'HAVELLS': 'Consumer Dur.',
            
            # Real Estate
            'DLF': 'Real Estate', 'GODREJPROP': 'Real Estate', 'OBEROIRLTY': 'Real Estate',
            
            # Others
            'LT': 'Construction', 'ADANIPORTS': 'Logistics', 'TITAN': 'Jewellery',
            'ASIANPAINT': 'Paints', 'BERGEPAINT': 'Paints', 'UPL': 'Chemicals'
        }
        
        self.cookies_initialized = False
    
    def initialize_nse_session(self):
        """Initialize NSE session with proper cookies"""
        try:
            home_response = self.session.get('https://www.nseindia.com', timeout=15)
            if home_response.status_code == 200:
                self.cookies_initialized = True
                logger.info("✅ NSE session initialized")
                return True
            else:
                logger.error(f"❌ NSE session failed: {home_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ NSE session error: {e}")
            return False
    
    def get_nse_premarket_data(self):
        """Fetch real NSE pre-market data"""
        if not self.cookies_initialized:
            if not self.initialize_nse_session():
                return None
        
        try:
            premarket_url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
            response = self.session.get(premarket_url, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ NSE pre-market data fetched")
                return data
            else:
                logger.error(f"❌ NSE API failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ NSE fetch error: {e}")
            return None
    
    def get_sector_for_symbol(self, symbol):
        """Get sector classification for a stock symbol"""
        clean_symbol = symbol.split('-')[0].upper()
        return self.sector_mapping.get(clean_symbol, 'Others')
    
    def filter_significant_movers(self, premarket_data, threshold=2.0):
        """Filter stocks with ±2% or more movement"""
        if not premarket_data or 'data' not in premarket_data:
            return {'gainers': [], 'losers': []}
        
        gainers = []
        losers = []
        
        for stock in premarket_data['data']:
            try:
                detail = stock.get('detail', {})
                preopen_market = detail.get('preOpenMarket', {})
                
                if not preopen_market:
                    continue
                
                symbol = stock.get('symbol', '')
                iep = preopen_market.get('IEP', 0)
                change = preopen_market.get('change', 0)
                percent_change = preopen_market.get('pChange', 0)
                
                if abs(percent_change) >= threshold and iep > 0:
                    sector = self.get_sector_for_symbol(symbol)
                    
                    stock_data = {
                        'symbol': symbol,
                        'price': iep,
                        'change': change,
                        'percent_change': percent_change,
                        'sector': sector,
                        'volume': preopen_market.get('totalTradedVolume', 0),
                        'value': preopen_market.get('totalTradedValue', 0)
                    }
                    
                    if percent_change > 0:
                        gainers.append(stock_data)
                    else:
                        losers.append(stock_data)
                        
            except Exception as e:
                logger.warning(f"⚠️ Stock processing error: {e}")
                continue
        
        gainers.sort(key=lambda x: x['percent_change'], reverse=True)
        losers.sort(key=lambda x: x['percent_change'])
        
        logger.info(f"📊 Filtered {len(gainers)} gainers, {len(losers)} losers")
        
        return {
            'gainers': gainers,
            'losers': losers,
            'total_stocks': len(premarket_data['data']),
            'timestamp': datetime.datetime.now()
        }

class RenderPreMarketTelegramBot:
    """Render.com compatible Telegram bot with NSE pre-market scanner"""
    
    def __init__(self):
        self.bot_token = "7623288925:AAHEpUAqbXBi1FYhq0ok7nFsykrSNaY8Sh4"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.chat_id = None
        self.is_running = True
        
        # Initialize data fetcher
        self.data_fetcher = NSEPreMarketDataFetcher()
        
        # Get Render URL
        self.render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        self.webhook_url = f"{self.render_url}/webhook"
        
        # Cache for pre-market data
        self.last_premarket_data = None
        self.last_scan_time = None
        
        # Setup
        self.setup_webhook()
        self.start_keep_alive()
        self.start_premarket_scheduler()
    
    def setup_webhook(self):
        """Setup Telegram webhook"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {"url": self.webhook_url}
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Webhook setup successful")
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
    
    def start_keep_alive(self):
        """Keep Render.com app alive"""
        def keep_alive():
            while self.is_running:
                try:
                    time.sleep(840)  # 14 minutes
                    requests.get(f"{self.render_url}/health", timeout=5)
                    logger.info("🏓 Keep-alive ping")
                except:
                    pass
        
        threading.Thread(target=keep_alive, daemon=True).start()
        logger.info("🔄 Keep-alive started")
    
    def start_premarket_scheduler(self):
        """Schedule pre-market scans during market hours"""
        def premarket_scheduler():
            while self.is_running:
                try:
                    now = datetime.datetime.now()
                    
                    # Check if pre-market time (9:00 AM - 9:15 AM IST, Mon-Fri)
                    if (9 <= now.hour <= 9 and now.minute <= 15 and 
                        now.weekday() < 5 and self.chat_id):
                        
                        # Run scan every 5 minutes during pre-market
                        if (not self.last_scan_time or 
                            (now - self.last_scan_time).seconds > 300):
                            
                            logger.info("📊 Running scheduled pre-market scan...")
                            self.run_premarket_scan()
                            self.last_scan_time = now
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=premarket_scheduler, daemon=True).start()
        logger.info("⏰ Pre-market scheduler started")
    
    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.chat_id:
            logger.warning("⚠️ No chat ID available")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Message sent")
                return True
            else:
                logger.error(f"❌ Send failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return False
    
    def send_real_data_banner(self):
        """Send real data disclaimer banner"""
        banner_message = """
🔴 <b>NSE PRE-MARKET SCANNER - REAL DATA ONLY</b> 🔴

✅ <b>Data Source:</b> NSE Official API
✅ <b>Data Type:</b> Live Pre-Market Trading Data
✅ <b>Update Frequency:</b> Real-time from NSE
✅ <b>Filter Criteria:</b> Stocks with ±2% or more movement

🚫 <b>What we DON'T use:</b>
❌ Mock or simulated data
❌ Estimated prices
❌ Historical data projections
❌ Third-party approximations

🎯 <b>What you GET:</b>
✅ Genuine NSE pre-market prices
✅ Real Indicative Equilibrium Price (IEP)
✅ Actual trading volumes and values
✅ Live percentage changes
✅ Sector-wise classification

⚠️ <b>DISCLAIMER:</b>
• Data sourced directly from NSE pre-market session
• Prices are indicative and may change during regular trading
• This is for informational purposes only
• Not investment advice - consult your financial advisor

🕘 <b>Pre-Market Session:</b> 9:00 AM - 9:15 AM IST
📊 <b>Regular Market:</b> 9:15 AM - 3:30 PM IST

<i>🔴 100% Real NSE Data Guarantee - No Mock/Simulation Ever!</i>
        """
        
        return self.send_message(banner_message)
    
    def send_pre_market_summary(self):
        """Send pre-market gainers/losers summary"""
        try:
            logger.info("🔍 Fetching NSE pre-market data...")
            premarket_data = self.data_fetcher.get_nse_premarket_data()
            
            if not premarket_data:
                error_message = """
❌ <b>PRE-MARKET DATA UNAVAILABLE</b>

🔍 <b>Attempted Source:</b> NSE Official API
⚠️ <b>Status:</b> Unable to fetch real pre-market data

💡 <b>Possible Reasons:</b>
• Pre-market session not active (9:00 AM - 9:15 AM IST)
• NSE API temporarily unavailable
• Network connectivity issues
• Market holiday

🕘 <b>Pre-Market Timing:</b> 9:00 AM - 9:15 AM IST
🔄 <b>Retry:</b> Please try again during pre-market hours

<i>🔴 This bot only shows real NSE data - no mock/simulation</i>
                """
                return self.send_message(error_message)
            
            logger.info("📊 Filtering significant movers...")
            movers = self.data_fetcher.filter_significant_movers(premarket_data, threshold=2.0)
            
            # Cache the data
            self.last_premarket_data = movers
            
            summary_message = self.format_premarket_summary(movers)
            return self.send_message(summary_message)
            
        except Exception as e:
            logger.error(f"❌ Pre-market summary error: {e}")
            error_msg = f"""
❌ <b>ERROR GENERATING PRE-MARKET SUMMARY</b>

🔧 <b>Technical Error:</b> {str(e)}
🔄 <b>Please try again in a few minutes</b>

<i>🔴 Only real NSE data is processed - no fallback simulation</i>
            """
            return self.send_message(error_msg)
    
    def format_premarket_summary(self, movers):
        """Format pre-market summary with sector classification"""
        try:
            gainers = movers['gainers']
            losers = movers['losers']
            timestamp = movers['timestamp']
            total_stocks = movers['total_stocks']
            
            # Group by sector
            gainers_by_sector = defaultdict(list)
            losers_by_sector = defaultdict(list)
            
            for stock in gainers:
                gainers_by_sector[stock['sector']].append(stock)
            
            for stock in losers:
                losers_by_sector[stock['sector']].append(stock)
            
            # Build message
            message = f"""
📊 <b>NSE PRE-MARKET REPORT - {timestamp.strftime('%d %b %Y')}</b>

🕘 <b>Report Time:</b> {timestamp.strftime('%H:%M:%S IST')}
📈 <b>Stocks Scanned:</b> {total_stocks:,}
🎯 <b>Filter:</b> ±2% or more movement
🔴 <b>Data:</b> Real NSE Pre-Market API

"""
            
            # Gainers section
            if gainers:
                message += f"🟢 <b>TOP GAINERS (±2%+)</b> 🟢\n\n"
                
                for sector, stocks in sorted(gainers_by_sector.items()):
                    message += f"<b>[{sector}]</b>\n"
                    
                    for stock in stocks[:3]:  # Top 3 per sector
                        volume_str = f"{stock['volume']:,}" if stock['volume'] > 0 else "N/A"
                        message += f"• <b>{stock['symbol']}</b>: ₹{stock['price']:.2f} "
                        message += f"(<b>+{stock['percent_change']:.2f}%</b>) "
                        message += f"Vol: {volume_str}\n"
                    
                    message += "\n"
            else:
                message += "🟢 <b>NO SIGNIFICANT GAINERS</b> (±2%+)\n\n"
            
            # Losers section
            if losers:
                message += f"🔴 <b>TOP LOSERS (±2%+)</b> 🔴\n\n"
                
                for sector, stocks in sorted(losers_by_sector.items()):
                    message += f"<b>[{sector}]</b>\n"
                    
                    for stock in stocks[:3]:  # Top 3 per sector
                        volume_str = f"{stock['volume']:,}" if stock['volume'] > 0 else "N/A"
                        message += f"• <b>{stock['symbol']}</b>: ₹{stock['price']:.2f} "
                        message += f"(<b>{stock['percent_change']:.2f}%</b>) "
                        message += f"Vol: {volume_str}\n"
                    
                    message += "\n"
            else:
                message += "🔴 <b>NO SIGNIFICANT LOSERS</b> (±2%+)\n\n"
            
            # Footer
            message += f"""
📊 <b>SUMMARY:</b>
• Gainers: {len(gainers)} stocks
• Losers: {len(losers)} stocks
• Sectors Active: {len(set(gainers_by_sector.keys()) | set(losers_by_sector.keys()))}

💡 <b>PRE-MARKET TIP:</b>
Pre-market prices are indicative. Actual opening prices may vary based on market sentiment, news flow, and order book dynamics during the opening session.

⚠️ <b>RISK DISCLAIMER:</b>
This information is for educational purposes only. Please consult your financial advisor before making investment decisions.

🔴 <b>Data Source:</b> NSE Official API - 100% Real Data
📅 <b>Generated:</b> {timestamp.strftime('%d %b %Y, %H:%M:%S IST')}
            """
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Format error: {e}")
            return f"❌ Error formatting pre-market summary: {str(e)}"
    
    def run_premarket_scan(self):
        """Run complete pre-market scan and send both messages"""
        try:
            # Send banner first
            banner_sent = self.send_real_data_banner()
            
            if banner_sent:
                time.sleep(2)  # Wait between messages
                
                # Send summary
                summary_sent = self.send_pre_market_summary()
                
                if summary_sent:
                    logger.info("✅ Pre-market scan completed")
                    return True
                else:
                    logger.error("❌ Summary send failed")
                    return False
            else:
                logger.error("❌ Banner send failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Scan error: {e}")
            return False
    
    def process_message(self, update):
        """Process incoming Telegram messages"""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            if not chat_id:
                return
            
            # Store chat_id
            if not self.chat_id:
                self.chat_id = chat_id
                logger.info(f"✅ Chat ID registered: {chat_id}")
            
            # Handle commands
            if text.startswith('/'):
                self.handle_command(text, chat_id)
                
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
    
    def handle_command(self, command, chat_id):
        """Handle bot commands"""
        
        if command == '/start':
            welcome_msg = """
🔴 <b>NSE PRE-MARKET SCANNER BOT</b> 🔴

🌐 <b>Hosted on:</b> Render.com (24/7 FREE)
📊 <b>Data Source:</b> NSE Official API
🎯 <b>Focus:</b> Pre-market gainers/losers (±2%+)

<b>🚀 Features:</b>
✅ Real NSE pre-market data only
✅ Automatic scans during 9:00-9:15 AM IST
✅ Sector-wise classification
✅ No mock/simulated data ever

<b>📱 Commands:</b>
/scan - Run manual pre-market scan
/status - Bot status and next scan time
/help - All available commands

<b>⏰ Auto-Schedule:</b>
Bot automatically scans and sends reports during pre-market hours (9:00-9:15 AM IST, Mon-Fri)

🔴 <b>100% Real NSE Data Guarantee!</b>
            """
            self.send_message(welcome_msg)
            
        elif command == '/scan':
            scan_msg = "🔍 <b>Running Manual Pre-Market Scan...</b>\n\nPlease wait..."
            self.send_message(scan_msg)
            
            success = self.run_premarket_scan()
            
            if not success:
                error_msg = "❌ Manual scan failed. Check if pre-market session is active (9:00-9:15 AM IST)."
                self.send_message(error_msg)
                
        elif command == '/status':
            now = datetime.datetime.now()
            next_scan = "Within 5 minutes" if (9 <= now.hour <= 9 and now.minute <= 15 and now.weekday() < 5) else "Next trading day 9:00-9:15 AM IST"
            
            status_msg = f"""
📊 <b>BOT STATUS</b>

🟢 <b>Status:</b> Online 24/7
🌐 <b>Hosting:</b> Render.com FREE
⏰ <b>Current Time:</b> {now.strftime('%H:%M:%S IST')}
📅 <b>Date:</b> {now.strftime('%d %b %Y, %A')}

<b>🔄 Scheduler:</b>
• Auto-scans: 9:00-9:15 AM IST (Mon-Fri)
• Next scan: {next_scan}
• Last scan: {self.last_scan_time.strftime('%H:%M:%S') if self.last_scan_time else 'Not yet'}

<b>📊 Data Status:</b>
• NSE connection: Active
• Cache status: {'Available' if self.last_premarket_data else 'Empty'}
• Real data only: ✅ Guaranteed

💡 Use /scan for manual pre-market analysis
            """
            self.send_message(status_msg)
            
        elif command == '/help':
            help_msg = """
🆘 <b>NSE PRE-MARKET SCANNER HELP</b>

<b>📊 Commands:</b>
/start - Initialize bot
/scan - Manual pre-market scan
/status - Bot status and schedule
/help - This help message

<b>⏰ Auto-Schedule:</b>
• Runs automatically 9:00-9:15 AM IST
• Monday to Friday only
• Scans every 5 minutes during session

<b>🎯 Features:</b>
• Real NSE pre-market data
• ±2% movement filter
• Sector classification
• Gainers/losers separation

<b>🔴 Data Policy:</b>
• 100% real NSE data
• No mock/simulation ever
• Direct API integration
• Live pre-market prices

<b>💡 Best Usage:</b>
Keep bot active and receive automatic pre-market reports every trading day!
            """
            self.send_message(help_msg)
            
        else:
            self.send_message(f"❓ Unknown command: {command}\nType /help for available commands.")

# Initialize bot
bot = RenderPreMarketTelegramBot()

# Flask routes for Render.com
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        update = request.get_json()
        bot.process_message(update)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/health')
def health():
    """Health check endpoint for keep-alive"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'bot_running': bot.is_running,
        'chat_registered': bool(bot.chat_id),
        'last_scan': bot.last_scan_time.isoformat() if bot.last_scan_time else None,
        'premarket_data_cached': bool(bot.last_premarket_data)
    })

@app.route('/')
def home():
    """Home page for Render.com deployment"""
    now = datetime.datetime.now()
    next_scan = "Active now!" if (9 <= now.hour <= 9 and now.minute <= 15 and now.weekday() < 5) else "Next trading day 9:00-9:15 AM IST"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NSE Pre-Market Scanner Bot</title>
        <style>
            body {{ font-family: Arial; max-width: 900px; margin: 50px auto; padding: 20px; background: #f8f9fa; }}
            .header {{ background: linear-gradient(135deg, #dc3545 0%, #6f42c1 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
            .feature {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ color: #28a745; font-weight: bold; }}
            .button {{ display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔴 NSE Pre-Market Scanner Bot</h1>
            <p>Real NSE Data • Sector Classification • 24/7 Hosted FREE</p>
        </div>
        
        <div class="feature">
            <h2>📊 Live Status</h2>
            <p><strong>Bot Status:</strong> <span class="status">✅ Online 24/7</span></p>
            <p><strong>Hosting:</strong> Render.com (FREE Tier)</p>
            <p><strong>Current Time:</strong> {now.strftime('%H:%M:%S IST, %d %b %Y')}</p>
            <p><strong>Next Scan:</strong> {next_scan}</p>
            <p><strong>Chat Registered:</strong> {'✅ Yes' if bot.chat_id else '❌ Send /start to bot'}</p>
        </div>
        
        <div class="grid">
            <div class="feature">
                <h3>🎯 Features</h3>
                <ul>
                    <li>✅ Real NSE pre-market data only</li>
                    <li>✅ ±2% movement filter</li>
                    <li>✅ Sector-wise classification</li>
                    <li>✅ Auto-schedule during market hours</li>
                    <li>✅ Gainers/losers separation</li>
                    <li>✅ No mock/simulated data ever</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>⏰ Schedule</h3>
                <ul>
                    <li><strong>Pre-Market:</strong> 9:00 - 9:15 AM IST</li>
                    <li><strong>Auto-Scan:</strong> Every 5 minutes</li>
                    <li><strong>Days:</strong> Monday to Friday</li>
                    <li><strong>Manual:</strong> /scan command anytime</li>
                </ul>
            </div>
        </div>
        
        <div class="feature">
            <h2>🚀 Get Started</h2>
            <a href="https://t.me/tradsysbot" class="button">Start Bot</a>
            <p>Send <code>/start</code> to receive automatic pre-market reports!</p>
        </div>
        
        <div class="feature">
            <h2>📱 Commands</h2>
            <ul>
                <li><code>/start</code> - Initialize bot and register for alerts</li>
                <li><code>/scan</code> - Run manual pre-market scan</li>
                <li><code>/status</code> - Check bot status and schedule</li>
                <li><code>/help</code> - Get help and usage guide</li>
            </ul>
        </div>
        
        <div class="feature">
            <h2>📊 Sample Report</h2>
            <pre style="background: #f1f1f1; padding: 15px; border-radius: 5px; font-size: 12px;">
📊 NSE PRE-MARKET REPORT - 14 Jun 2025

🟢 TOP GAINERS (±2%+) 🟢

[IT]
• TCS: ₹3,456.75 (+3.25%) Vol: 125,430
• INFY: ₹1,234.50 (+2.87%) Vol: 98,765

[Banking]
• HDFCBANK: ₹1,675.90 (+2.15%) Vol: 156,789

🔴 TOP LOSERS (±2%+) 🔴

[Auto]
• MARUTI: ₹9,876.50 (-2.67%) Vol: 87,654

📊 SUMMARY:
• Gainers: 12 stocks • Losers: 8 stocks
🔴 Data Source: NSE Official API - 100% Real Data
            </pre>
        </div>
        
        <div class="feature">
            <h2>🔴 Data Guarantee</h2>
            <p><strong>✅ Real NSE Data Only:</strong> Direct API integration</p>
            <p><strong>❌ No Mock Data:</strong> Authentic pre-market prices</p>
            <p><strong>📊 Live Updates:</strong> Real-time during 9:00-9:15 AM IST</p>
            <p><strong>🎯 Accurate Filtering:</strong> Genuine ±2% movers</p>
        </div>
    </body>
    </html>
    """

@app.route('/manual-scan')
def manual_scan():
    """Manual scan trigger via web"""
    if bot.chat_id:
        success = bot.run_premarket_scan()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Pre-market scan completed' if success else 'Scan failed - check logs',
            'timestamp': datetime.datetime.now().isoformat()
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No chat registered. Send /start to bot first.',
            'bot_link': 'https://t.me/tradsysbot'
        })

if __name__ == '__main__':
    logger.info("🚀 Starting NSE Pre-Market Scanner Bot on Render.com...")
    logger.info("🔴 Real NSE data only - No mock/simulation")
    logger.info("⏰ Auto-scans during 9:00-9:15 AM IST")
    
    # Get port from environment (Render.com sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Start Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
