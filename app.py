import os
import time
import requests
import json
import threading
import datetime
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
import logging
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedNSEDataFetcher:
    """Enhanced fetcher with better reliability and trading-focused features"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.cache = {}
        self.cache_duration = 60  # 1 minute cache
        
    def setup_session(self):
        """Setup session with proper headers and retry logic"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
        # Add retry adapter
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def set_cached_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = (data, time.time())
    
    def get_nse_cookies(self) -> bool:
        """Get NSE cookies with proper session management"""
        try:
            # Clear any existing cookies
            self.session.cookies.clear()
            
            # Get main page to establish session
            response = self.session.get(
                'https://www.nseindia.com', 
                timeout=20,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                logger.info("✅ NSE session established successfully")
                return True
            else:
                logger.error(f"❌ NSE session failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ NSE cookie error: {e}")
            return False
    
    def get_nse_index_data(self, symbol: str = "NIFTY 50") -> Optional[Dict]:
        """Enhanced NSE index data fetching"""
        cache_key = f"nse_index_{symbol}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        try:
            # Ensure we have cookies
            if not self.get_nse_cookies():
                return None
            
            # Wait a bit after getting cookies
            time.sleep(2)
            
            # Try multiple NSE endpoints
            endpoints = [
                f"https://www.nseindia.com/api/allIndices",
                f"https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse based on endpoint
                        if "allIndices" in endpoint:
                            for item in data.get('data', []):
                                if item.get('index') == symbol:
                                    result = self.parse_nse_index_data(item, 'NSE API')
                                    if result:
                                        self.set_cached_data(cache_key, result)
                                        return result
                        
                        elif "equity-stockIndices" in endpoint:
                            for item in data.get('data', []):
                                if item.get('index') == symbol:
                                    result = self.parse_nse_index_data(item, 'NSE Equity API')
                                    if result:
                                        self.set_cached_data(cache_key, result)
                                        return result
                                        
                except Exception as e:
                    logger.error(f"NSE endpoint {endpoint} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"NSE index data failed: {e}")
            
        return None
    
    def parse_nse_index_data(self, item: Dict, source: str) -> Optional[Dict]:
        """Parse NSE index data into standardized format"""
        try:
            last_price = float(item.get('last', 0))
            if last_price <= 0:
                return None
                
            change = float(item.get('change', 0))
            percent_change = float(item.get('pChange', 0))
            
            return {
                'source': source,
                'symbol': item.get('index', 'NIFTY 50'),
                'price': last_price,
                'change': change,
                'change_percent': percent_change,
                'open': float(item.get('open', 0)),
                'high': float(item.get('dayHigh', 0)),
                'low': float(item.get('dayLow', 0)),
                'previous_close': float(item.get('previousClose', 0)),
                'timestamp': datetime.datetime.now(),
                'status': 'live',
                'market_status': 'open' if abs(change) > 0 else 'unknown'
            }
        except Exception as e:
            logger.error(f"Error parsing NSE data: {e}")
            return None
    
    def get_yahoo_finance_data(self, symbol: str = "^NSEI") -> Optional[Dict]:
        """Enhanced Yahoo Finance with more data points"""
        cache_key = f"yahoo_{symbol}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        try:
            # Use yfinance for better reliability
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[0]
                high_price = hist['High'].max()
                low_price = hist['Low'].min()
                volume = int(hist['Volume'].sum())
                
                previous_close = info.get('previousClose', current_price)
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close else 0
                
                result = {
                    'source': 'Yahoo Finance Enhanced',
                    'symbol': 'NIFTY 50',
                    'price': float(current_price),
                    'change': float(change),
                    'change_percent': float(change_percent),
                    'open': float(open_price),
                    'high': float(high_price),
                    'low': float(low_price),
                    'previous_close': float(previous_close),
                    'volume': volume,
                    'timestamp': datetime.datetime.now(),
                    'status': 'live',
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'market_status': self.get_market_status()
                }
                
                self.set_cached_data(cache_key, result)
                return result
                
        except Exception as e:
            logger.error(f"Yahoo Finance enhanced failed: {e}")
            
        return None
    
    def get_market_status(self) -> str:
        """Determine current market status"""
        now = datetime.datetime.now()
        
        # Check if weekend
        if now.weekday() > 4:  # Saturday = 5, Sunday = 6
            return 'closed_weekend'
            
        # Check market hours (9:15 AM to 3:30 PM IST)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close:
            return 'open'
        elif now < market_open:
            return 'pre_market'
        else:
            return 'closed'
    
    def get_technical_indicators(self, symbol: str = "^NSEI", period: str = "1mo") -> Dict:
        """Get technical indicators for trading decisions"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if len(hist) < 20:
                return {}
            
            # Calculate technical indicators
            close_prices = hist['Close']
            
            # Moving averages
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
            
            # RSI
            rsi = self.calculate_rsi(close_prices)
            
            # Bollinger Bands
            bb_upper, bb_lower = self.calculate_bollinger_bands(close_prices)
            
            # Support and Resistance
            support, resistance = self.calculate_support_resistance(hist)
            
            return {
                'sma_20': float(sma_20) if not pd.isna(sma_20) else None,
                'sma_50': float(sma_50) if sma_50 and not pd.isna(sma_50) else None,
                'rsi': float(rsi) if not pd.isna(rsi) else None,
                'bb_upper': float(bb_upper) if not pd.isna(bb_upper) else None,
                'bb_lower': float(bb_lower) if not pd.isna(bb_lower) else None,
                'support': float(support) if support else None,
                'resistance': float(resistance) if resistance else None,
                'trend': self.determine_trend(close_prices),
                'volatility': float(close_prices.pct_change().std() * 100) if len(close_prices) > 1 else None
            }
            
        except Exception as e:
            logger.error(f"Technical indicators error: {e}")
            return {}
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return np.nan
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            return upper.iloc[-1], lower.iloc[-1]
        except:
            return np.nan, np.nan
    
    def calculate_support_resistance(self, hist: pd.DataFrame, window: int = 10) -> Tuple[float, float]:
        """Calculate support and resistance levels"""
        try:
            highs = hist['High'].rolling(window=window).max()
            lows = hist['Low'].rolling(window=window).min()
            
            resistance = highs.tail(20).max()  # Recent resistance
            support = lows.tail(20).min()      # Recent support
            
            return support, resistance
        except:
            return None, None
    
    def determine_trend(self, prices: pd.Series) -> str:
        """Determine trend direction"""
        try:
            if len(prices) < 10:
                return 'insufficient_data'
                
            recent_prices = prices.tail(10)
            slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            
            if slope > 0.1:
                return 'bullish'
            elif slope < -0.1:
                return 'bearish'
            else:
                return 'sideways'
        except:
            return 'unknown'
    
    def get_comprehensive_market_data(self) -> Optional[Dict]:
        """Get comprehensive market data for AI trading"""
        try:
            # Get basic data from multiple sources in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self.get_nse_index_data): 'nse',
                    executor.submit(self.get_yahoo_finance_data): 'yahoo',
                }
                
                results = {}
                for future in as_completed(futures):
                    source = futures[future]
                    try:
                        data = future.result(timeout=10)
                        if data:
                            results[source] = data
                    except Exception as e:
                        logger.error(f"{source} failed: {e}")
            
            # Choose best data source
            primary_data = None
            if 'nse' in results:
                primary_data = results['nse']
                logger.info("Using NSE as primary data source")
            elif 'yahoo' in results:
                primary_data = results['yahoo']
                logger.info("Using Yahoo Finance as primary data source")
            
            if not primary_data:
                return None
            
            # Enhance with technical indicators
            technical_data = self.get_technical_indicators()
            primary_data['technical_indicators'] = technical_data
            primary_data['market_status'] = self.get_market_status()
            
            # Add trading signals
            primary_data['trading_signals'] = self.generate_trading_signals(primary_data)
            
            return primary_data
            
        except Exception as e:
            logger.error(f"Comprehensive data error: {e}")
            return None
    
    def generate_trading_signals(self, data: Dict) -> Dict:
        """Generate basic trading signals for AI"""
        signals = {
            'overall_sentiment': 'neutral',
            'strength': 0,  # -100 to +100
            'signals': []
        }
        
        try:
            price = data.get('price', 0)
            change_percent = data.get('change_percent', 0)
            technical = data.get('technical_indicators', {})
            
            score = 0
            
            # Price momentum signal
            if change_percent > 1:
                signals['signals'].append('strong_bullish_momentum')
                score += 30
            elif change_percent > 0.5:
                signals['signals'].append('bullish_momentum')
                score += 15
            elif change_percent < -1:
                signals['signals'].append('strong_bearish_momentum')
                score -= 30
            elif change_percent < -0.5:
                signals['signals'].append('bearish_momentum')
                score -= 15
            
            # RSI signals
            rsi = technical.get('rsi')
            if rsi:
                if rsi > 70:
                    signals['signals'].append('overbought_rsi')
                    score -= 20
                elif rsi < 30:
                    signals['signals'].append('oversold_rsi')
                    score += 20
            
            # Moving average signals
            sma_20 = technical.get('sma_20')
            if sma_20 and price:
                if price > sma_20 * 1.02:
                    signals['signals'].append('above_sma20')
                    score += 10
                elif price < sma_20 * 0.98:
                    signals['signals'].append('below_sma20')
                    score -= 10
            
            # Bollinger Bands signals
            bb_upper = technical.get('bb_upper')
            bb_lower = technical.get('bb_lower')
            if bb_upper and bb_lower and price:
                if price > bb_upper:
                    signals['signals'].append('above_bb_upper')
                    score -= 15
                elif price < bb_lower:
                    signals['signals'].append('below_bb_lower')
                    score += 15
            
            # Trend signal
            trend = technical.get('trend')
            if trend == 'bullish':
                signals['signals'].append('bullish_trend')
                score += 15
            elif trend == 'bearish':
                signals['signals'].append('bearish_trend')
                score -= 15
            
            # Set overall sentiment
            if score > 30:
                signals['overall_sentiment'] = 'bullish'
            elif score < -30:
                signals['overall_sentiment'] = 'bearish'
            
            signals['strength'] = max(-100, min(100, score))
            
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
        
        return signals

class TradingAITelegramBot:
    """Enhanced Telegram bot for AI trading assistance"""
    
    def __init__(self):
        self.bot_token = "7623288925:AAHEpUAqbXBi1FYhq0ok7nFsykrSNaY8Sh4"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.chat_id = None
        self.is_running = True
        
        # Initialize enhanced data fetcher
        self.data_fetcher = EnhancedNSEDataFetcher()
        
        # Setup
        self.render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        self.webhook_url = f"{self.render_url}/webhook"
        
        self.setup_webhook()
        self.start_background_tasks()
        
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
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        def keep_alive():
            while self.is_running:
                try:
                    time.sleep(840)  # 14 minutes
                    requests.get(f"{self.render_url}/health", timeout=5)
                    logger.info("🏓 Keep-alive ping")
                except:
                    pass
        
        threading.Thread(target=keep_alive, daemon=True).start()
        logger.info("🚀 Background tasks started")
    
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
    
    def get_enhanced_market_message(self) -> str:
        """Generate comprehensive market analysis message"""
        try:
            data = self.data_fetcher.get_comprehensive_market_data()
            
            if not data:
                return """
❌ <b>MARKET DATA UNAVAILABLE</b>

🔍 <b>Attempted Sources:</b>
• NSE API (Enhanced)
• Yahoo Finance (Enhanced)

⚠️ <b>All data sources currently unavailable.</b>
🔄 <b>Please try again in a few minutes.</b>
                """
            
            # Format comprehensive message
            price = data['price']
            change = data['change']
            change_percent = data['change_percent']
            
            change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            color = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
            
            message = f"""
{color} <b>NIFTY 50 - AI TRADING ANALYSIS</b> {color}

💰 <b>Current Price:</b> ₹{price:.2f}
{change_emoji} <b>Change:</b> {change:+.2f} ({change_percent:+.2f}%)

📊 <b>Day Statistics:</b>
• Open: ₹{data.get('open', 0):.2f}
• High: ₹{data.get('high', 0):.2f}
• Low: ₹{data.get('low', 0):.2f}
• Prev Close: ₹{data.get('previous_close', 0):.2f}

🔄 <b>Market Status:</b> {data.get('market_status', 'unknown').replace('_', ' ').title()}
            """
            
            # Add technical indicators
            technical = data.get('technical_indicators', {})
            if technical:
                message += f"\n\n📈 <b>TECHNICAL ANALYSIS:</b>\n"
                
                if technical.get('sma_20'):
                    sma_position = "Above" if price > technical['sma_20'] else "Below"
                    message += f"• SMA(20): ₹{technical['sma_20']:.2f} ({sma_position})\n"
                
                if technical.get('rsi'):
                    rsi = technical['rsi']
                    rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                    message += f"• RSI(14): {rsi:.1f} ({rsi_signal})\n"
                
                if technical.get('trend'):
                    trend_emoji = "📈" if technical['trend'] == 'bullish' else "📉" if technical['trend'] == 'bearish' else "➡️"
                    message += f"• Trend: {trend_emoji} {technical['trend'].title()}\n"
                
                if technical.get('support') and technical.get('resistance'):
                    message += f"• Support: ₹{technical['support']:.2f}\n"
                    message += f"• Resistance: ₹{technical['resistance']:.2f}\n"
            
            # Add AI trading signals
            signals = data.get('trading_signals', {})
            if signals:
                sentiment = signals.get('overall_sentiment', 'neutral')
                strength = signals.get('strength', 0)
                
                sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
                
                message += f"\n\n🤖 <b>AI TRADING SIGNALS:</b>\n"
                message += f"• Sentiment: {sentiment_emoji} {sentiment.title()}\n"
                message += f"• Strength: {strength}/100\n"
                
                if signals.get('signals'):
                    active_signals = signals['signals'][:3]  # Show top 3 signals
                    message += f"• Active Signals: {', '.join(active_signals)}\n"
            
            message += f"\n\n📱 <b>Source:</b> {data['source']}"
            message += f"\n⏰ <b>Updated:</b> {data['timestamp'].strftime('%H:%M:%S')}"
            message += f"\n\n<i>🤖 AI-Enhanced Trading Analysis</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating enhanced message: {e}")
            return "❌ Error processing market data. Please try again."
    
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
🤖 <b>AI TRADING ASSISTANT - NSE/BSE</b>

✅ <b>Enhanced Features:</b>
• Real-time NSE data with fallbacks
• Technical analysis (RSI, MA, BB)
• AI trading signals
• Support/Resistance levels
• Market sentiment analysis

📊 <b>Commands:</b>
/market - Complete market analysis
/technical - Technical indicators only
/signals - AI trading signals
/status - System status

🎯 <b>Optimized for Indian Market Traders</b>
• NSE/BSE focus
• Options trading insights
• Real-time alerts
• AI-powered analysis

<b>🚀 Start with /market for full analysis!</b>
            """
            self.send_message(chat_id, welcome_msg)
            
        elif command in ['/market', '/nifty']:
            market_msg = self.get_enhanced_market_message()
            self.send_message(chat_id, market_msg)
            
        elif command == '/technical':
            # Technical analysis only
            data = self.data_fetcher.get_comprehensive_market_data()
            if data and data.get('technical_indicators'):
                tech = data['technical_indicators']
                tech_msg = f"""
📈 <b>TECHNICAL ANALYSIS - NIFTY 50</b>

🔍 <b>Moving Averages:</b>
• SMA(20): ₹{tech.get('sma_20', 'N/A'):.2f}
• SMA(50): ₹{tech.get('sma_50', 'N/A'):.2f}

📊 <b>Oscillators:</b>
• RSI(14): {tech.get('rsi', 'N/A'):.1f}

📉 <b>Bollinger Bands:</b>
• Upper: ₹{tech.get('bb_upper', 'N/A'):.2f}
• Lower: ₹{tech.get('bb_lower', 'N/A'):.2f}

🎯 <b>Support/Resistance:</b>
• Support: ₹{tech.get('support', 'N/A'):.2f}
• Resistance: ₹{tech.get('resistance', 'N/A'):.2f}

📈 <b>Trend:</b> {tech.get('trend', 'Unknown').title()}
📊 <b>Volatility:</b> {tech.get('volatility', 'N/A'):.2f}%
                """
                self.send_message(chat_id, tech_msg)
            else:
                self.send_message(chat_id, "❌ Technical analysis unavailable")
                
        elif command == '/signals':
            # AI signals only
            data = self.data_fetcher.get_comprehensive_market_data()
            if data and data.get('trading_signals'):
                signals = data['trading_signals']
                
                sentiment = signals.get('overall_sentiment', 'neutral')
                strength = signals.get('strength', 0)
                active_signals = signals.get('signals', [])
                
                sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
                
                signals_msg = f"""
🤖 <b>AI TRADING SIGNALS - NIFTY 50</b>

{sentiment_emoji} <b>Overall Sentiment:</b> {sentiment.title()}
📊 <b>Signal Strength:</b> {strength}/100

🎯 <b>Active Signals:</b>
                """
                
                for signal in active_signals:
                    signals_msg += f"• {signal.replace('_', ' ').title()}\n"
                
                if not active_signals:
                    signals_msg += "• No active signals\n"
                
                signals_msg += f"\n⏰ <b>Generated:</b> {datetime.datetime.now().strftime('%H:%M:%S')}"
                
                self.send_message(chat_id, signals_msg)
            else:
                self.send_message(chat_id, "❌ AI signals unavailable")
                
        elif command == '/status':
            market_status = self.data_fetcher.get_market_status()
            status_msg = f"""
📊 <b>SYSTEM STATUS</b>

🕒 <b>Market Status:</b> {market_status.replace('_', ' ').title()}
🤖 <b>AI Engine:</b> Active
📡 <b>Data Sources:</b> Multi-source
💾 <b>Cache:</b> Enabled (60s)

<b>✅ Capabilities:</b>
• Real-time data fetching
• Technical analysis
• AI signal generation
• Multi-source fallback
• Enhanced error handling

<b>📈 Data Quality:</b> Production Ready
            """
            self.send_message(chat_id, status_msg)
            
        else:
            self.send_message(chat_id, f"❓ Unknown command: {command}\nType /start for help.")

# Initialize enhanced bot
bot = TradingAITelegramBot()

# Flask app setup
app = Flask(__name__)

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
        'market_status': bot.data_fetcher.get_market_status(),
        'cache_size': len(bot.data_fetcher.cache),
        'features': ['real_time_data', 'technical_analysis', 'ai_signals', 'multi_source']
    })

@app.route('/')
def home():
    return f"""
    <h1>🤖 AI Trading Assistant - NSE/BSE</h1>
    <p><strong>Enhanced Features:</strong> Real-time data, Technical analysis, AI signals</p>
    <p><strong>Market Status:</strong> {bot.data_fetcher.get_market_status()}</p>
    <p><strong>Bot:</strong> <a href="https://t.me/tradsysbot">@tradsysbot</a></p>
    <p><strong>Updated:</strong> {datetime.datetime.now()}</p>
    """

if __name__ == '__main__':
    logger.info("🤖 Starting AI Trading Assistant...")
    logger.info("📊 Enhanced with technical analysis and AI signals")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
