        ', 'https://your-app.onrender.com')
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
                logger.info("✅ Webhook setup successful")
            else:
                logger.error(f"❌ Webhook setup failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
    
    def start_background_tasks(self):
        """Start background monitoring"""
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
                recommendation = signals.get('recommendation', 'hold')
                
                sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
                rec_emoji = "🔥" if recommendation == 'buy' else "❄️" if recommendation == 'sell' else "🤚"
                
                message += f"\n\n🤖 <b>AI TRADING SIGNALS:</b>\n"
                message += f"• Sentiment: {sentiment_emoji} {sentiment.title()}\n"
                message += f"• Strength: {strength}/100\n"
                message += f"• Recommendation: {rec_emoji} {recommendation.upper()}\n"
                
                if signals.get('signals'):
                    active_signals = signals['signals'][:3]  # Show top 3 signals
                    message += f"• Key Signals: {', '.join(active_signals)}\n"
            
            # Add options analysis if available
            options = data.get('options_analysis', {})
            if options:
                message += f"\n\n📊 <b>OPTIONS ANALYSIS:</b>\n"
                message += f"• PCR: {options.get('pcr', 'N/A')}\n"
                message += f"• Max Pain: ₹{options.get('max_pain', 'N/A')}\n"
                message += f"• Options Sentiment: {options.get('sentiment', 'N/A').title()}\n"
                
                if options.get('support_levels'):
                    support_str = ', '.join([f"₹{s}" for s in options['support_levels']])
                    message += f"• OI Support: {support_str}\n"
                
                if options.get('resistance_levels'):
                    resistance_str = ', '.join([f"₹{r}" for r in options['resistance_levels']])
                    message += f"• OI Resistance: {resistance_str}\n"
            
            message += f"\n\n📱 <b>Source:</b> {data['source']}"
            message += f"\n⏰ <b>Updated:</b> {data['timestamp'].strftime('%H:%M:%S')}"
            message += f"\n\n<i>🤖 AI-Enhanced Trading Analysis</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating enhanced message: {e}")
            return "❌ Error processing market data. Please try again."
    
    def get_options_only_message(self) -> str:
        """Generate options-only analysis message"""
        try:
            options_data = self.data_fetcher.options_analyzer.get_options_chain()
            
            if not options_data:
                return "❌ Options data unavailable. Market may be closed or NSE API issues."
            
            sentiment = self.data_fetcher.options_analyzer.analyze_options_sentiment(options_data)
            
            if not sentiment:
                return "❌ Unable to analyze options sentiment."
            
            underlying = options_data.get('underlying_price', 0)
            expiry = options_data.get('expiry_date', 'N/A')
            
            pcr = sentiment.get('pcr', 0)
            max_pain = sentiment.get('max_pain', 0)
            options_sentiment = sentiment.get('sentiment', 'neutral')
            
            # Sentiment emoji
            sentiment_emoji = "🐂" if options_sentiment == 'bullish' else "🐻" if options_sentiment == 'bearish' else "😐"
            
            message = f"""
📊 <b>NIFTY OPTIONS ANALYSIS</b>

💰 <b>Underlying:</b> ₹{underlying:.2f}
📅 <b>Expiry:</b> {expiry}

🎯 <b>KEY METRICS:</b>
• PCR: {pcr}
• Max Pain: ₹{max_pain}
• Sentiment: {sentiment_emoji} {options_sentiment.title()}

📈 <b>OPEN INTEREST:</b>
• Total Call OI: {sentiment.get('total_call_oi', 0):,}
• Total Put OI: {sentiment.get('total_put_oi', 0):,}

🎲 <b>KEY LEVELS:</b>
            """
            
            if sentiment.get('support_levels'):
                support_str = ', '.join([f"₹{s}" for s in sentiment['support_levels']])
                message += f"• Support: {support_str}\n"
            
            if sentiment.get('resistance_levels'):
                resistance_str = ', '.join([f"₹{r}" for r in sentiment['resistance_levels']])
                message += f"• Resistance: {resistance_str}\n"
            
            # PCR interpretation
            message += f"\n💡 <b>PCR INTERPRETATION:</b>\n"
            if pcr > 1.5:
                message += "• Very Bullish (High Put Writing)\n"
            elif pcr > 1.2:
                message += "• Bullish (Put Writing)\n"
            elif pcr < 0.7:
                message += "• Bearish (Call Writing)\n"
            elif pcr < 0.5:
                message += "• Very Bearish (Heavy Call Writing)\n"
            else:
                message += "• Neutral (Balanced Activity)\n"
            
            message += f"\n⏰ <b>Updated:</b> {options_data['timestamp'].strftime('%H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Options message error: {e}")
            return "❌ Error processing options data."
    
    def get_technical_only_message(self) -> str:
        """Generate technical analysis only message"""
        try:
            data = self.data_fetcher.get_comprehensive_market_data()
            
            if not data:
                return "❌ Technical analysis unavailable - no market data."
            
            technical = data.get('technical_indicators', {})
            if not technical:
                return "❌ Technical indicators unavailable - insufficient price history."
            
            price = data.get('price', 0)
            
            message = f"""
📈 <b>NIFTY 50 - TECHNICAL ANALYSIS</b>

💰 <b>Current Price:</b> ₹{price:.2f}

🔍 <b>MOVING AVERAGES:</b>
• SMA(20): ₹{technical.get('sma_20', 'N/A'):.2f}
            """
            
            if technical.get('sma_50'):
                message += f"• SMA(50): ₹{technical['sma_50']:.2f}\n"
            
            # Price vs MA analysis
            sma_20 = technical.get('sma_20', 0)
            if sma_20:
                if price > sma_20:
                    message += f"• Price vs SMA(20): 📈 Above (+{((price/sma_20 - 1) * 100):.1f}%)\n"
                else:
                    message += f"• Price vs SMA(20): 📉 Below ({((price/sma_20 - 1) * 100):.1f}%)\n"
            
            message += f"""
📊 <b>OSCILLATORS:</b>
• RSI(14): {technical.get('rsi', 'N/A'):.1f}
• Signal: {technical.get('rsi_signal', 'N/A').title()}

📉 <b>BOLLINGER BANDS:</b>
• Upper: ₹{technical.get('bb_upper', 'N/A'):.2f}
• Lower: ₹{technical.get('bb_lower', 'N/A'):.2f}
            """
            
            # BB position
            bb_upper = technical.get('bb_upper', 0)
            bb_lower = technical.get('bb_lower', 0)
            if bb_upper and bb_lower:
                if price > bb_upper:
                    message += "• Position: Above Upper Band (Overbought)\n"
                elif price < bb_lower:
                    message += "• Position: Below Lower Band (Oversold)\n"
                else:
                    message += "• Position: Within Bands (Normal)\n"
            
            message += f"""
🎯 <b>SUPPORT/RESISTANCE:</b>
• Support: ₹{technical.get('support', 'N/A'):.2f}
• Resistance: ₹{technical.get('resistance', 'N/A'):.2f}

📈 <b>TREND ANALYSIS:</b>
• Current Trend: {technical.get('trend', 'Unknown').title()}
            """
            
            # Trend interpretation
            trend = technical.get('trend', 'sideways')
            if trend == 'bullish':
                message += "• Interpretation: 🐂 Upward momentum\n"
            elif trend == 'bearish':
                message += "• Interpretation: 🐻 Downward momentum\n"
            else:
                message += "• Interpretation: ➡️ Sideways movement\n"
            
            message += f"\n⏰ <b>Analysis Time:</b> {data['timestamp'].strftime('%H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Technical message error: {e}")
            return "❌ Error processing technical analysis."
    
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
• Options chain analysis (PCR, Max Pain)
• AI trading signals & recommendations
• Support/Resistance levels
• Market sentiment analysis

