import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MultiTimeframeAnalyzer:
    """
    Analyzes market data across multiple timeframes to find trade setups
    """
    
    def __init__(self):
        """Initialize the multi-timeframe analyzer"""
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', 'D']
        self.data = {}
        self.signals = {}
        
    def add_timeframe_data(self, timeframe, data):
        """
        Add data for a specific timeframe
        
        Args:
            timeframe: Timeframe identifier ('1m', '5m', etc.)
            data: DataFrame with OHLC data
        """
        self.data[timeframe] = data
        
    def get_timeframe_data(self, timeframe):
        """
        Get data for a specific timeframe
        
        Args:
            timeframe: Timeframe identifier
            
        Returns:
            DataFrame with OHLC data or None if not available
        """
        return self.data.get(timeframe)
        
    def analyze_all_timeframes(self):
        """
        Analyze all available timeframes
        
        Returns:
            Dictionary of signals for each timeframe
        """
        self.signals = {}
        
        for timeframe in self.data.keys():
            self.signals[timeframe] = self.analyze_timeframe(timeframe)
            
        return self.signals
        
    def analyze_timeframe(self, timeframe):
        """
        Analyze a specific timeframe
        
        Args:
            timeframe: Timeframe identifier
            
        Returns:
            Dictionary of signals for this timeframe
        """
        if timeframe not in self.data:
            return {}
            
        data = self.data[timeframe]
        
        # Generate basic signals
        signals = {
            'trend': self._detect_trend(data),
            'momentum': self._calculate_momentum(data),
            'support_resistance': self._find_support_resistance(data),
            'volatility': self._calculate_volatility(data)
        }
        
        return signals
        
    def _detect_trend(self, data):
        """
        Detect the trend in the data
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Trend information ('bullish', 'bearish', 'sideways')
        """
        if len(data) < 20:
            return 'unknown'
            
        # Simple 20-period moving average
        data['ma20'] = data['close'].rolling(window=20).mean()
        
        # Calculate if price is above, below, or near the moving average
        last_close = data['close'].iloc[-1]
        last_ma = data['ma20'].iloc[-1]
        
        # Calculate the slope of the moving average (last 5 periods)
        if len(data) >= 25:
            ma_slope = (data['ma20'].iloc[-1] - data['ma20'].iloc[-5]) / 5
        else:
            ma_slope = 0
            
        # Determine trend
        if last_close > last_ma * 1.02 and ma_slope > 0:
            return 'bullish'
        elif last_close < last_ma * 0.98 and ma_slope < 0:
            return 'bearish'
        else:
            return 'sideways'
        
    def _calculate_momentum(self, data):
        """
        Calculate momentum indicators
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Momentum information (RSI, etc.)
        """
        if len(data) < 14:
            return {'rsi': 50}
            
        # Simple RSI calculation
        delta = data['close'].diff()
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'rsi': rsi.iloc[-1],
            'rsi_signal': 'oversold' if rsi.iloc[-1] < 30 else 'overbought' if rsi.iloc[-1] > 70 else 'neutral'
        }
        
    def _find_support_resistance(self, data):
        """
        Find support and resistance levels
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Support and resistance levels
        """
        if len(data) < 20:
            return {'support': [], 'resistance': []}
            
        # Look for local highs and lows (simple method)
        highs = []
        lows = []
        
        for i in range(2, len(data) - 2):
            # Local high
            if (data['high'].iloc[i] > data['high'].iloc[i-1] and 
                data['high'].iloc[i] > data['high'].iloc[i-2] and
                data['high'].iloc[i] > data['high'].iloc[i+1] and
                data['high'].iloc[i] > data['high'].iloc[i+2]):
                highs.append(data['high'].iloc[i])
                
            # Local low
            if (data['low'].iloc[i] < data['low'].iloc[i-1] and 
                data['low'].iloc[i] < data['low'].iloc[i-2] and
                data['low'].iloc[i] < data['low'].iloc[i+1] and
                data['low'].iloc[i] < data['low'].iloc[i+2]):
                lows.append(data['low'].iloc[i])
                
        # Get the latest price
        current_price = data['close'].iloc[-1]
        
        # Filter for nearby levels
        support = [level for level in lows if level < current_price]
        resistance = [level for level in highs if level > current_price]
        
        # Get the closest levels
        if support:
            support = [max(support)]
        if resistance:
            resistance = [min(resistance)]
            
        return {
            'support': support,
            'resistance': resistance
        }
        
    def _calculate_volatility(self, data):
        """
        Calculate volatility metrics
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Volatility information
        """
        if len(data) < 20:
            return {'atr': 0, 'volatility_level': 'unknown'}
            
        # Calculate simple ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        # Calculate ATR as a percentage of price
        atr_pct = atr / data['close'].iloc[-1] * 100
        
        # Determine volatility level
        if atr_pct < 0.5:
            volatility_level = 'very_low'
        elif atr_pct < 1.0:
            volatility_level = 'low'
        elif atr_pct < 2.0:
            volatility_level = 'medium'
        elif atr_pct < 3.0:
            volatility_level = 'high'
        else:
            volatility_level = 'very_high'
            
        return {
            'atr': atr,
            'atr_pct': atr_pct,
            'volatility_level': volatility_level
        }
        
    def get_trade_recommendation(self):
        """
        Generate a trade recommendation based on multi-timeframe analysis
        
        Returns:
            Trade recommendation dictionary
        """
        if not self.signals:
            return {
                'recommendation': 'neutral',
                'confidence': 0,
                'reason': 'Insufficient data for analysis'
            }
            
        # Count bullish and bearish signals across timeframes
        bullish_count = 0
        bearish_count = 0
        total_signals = 0
        
        for tf, signals in self.signals.items():
            total_signals += 1
            
            # Check trend
            if signals.get('trend') == 'bullish':
                bullish_count += 1
            elif signals.get('trend') == 'bearish':
                bearish_count += 1
                
            # Check momentum
            momentum = signals.get('momentum', {})
            if momentum.get('rsi_signal') == 'oversold':
                bullish_count += 0.5
            elif momentum.get('rsi_signal') == 'overbought':
                bearish_count += 0.5
                
        # Calculate confidence
        if total_signals > 0:
            bullish_confidence = bullish_count / total_signals
            bearish_confidence = bearish_count / total_signals
            
            if bullish_confidence > bearish_confidence and bullish_confidence > 0.5:
                recommendation = 'bullish'
                confidence = bullish_confidence
                reason = 'Bullish signals across multiple timeframes'
            elif bearish_confidence > bullish_confidence and bearish_confidence > 0.5:
                recommendation = 'bearish'
                confidence = bearish_confidence
                reason = 'Bearish signals across multiple timeframes'
            else:
                recommendation = 'neutral'
                confidence = max(0.5, 1 - abs(bullish_confidence - bearish_confidence))
                reason = 'Mixed signals across timeframes'
        else:
            recommendation = 'neutral'
            confidence = 0
            reason = 'No timeframe data available'
            
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reason': reason
        }