📊 <b>Commands:</b>
/market - Complete market analysis
/options - Options chain analysis only
/technical - Technical indicators only
/signals - AI trading signals only
/status - System status & health

🎯 <b>Optimized for Indian Traders</b>
• NSE/BSE focus with real data
• Options trading insights
• Intraday & swing trading signals
• AI-powered recommendations

<b>🚀 Start with /market for full analysis!</b>

<i>Developed for serious NSE/BSE traders 🇮🇳</i>
            """
            self.send_message(chat_id, welcome_msg)
            
        elif command in ['/market', '/nifty']:
            market_msg = self.get_enhanced_market_message()
            self.send_message(chat_id, market_msg)
            
        elif command == '/options':
            options_msg = self.get_options_only_message()
            self.send_message(chat_id, options_msg)
            
        elif command == '/technical':
            tech_msg = self.get_technical_only_message()
            self.send_message(chat_id, tech_msg)
            
        elif command == '/signals':
            # AI signals only
            data = self.data_fetcher.get_comprehensive_market_data()
            if data and data.get('trading_signals'):
                signals = data['trading_signals']
                
                sentiment = signals.get('overall_sentiment', 'neutral')
                strength = signals.get('strength', 0)
                recommendation = signals.get('recommendation', 'hold')
                active_signals = signals.get('signals', [])
                
                sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
                rec_emoji = "🔥" if recommendation == 'buy' else "❄️" if recommendation == 'sell' else "🤚"
                
                # Color based on strength
                if strength > 50:
                    strength_color = "🟢"
                elif strength < -50:
                    strength_color = "🔴"
                else:
                    strength_color = "🟡"
                
                signals_msg = f"""
🤖 <b>AI TRADING SIGNALS - NIFTY 50</b>

{sentiment_emoji} <b>Overall Sentiment:</b> {sentiment.title()}
{strength_color} <b>Signal Strength:</b> {strength}/100
{rec_emoji} <b>AI Recommendation:</b> {recommendation.upper()}

🎯 <b>Active Signals:</b>
                """
                
                for i, signal in enumerate(active_signals[:5], 1):
                    clean_signal = signal.replace('_', ' ').title()
                    signals_msg += f"{i}. {clean_signal}\n"
                
                if not active_signals:
                    signals_msg += "• No active signals detected\n"
                
                # Add interpretation
                signals_msg += f"\n💡 <b>Interpretation:</b>\n"
                if strength > 60:
                    signals_msg += "• Strong signal - Consider action\n"
                elif strength > 30:
                    signals_msg += "• Moderate signal - Watch closely\n"
                elif strength < -60:
                    signals_msg += "• Strong bearish signal\n"
                elif strength < -30:
                    signals_msg += "• Moderate bearish signal\n"
                else:
                    signals_msg += "• Weak/mixed signals - Wait for clarity\n"
                
                signals_msg += f"\n⏰ <b>Generated:</b> {datetime.datetime.now().strftime('%H:%M:%S')}"
                signals_msg += f"\n\n<i>⚠️ For educational purposes only</i>"
                
                self.send_message(chat_id, signals_msg)
            else:
                self.send_message(chat_id, "❌ AI signals unavailable - no market data")
                
        elif command == '/status':
            market_status = self.data_fetcher.get_market_status()
            cache_size = len(self.data_fetcher.cache.memory_cache)
            price_history_size = len(self.data_fetcher.price_history)
            
            status_msg = f"""
📊 <b>SYSTEM STATUS</b>

🕒 <b>Market Status:</b> {market_status.replace('_', ' ').title()}
🤖 <b>AI Engine:</b> ✅ Active
📡 <b>Data Sources:</b> NSE + Yahoo Finance
💾 <b>Cache Status:</b> {cache_size}/100 entries
📈 <b>Price History:</b> {price_history_size} data points

<b>✅ Active Features:</b>
• Real-time data fetching
• Technical analysis engine
• Options chain analysis
• AI signal generation
• Multi-source fallback
• Rate limiting & caching

<b>📊 Data Quality:</b> Production Ready
<b>🚀 Performance:</b> Optimized for speed

<b>🔧 Last Update:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
            """
            self.send_message(chat_id, status_msg)
            
        else:
            help_msg = f"""
❓ <b>Unknown command:</b> {command}

📚 <b>Available Commands:</b>
/start - Welcome & features
/market - Complete analysis
/options - Options chain only
/technical - Technical analysis only
/signals - AI trading signals
/status - System status

💡 <b>Tip:</b> Use /market for comprehensive analysis!
            """
            self.send_message(chat_id, help_msg)

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
    cache_size = len(bot.data_fetcher.cache.memory_cache)
    price_history_size = len(bot.data_fetcher.price_history)
    market_status = bot.data_fetcher.get_market_status()
    
    return jsonify({
        'status': 'healthy',
        'market_status': market_status,
        'cache_size': cache_size,
        'price_history_size': price_history_size,
        'features': [
            'real_time_data',
            'technical_analysis', 
            'options_analysis',
            'ai_signals',
            'multi_source_fallback'
        ],
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/')
def home():
    market_status = bot.data_fetcher.get_market_status()
    cache_size = len(bot.data_fetcher.cache.memory_cache)
    
    return f"""
    <html>
    <head>
        <title>AI Trading Assistant - NSE/BSE</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .feature {{ background: #f0f8f0; padding: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
            h1 {{ color: #2c3e50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Trading Assistant - NSE/BSE</h1>
            
            <div class="status">
                <h3>📊 System Status</h3>
                <p><strong>Market Status:</strong> {market_status.replace('_', ' ').title()}</p>
                <p><strong>Cache Entries:</strong> {cache_size}/100</p>
                <p><strong>Last Updated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h3>🚀 Enhanced Features</h3>
            <div class="feature">📈 Real-time NSE data with Yahoo Finance fallback</div>
            <div class="feature">🔍 Technical analysis (RSI, Moving Averages, Bollinger Bands)</div>
            <div class="feature">📊 Options chain analysis (PCR, Max Pain, OI levels)</div>
            <div class="feature">🤖 AI trading signals and recommendations</div>
            <div class="feature">⚡ Advanced caching and rate limiting</div>
            <div class="feature">🛡️ Multi-source data reliability</div>
            
            <h3>📱 Telegram Bot</h3>
            <p><strong>Bot Link:</strong> <a href="https://t.me/tradsysbot" target="_blank">@tradsysbot</a></p>
            <p><strong>Commands:</strong> /start, /market, /options, /technical, /signals, /status</p>
            
            <h3>🎯 Optimized For</h3>
            <ul>
                <li>NSE/BSE intraday and swing traders</li>
                <li>Options traders seeking PCR and OI analysis</li>
                <li>Technical analysis enthusiasts</li>
                <li>AI-powered trading decisions</li>
            </ul>
            
            <div class="status">
                <p><em>⚠️ For educational and informational purposes only. Not financial advice.</em></p>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    logger.info("🤖 Starting AI Trading Assistant...")
    logger.info("📊 Enhanced with technical analysis, options analysis, and AI signals")
    logger.info("🚀 Optimized for NSE/BSE traders")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < slow:
                return 0.0, 0.0, 0.0
            
            # Calculate EMAs
            ema_fast = TechnicalAnalyzer.calculate_ema(prices, fast)
            ema_slow = TechnicalAnalyzer.calculate_ema(prices, slow)
            
            # MACD line = Fast EMA - Slow EMA
            macd_line = ema_fast - ema_slow
            
            # Calculate MACD signal line (9-period EMA of MACD line)
            # For simplicity, using a basic average
            macd_signal = macd_line * 0.8  # Simplified signal line
            
            # MACD histogram = MACD line - Signal line
            macd_histogram = macd_line - macd_signal
            
            return macd_line, macd_signal, macd_histogram
        except:
            return 0.0, 0.0, 0.0
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices) if prices else 0
            
            multiplier = 2 / (period + 1)
            ema = prices[0]  # Start with first price
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except:
            return 0.0
    
    @staticmethod
    def analyze_volume_trend(prices: List[float]) -> str:
        """Analyze volume trend based on price movements"""
        try:
            if len(prices) < 10:
                return 'insufficient_data'
            
            # Simulate volume based on price volatility
            price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            avg_volatility = sum(price_changes[-10:]) / min(10, len(price_changes))
            recent_volatility = sum(price_changes[-5:]) / min(5, len(price_changes))
            
            if recent_volatility > avg_volatility * 1.2:
                return 'increasing'
            elif recent_volatility < avg_volatility * 0.8:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'unknown'
    
    @staticmethod
    def calculate_stochastic(prices: List[float], period: int = 14) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        try:
            if len(prices) < period:
                return 50.0, 50.0
            
            recent_prices = prices[-period:]
            highest = max(recent_prices)
            lowest = min(recent_prices)
            current = prices[-1]
            
            if highest == lowest:
                k_percent = 50.0
            else:
                k_percent = ((current - lowest) / (highest - lowest)) * 100
            
            # Simplified D% (3-period moving average of K%)
            d_percent = k_percent * 0.7  # Simplified calculation
            
            return k_percent, d_percent
        except:
            return 50.0, 50.0
    def analyze_entry_exit_points(self, current_price: float, rsi: float, sma_20: float, 
                                 sma_50: float, bb_upper: float, bb_lower: float,
                                 macd_line: float, macd_signal: float, 
                                 support: float, resistance: float) -> Dict:
        """Analyze entry and exit points based on technical indicators"""
        try:
            entry_signals = []
            exit_signals = []
            stop_loss_levels = []
            target_levels = []
            
            # RSI-based signals
            if rsi < 30:  # Oversold
                entry_signals.append({
                    'type': 'BUY',
                    'reason': 'RSI Oversold',
                    'strength': 'Strong',
                    'price_level': current_price,
                    'confidence': 85
                })
                target_levels.append(current_price * 1.02)  # 2% target
                stop_loss_levels.append(current_price * 0.985)  # 1.5% stop loss
                
            elif rsi > 70:  # Overbought
                exit_signals.append({
                    'type': 'SELL',
                    'reason': 'RSI Overbought',
                    'strength': 'Strong',
                    'price_level': current_price,
                    'confidence': 85
                })
            
            # Moving Average Crossover signals
            if sma_50 and current_price > sma_20 > sma_50:
                entry_signals.append({
                    'type': 'BUY',
                    'reason': 'Golden Cross Pattern',
                    'strength': 'Medium',
                    'price_level': current_price,
                    'confidence': 75
                })
            elif sma_50 and current_price < sma_20 < sma_50:
                exit_signals.append({
                    'type': 'SELL',
                    'reason': 'Death Cross Pattern',
                    'strength': 'Medium',
                    'price_level': current_price,
                    'confidence': 75
                })
            
            # Bollinger Bands signals
            if current_price <= bb_lower:
                entry_signals.append({
                    'type': 'BUY',
                    'reason': 'BB Lower Band Bounce',
                    'strength': 'Medium',
                    'price_level': bb_lower,
                    'confidence': 70
                })
                target_levels.append(bb_upper)
                stop_loss_levels.append(bb_lower * 0.995)
                
            elif current_price >= bb_upper:
                exit_signals.append({
                    'type': 'SELL',
                    'reason': 'BB Upper Band Resistance',
                    'strength': 'Medium',
                    'price_level': bb_upper,
                    'confidence': 70
                })
            
            # MACD signals
            if macd_line > macd_signal and macd_line > 0:
                entry_signals.append({
                    'type': 'BUY',
                    'reason': 'MACD Bullish Crossover',
                    'strength': 'Medium',
                    'price_level': current_price,
                    'confidence': 70
                })
            elif macd_line < macd_signal and macd_line < 0:
                exit_signals.append({
                    'type': 'SELL',
                    'reason': 'MACD Bearish Crossover',
                    'strength': 'Medium',
                    'price_level': current_price,
                    'confidence': 70
                })
            
            # Support and Resistance levels
            if abs(current_price - support) / support < 0.01:  # Within 1% of support
                entry_signals.append({
                    'type': 'BUY',
                    'reason': 'Near Support Level',
                    'strength': 'Strong',
                    'price_level': support,
                    'confidence': 80
                })
                stop_loss_levels.append(support * 0.98)
                target_levels.append(resistance)
                
            elif abs(current_price - resistance) / resistance < 0.01:  # Within 1% of resistance
                exit_signals.append({
                    'type': 'SELL',
                    'reason': 'Near Resistance Level',
                    'strength': 'Strong',
                    'price_level': resistance,
                    'confidence': 80
                })
            
            # Calculate risk-reward ratios
            best_entry = None
            best_exit = None
            
            if entry_signals:
                best_entry = max(entry_signals, key=lambda x: x['confidence'])
            
            if exit_signals:
                best_exit = max(exit_signals, key=lambda x: x['confidence'])
            
            # Overall recommendation
            if len(entry_signals) > len(exit_signals):
                overall_signal = 'BUY'
                signal_strength = len(entry_signals) * 20
            elif len(exit_signals) > len(entry_signals):
                overall_signal = 'SELL'
                signal_strength = len(exit_signals) * 20
            else:
                overall_signal = 'HOLD'
                signal_strength = 50
            
            return {
                'entry_signals': entry_signals,
                'exit_signals': exit_signals,
                'stop_loss_levels': list(set(stop_loss_levels)),  # Remove duplicates
                'target_levels': list(set(target_levels)),
                'best_entry': best_entry,
                'best_exit': best_exit,
                'overall_signal': overall_signal,
                'signal_strength': min(100, signal_strength),
                'total_signals': len(entry_signals) + len(exit_signals),
                'risk_reward_ratio': self.calculate_risk_reward(
                    current_price, target_levels, stop_loss_levels
                )
            }
            
        except Exception as e:
            logger.error(f"Entry/Exit analysis error: {e}")
            return {
                'entry_signals': [],
                'exit_signals': [],
                'overall_signal': 'HOLD',
                'signal_strength': 0
            }
    
    def calculate_risk_reward(self, current_price: float, targets: List[float], 
                            stop_losses: List[float]) -> float:
        """Calculate risk-reward ratio"""
        try:
            if not targets or not stop_losses:
                return 0.0
            
            avg_target = sum(targets) / len(targets)
            avg_stop_loss = sum(stop_losses) / len(stop_losses)
            
            potential_reward = avg_target - current_price
            potential_risk = current_price - avg_stop_loss
            
            if potential_risk <= 0:
                return 0.0
            
            return potential_reward / potential_risk
        except:
            return 0.0
    def get_enhanced_technical_message(self) -> str:
        """Generate enhanced technical analysis with entry/exit points"""
        try:
            data = self.data_fetcher.get_comprehensive_market_data()
            
            if not data:
                return "❌ Technical analysis unavailable - no market data."
            
            technical = data.get('technical_indicators', {})
            if not technical:
                return "❌ Technical indicators unavailable - insufficient price history."
            
            price = data.get('price', 0)
            entry_exit = technical.get('entry_exit_signals', {})
            
            message = f"""
📈 <b>NIFTY 50 - ENHANCED TECHNICAL ANALYSIS</b>

💰 <b>Current Price:</b> ₹{price:.2f}
📊 <b>Market Status:</b> {data.get('market_status', 'unknown').replace('_', ' ').title()}

🔍 <b>TECHNICAL INDICATORS:</b>
• RSI(14): {technical.get('rsi', 'N/A'):.1f} ({technical.get('rsi_signal', 'N/A').title()})
• SMA(20): ₹{technical.get('sma_20', 'N/A'):.2f}
"""
            
            if technical.get('sma_50'):
                message += f"• SMA(50): ₹{technical['sma_50']:.2f}\n"
            
            # Price position vs moving averages
            sma_20 = technical.get('sma_20', 0)
            if sma_20:
                position = "Above" if price > sma_20 else "Below"
                percentage = abs((price - sma_20) / sma_20 * 100)
                message += f"• Price vs SMA(20): {position} ({percentage:.1f}%)\n"
            
            message += f"""
• MACD: {technical.get('macd_line', 'N/A'):.2f} | Signal: {technical.get('macd_signal', 'N/A'):.2f}
• MACD Trend: {technical.get('macd_trend', 'Unknown').title()}
• Volume Trend: {technical.get('volume_trend', 'Unknown').title()}

📉 <b>BOLLINGER BANDS:</b>
• Upper: ₹{technical.get('bb_upper', 'N/A'):.2f}
• Middle: ₹{technical.get('bb_middle', 'N/A'):.2f}
• Lower: ₹{technical.get('bb_lower', 'N/A'):.2f}
            """
            
            # BB position analysis
            bb_upper = technical.get('bb_upper', 0)
            bb_lower = technical.get('bb_lower', 0)
            if bb_upper and bb_lower:
                if price > bb_upper:
                    message += "• Position: Above Upper Band (Overbought Zone)\n"
                elif price < bb_lower:
                    message += "• Position: Below Lower Band (Oversold Zone)\n"
                else:
                    bb_position = ((price - bb_lower) / (bb_upper - bb_lower)) * 100
                    message += f"• Position: {bb_position:.0f}% within bands\n"
            
            message += f"""
🎯 <b>KEY LEVELS:</b>
• Support: ₹{technical.get('support', 'N/A'):.2f}
• Resistance: ₹{technical.get('resistance', 'N/A'):.2f}
• Trend: {technical.get('trend', 'Unknown').title()}
            """
            
            # Entry/Exit Points Analysis
            if entry_exit:
                overall_signal = entry_exit.get('overall_signal', 'HOLD')
                signal_strength = entry_exit.get('signal_strength', 0)
                
                signal_emoji = "🔥" if overall_signal == 'BUY' else "❄️" if overall_signal == 'SELL' else "🤚"
                strength_color = "🟢" if signal_strength > 70 else "🟡" if signal_strength > 40 else "🔴"
                
                message += f"""

🎯 <b>ENTRY/EXIT ANALYSIS:</b>
{signal_emoji} <b>Overall Signal:</b> {overall_signal}
{strength_color} <b>Signal Strength:</b> {signal_strength}/100
🎲 <b>Total Signals:</b> {entry_exit.get('total_signals', 0)}
                """
                
                # Best entry signal
                best_entry = entry_exit.get('best_entry')
                if best_entry:
                    message += f"""
🔥 <b>BEST ENTRY SIGNAL:</b>
• Type: {best_entry['type']}
• Reason: {best_entry['reason']}
• Price Level: ₹{best_entry['price_level']:.2f}
• Confidence: {best_entry['confidence']}%
• Strength: {best_entry['strength']}
                    """
                
                # Best exit signal
                best_exit = entry_exit.get('best_exit')
                if best_exit:
                    message += f"""
❄️ <b>BEST EXIT SIGNAL:</b>
• Type: {best_exit['type']}
• Reason: {best_exit['reason']}
• Price Level: ₹{best_exit['price_level']:.2f}
• Confidence: {best_exit['confidence']}%
• Strength: {best_exit['strength']}
                    """
                
                # Risk management
                stop_losses = entry_exit.get('stop_loss_levels', [])
                targets = entry_exit.get('target_levels', [])
                risk_reward = entry_exit.get('risk_reward_ratio', 0)
                
                if stop_losses or targets:
                    message += f"\n🛡️ <b>RISK MANAGEMENT:</b>\n"
                    
                    if stop_losses:
                        avg_sl = sum(stop_losses) / len(stop_losses)
                        message += f"• Suggested Stop Loss: ₹{avg_sl:.2f}\n"
                    
                    if targets:
                        avg_target = sum(targets) / len(targets)
                        message += f"• Suggested Target: ₹{avg_target:.2f}\n"
                    
                    if risk_reward > 0:
                        message += f"• Risk:Reward Ratio: 1:{risk_reward:.1f}\n"
                
                # Active signals summary
                entry_signals = entry_exit.get('entry_signals', [])
                exit_signals = entry_exit.get('exit_signals', [])
                
                if entry_signals:
                    message += f"\n🎯 <b>ACTIVE ENTRY SIGNALS:</b>\n"
                    for i, signal in enumerate(entry_signals[:3], 1):
                        message += f"{i}. {signal['reason']} (Confidence: {signal['confidence']}%)\n"
                
                if exit_signals:
                    message += f"\n🚪 <b>ACTIVE EXIT SIGNALS:</b>\n"
                    for i, signal in enumerate(exit_signals[:3], 1):
                        message += f"{i}. {signal['reason']} (Confidence: {signal['confidence']}%)\n"
            
            message += f"\n\n⏰ <b>Analysis Time:</b> {data['timestamp'].strftime('%H:%M:%S')}"
            message += f"\n📱 <b>Source:</b> {data['source']}"
            message += f"\n\n<i>📊 Enhanced Technical Analysis with Entry/Exit Points</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"Enhanced technical message error: {e}")
            return "❌ Error processing enhanced technical analysis."    def get_bb_position(self, price: float, bb_upper: float, bb_lower: float) -> str:
        """Determine Bollinger Band position"""
        try:
            if price > bb_upper:
                return 'above_upper'
            elif price < bb_lower:
                return 'below_lower'
            else:
                bb_width = bb_upper - bb_lower
                position = (price - bb_lower) / bb_width
                if position > 0.7:
                    return 'upper_zone'
                elif position < 0.3:
                    return 'lower_zone'
                else:
                    return 'middle_zone'
        except:
            return 'unknown'
    
    def analyze_entry_exit_points(self, current_price: float, rsi: float, sma_20: float, 
                                 sma_50: float, ema_9: float, ema_21: float, bb_upper: float, 
                                 bb_lower: float, macd: float, macd_signal: float, trend: str) -> Dict:
        """Analyze entry and exit points based on technical indicators"""
        signals = {
            'entry_signals': [],
            'exit_signals': [],
            'stop_loss_levels': [],
            'target_levels': [],
            'overall_action': 'hold',
            'confidence': 0,
            'risk_level': 'medium'
        }
        
        try:
            entry_score = 0
            exit_score = 0
            
            # ENTRY SIGNAL ANALYSIS
            
            # 1. RSI Oversold Entry (Strong Buy Signal)
            if rsi < 30:
                signals['entry_signals'].append({
                    'type': 'RSI Oversold',
                    'strength': 'strong',
                    'description': f'RSI at {rsi:.1f} indicates oversold condition',
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.97,  # 3% stop loss
                    'target': current_price * 1.05     # 5% target
                })
                entry_score += 30
            
            # 2. Bollinger Bands Lower Touch
            if current_price <= bb_lower * 1.005:  # Within 0.5% of lower band
                signals['entry_signals'].append({
                    'type': 'BB Lower Touch',
                    'strength': 'medium',
                    'description': 'Price near lower Bollinger Band - potential bounce',
                    'entry_price': current_price,
                    'stop_loss': bb_lower * 0.98,
                    'target': (bb_upper + bb_lower) / 2  # Middle band target
                })
                entry_score += 20
            
            # 3. EMA Golden Cross
            if ema_9 > ema_21 and trend == 'bullish':
                signals['entry_signals'].append({
                    'type': 'EMA Golden Cross',
                    'strength': 'strong',
                    'description': 'EMA 9 above EMA 21 with bullish trend',
                    'entry_price': current_price,
                    'stop_loss': ema_21 * 0.98,
                    'target': current_price * 1.08
                })
                entry_score += 35
            
            # 4. MACD Bullish Crossover
            if macd and macd_signal and macd > macd_signal and macd > 0:
                signals['entry_signals'].append({
                    'type': 'MACD Bullish',
                    'strength': 'strong',
                    'description': 'MACD above signal line and positive',
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.96,
                    'target': current_price * 1.06
                })
                entry_score += 25
            
            # 5. Support Level Bounce
            support_levels = self.technical_analyzer.calculate_support_levels(self.price_history)
            for support in support_levels:
                if abs(current_price - support) / support < 0.01:  # Within 1% of support
                    signals['entry_signals'].append({
                        'type': 'Support Bounce',
                        'strength': 'medium',
                        'description': f'Price near support level ₹{support:.2f}',
                        'entry_price': current_price,
                        'stop_loss': support * 0.98,
                        'target': current_price * 1.04
                    })
                    entry_score += 15
                    break
            
            # EXIT SIGNAL ANALYSIS
            
            # 1. RSI Overbought Exit
            if rsi > 70:
                signals['exit_signals'].append({
                    'type': 'RSI Overbought',
                    'strength': 'strong',
                    'description': f'RSI at {rsi:.1f} indicates overbought condition',
                    'exit_price': current_price,
                    'reason': 'Take profit before potential reversal'
                })
                exit_score += 30
            
            # 2. Bollinger Bands Upper Touch
            if current_price >= bb_upper * 0.995:  # Within 0.5% of upper band
                signals['exit_signals'].append({
                    'type': 'BB Upper Touch',
                    'strength': 'medium',
                    'description': 'Price near upper Bollinger Band - potential reversal',
                    'exit_price': current_price,
                    'reason': 'Take profit at resistance'
                })
                exit_score += 20
            
            # 3. EMA Death Cross
            if ema_9 < ema_21 and trend == 'bearish':
                signals['exit_signals'].append({
                    'type': 'EMA Death Cross',
                    'strength': 'strong',
                    'description': 'EMA 9 below EMA 21 with bearish trend',
                    'exit_price': current_price,
                    'reason': 'Trend reversal signal'
                })
                exit_score += 35
            
            # 4. MACD Bearish Crossover
            if macd and macd_signal and macd < macd_signal:
                signals['exit_signals'].append({
                    'type': 'MACD Bearish',
                    'strength': 'medium',
                    'description': 'MACD below signal line',
                    'exit_price': current_price,
                    'reason': 'Momentum turning negative'
                })
                exit_score += 20
            
            # 5. Resistance Level Rejection
            resistance_levels = self.technical_analyzer.calculate_resistance_levels(self.price_history)
            for resistance in resistance_levels:
                if abs(current_price - resistance) / resistance < 0.01:  # Within 1% of resistance
                    signals['exit_signals'].append({
                        'type': 'Resistance Rejection',
                        'strength': 'medium',
                        'description': f'Price near resistance level ₹{resistance:.2f}',
                        'exit_price': current_price,
                        'reason': 'Take profit at resistance'
                    })
                    exit_score += 15
                    break
            
            # OVERALL DECISION
            net_score = entry_score - exit_score
            
            if net_score > 40:
                signals['overall_action'] = 'strong_buy'
                signals['confidence'] = min(90, 60 + net_score)
                signals['risk_level'] = 'low'
            elif net_score > 20:
                signals['overall_action'] = 'buy'
                signals['confidence'] = min(80, 50 + net_score)
                signals['risk_level'] = 'medium'
            elif net_score < -40:
                signals['overall_action'] = 'strong_sell'
                signals['confidence'] = min(90, 60 + abs(net_score))
                signals['risk_level'] = 'low'
            elif net_score < -20:
                signals['overall_action'] = 'sell'
                signals['confidence'] = min(80, 50 + abs(net_score))
                signals['risk_level'] = 'medium'
            else:
                signals['overall_action'] = 'hold'
                signals['confidence'] = 40
                signals['risk_level'] = 'medium'
            
            # STOP LOSS AND TARGET CALCULATIONS
            if signals['overall_action'] in ['buy', 'strong_buy']:
                # Calculate stop loss levels
                atr_stop = current_price * 0.97  # 3% ATR-based stop
                support_stop = min(support_levels) * 0.99 if support_levels else current_price * 0.95
                signals['stop_loss_levels'] = [
                    {'type': 'ATR Stop', 'level': atr_stop},
                    {'type': 'Support Stop', 'level': support_stop}
                ]
                
                # Calculate target levels
                signals['target_levels'] = [
                    {'type': 'T1 (3%)', 'level': current_price * 1.03, 'probability': 70},
                    {'type': 'T2 (5%)', 'level': current_price * 1.05, 'probability': 50},
                    {'type': 'T3 (8%)', 'level': current_price * 1.08, 'probability': 30}
                ]
            
            elif signals['overall_action'] in ['sell', 'strong_sell']:
                # For short positions
                resistance_stop = max(resistance_levels) * 1.01 if resistance_levels else current_price * 1.05
                signals['stop_loss_levels'] = [
                    {'type': 'ATR Stop', 'level': current_price * 1.03},
                    {'type': 'Resistance Stop', 'level': resistance_stop}
                ]
                
                signals['target_levels'] = [
                    {'type': 'T1 (3%)', 'level': current_price * 0.97, 'probability': 70},
                    {'type': 'T2 (5%)', 'level': current_price * 0.95, 'probability': 50},
                    {'type': 'T3 (8%)', 'level': current_price * 0.92, 'probability': 30}
                ]
            
        except Exception as e:
            logger.error(f"Entry/Exit analysis error: {e}")
        
        return signals

>Current Price:</b> ₹{price:.2f}

{action_emoji} <b>AI Recommendation:</b> {action.replace('_', ' ').upper()}
📊 <b>Confidence:</b> {confidence}%
⚠️ <b>Risk Level:</b> {risk_level.title()}

🔵 <b>ENTRY SIGNALS:</b>
            """
            
            entry_signals = signals.get('entry_signals', [])
            if entry_signals:
                for i, signal in enumerate(entry_signals[:3], 1):
                    strength_emoji = "🔥" if signal['strength'] == 'strong' else "⚡"
                    message += f"""
{i}. {strength_emoji} <b>{signal['type']}</b>
   • {signal['description']}
   • Entry: ₹{signal['entry_price']:.2f}
   • Stop Loss: ₹{signal['stop_loss']:.2f}
   • Target: ₹{signal['target']:.2f}
                    """
            else:
                message += "\n• No strong entry signals detected"
            
            message += f"\n\n🔴 <b>EXIT SIGNALS:</b>"
            
            exit_signals = signals.get('exit_signals', [])
            if exit_signals:
                for i, signal in enumerate(exit_signals[:3], 1):
                    strength_emoji = "🔥" if signal['strength'] == 'strong' else "⚡"
                    message += f"""
{i}. {strength_emoji} <b>{signal['type']}</b>
   • {signal['description']}
   • Exit: ₹{signal['exit_price']:.2f}
   • Reason: {signal['reason']}
                    """
            else:
                message += "\n• No strong exit signals detected"
            
            # Stop Loss Levels
            stop_levels = signals.get('stop_loss_levels', [])
            if stop_levels:
                message += f"\n\n🛑 <b>STOP LOSS LEVELS:</b>"
                for stop in stop_levels[:2]:
                    message += f"\n• {stop['type']}: ₹{stop['level']:.2f}"
            
            # Target Levels
            target_levels = signals.get('target_levels', [])
            if target_levels:
                message += f"\n\n🎯 <b>TARGET LEVELS:</b>"
                for target in target_levels[:3]:
                    message += f"\n• {target['type']}: ₹{target['level']:.2f} ({target['probability']}%)"
            
            # Key Technical Levels
            message += f"\n\n📊 <b>KEY TECHNICAL LEVELS:</b>"
            
            support_levels = technical.get('support_levels', [])
            if support_levels:
                support_str = ', '.join([f"₹{s:.2f}" for s in support_levels[:3]])
                message += f"\n• Support: {support_str}"
            
            resistance_levels = technical.get('resistance_levels', [])
            if resistance_levels:
                resistance_str = ', '.join([f"₹{r:.2f}" for r in resistance_levels[:3]])
                message += f"\n• Resistance: {resistance_str}"
            
            # Current Technical Status
            message += f"\n\n📈 <b>CURRENT STATUS:</b>"
            message += f"\n• RSI: {technical.get('rsi', 'N/A'):.1f} ({technical.get('rsi_signal', 'N/A')})"
            message += f"\n• EMA Cross: {technical.get('ema_crossover', 'N/A').title()}"
            message += f"\n• BB Position: {technical.get('bb_position', 'N/A').replace('_', ' ').title()}"
            message += f"\n• Trend: {technical.get('trend', 'N/A').title()}"
            
            # Risk Management Tips
            message += f"\n\n💡 <b>RISK MANAGEMENT:</b>"
            if action in ['buy', 'strong_buy']:
                message += f"\n• Position Size: Max 2-3% of portfolio"
                message += f"\n• Risk-Reward: Minimum 1:2 ratio"
                message += f"\n• Trail stop loss after 3% profit"
            elif action in ['sell', 'strong_sell']:
                message += f"\n• Book profits on existing longs"
                message += f"\n• Avoid new long positions"
                message += f"\n• Consider short positions with strict SL"
            else:
                message += f"\n• Wait for clearer signals"
                message += f"\n• Prepare for breakout/breakdown"
                message += f"\n• Keep cash reserves ready"
            
            message += f"\n\n⏰ <b>Analysis Time:</b> {data['timestamp'].strftime('%H:%M:%S')}"
            message += f"\n\n<i>⚠️ For educational purposes only. Not financial advice.</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"Entry/Exit message error: {e}")
            return "❌ Error processing entry/exit analysis."

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices) if prices else 0
            
            multiplier = 2 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except:
            return 0.0
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < slow:
                return 0.0, 0.0, 0.0
            
            ema_fast = TechnicalAnalyzer.calculate_ema(prices, fast)
            ema_slow = TechnicalAnalyzer.calculate_ema(prices, slow)
            
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line (EMA of MACD)
            macd_values = []
            for i in range(slow, len(prices)):
                subset = prices[:i+1]
                ema_f = TechnicalAnalyzer.calculate_ema(subset, fast)
                ema_s = TechnicalAnalyzer.calculate_ema(subset, slow)
                macd_values.append(ema_f - ema_s)
            
            if len(macd_values) >= signal:
                signal_line = TechnicalAnalyzer.calculate_ema(macd_values, signal)
            else:
                signal_line = macd_line
            
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
        except:
            return 0.0, 0.0, 0.0
    
    @staticmethod
    def calculate_support_levels(prices: List[float], window: int = 20) -> List[float]:
        """Calculate multiple support levels"""
        try:
            if len(prices) < window:
                return [min(prices)] if prices else [0]
            
            supports = []
            recent_prices = prices[-50:] if len(prices) >= 50 else prices
            
            # Find local lows
            for i in range(window, len(recent_prices) - window):
                is_low = True
                current = recent_prices[i]
                
                for j in range(i - window, i + window):
                    if j != i and recent_prices[j] < current:
                        is_low = False
                        break
                
                if is_low:
                    supports.append(current)
            
            # Add overall minimum
            supports.append(min(recent_prices))
            
            # Remove duplicates and sort
            supports = sorted(list(set(supports)))
            return supports[-3:] if len(supports) > 3 else supports
        except:
            return [min(prices)] if prices else [0]
    
    @staticmethod
    def calculate_resistance_levels(prices: List[float], window: int = 20) -> List[float]:
        """Calculate multiple resistance levels"""
        try:
            if len(prices) < window:
                return [max(prices)] if prices else [0]
            
            resistances = []
            recent_prices = prices[-50:] if len(prices) >= 50 else prices
            
            # Find local highs
            for i in range(window, len(recent_prices) - window):
                is_high = True
                current = recent_prices[i]
                
                for j in range(i - window, i + window):
                    if j != i and recent_prices[j] > current:
                        is_high = False
                        break
                
                if is_high:
                    resistances.append(current)
            
            # Add overall maximum
            resistances.append(max(recent_prices))
            
            # Remove duplicates and sort
            resistances = sorted(list(set(resistances)), reverse=True)
            return resistances[-3:] if len(resistances) > 3 else resistances
        except:
            return [max(prices)] if prices else [0]

        elif command == '/entry' or command == '/exit':
            entry_exit_msg = self.data_fetcher.get_entry_exit_message()
            self.send_message(chat_id, entry_exit_msg)

