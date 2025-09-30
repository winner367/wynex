import pandas as pd
from typing import Dict, List, Union, Any
import numpy as np
import json
import os
from datetime import datetime
import logging

# Import required dependencies
from advanced_pattern_recognition import PatternRecognition
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from adaptive_risk_management import AdaptiveRiskManager

# Import TA-Lib with fallback
try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    print("TA-Lib not available. Using fallback implementations.")

# Fallback implementations for TA-Lib functions
def fallback_rsi(data, timeperiod=14):
    """Fallback implementation of RSI using pandas"""
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=timeperiod).mean()
    avg_loss = loss.rolling(window=timeperiod).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fallback_sma(data, timeperiod=30):
    """Fallback implementation of Simple Moving Average"""
    return data.rolling(window=timeperiod).mean()

def fallback_ema(data, timeperiod=30):
    """Fallback implementation of Exponential Moving Average"""
    return data.ewm(span=timeperiod, adjust=False).mean()

def fallback_macd(data, fastperiod=12, slowperiod=26, signalperiod=9):
    """Fallback implementation of MACD"""
    fast_ema = fallback_ema(data, fastperiod)
    slow_ema = fallback_ema(data, slowperiod)
    macd_line = fast_ema - slow_ema
    signal_line = fallback_ema(macd_line, signalperiod)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# Function to get the appropriate TA function (either from TA-Lib or fallback)
def get_ta_func(func_name):
    """Get the appropriate TA function based on availability"""
    if HAS_TALIB:
        return getattr(talib, func_name)
    else:
        fallbacks = {
            'RSI': fallback_rsi,
            'SMA': fallback_sma,
            'EMA': fallback_ema,
            'MACD': fallback_macd
        }
        return fallbacks.get(func_name)

class StrategyEngine:
    """Engine for implementing and executing trading strategies"""
    
    def __init__(self):
        """Initialize the strategy engine"""
        self.pattern_recognition = PatternRecognition()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.risk_manager = AdaptiveRiskManager()
        
        # Strategy registry
        self.strategies = {
            'pattern_based': self.pattern_based_strategy,
            'trend_following': self.trend_following_strategy,
            'mean_reversion': self.mean_reversion_strategy,
            'breakout': self.breakout_strategy,
            'multi_timeframe': self.multi_timeframe_strategy
        }
        
        # Current strategy
        self.current_strategy = 'multi_timeframe'
        
    def execute_strategy(self, 
                        ohlc_data: pd.DataFrame,
                        ohlc_data_dict: Dict[str, pd.DataFrame],
                        market: str,
                        trade_types: List[str],
                        account_balance: float) -> Dict[str, Union[str, float]]:
        """
        Execute the selected trading strategy
        
        Args:
            ohlc_data: OHLC price data for primary timeframe
            ohlc_data_dict: Dictionary of OHLC data for multiple timeframes
            market: Market being traded
            trade_types: Available trade types
            account_balance: Current account balance
            
        Returns:
            Dictionary with strategy results
        """
        # Update the risk manager with current balance
        self.risk_manager.update_balance(account_balance)
        
        # Get available strategies for this data
        available_strategies = {}
        for strategy_name, strategy_func in self.strategies.items():
            if strategy_name == self.current_strategy:
                available_strategies[strategy_name] = strategy_func
        
        # Execute selected strategy
        strategy_func = self.strategies.get(self.current_strategy)
        if strategy_func:
            return strategy_func(ohlc_data, ohlc_data_dict, market, trade_types)
        else:
            # Fallback to multi-timeframe strategy
            return self.multi_timeframe_strategy(ohlc_data, ohlc_data_dict, market, trade_types)
    
    def pattern_based_strategy(self, 
                          ohlc_data: pd.DataFrame,
                          ohlc_data_dict: Dict[str, pd.DataFrame],
                          market: str, 
                          trade_types: List[str]) -> Dict[str, Union[str, float]]:
        """
        Implements a candlestick pattern-based strategy
        
        Args:
            ohlc_data: OHLC price data
            ohlc_data_dict: Dictionary mapping timeframe to OHLC data
            market: Market being traded
            trade_types: List of available trade types
            
        Returns:
            Dictionary with strategy results
        """
        # Initialize empty result
        result = {
            'trade_type': None,
            'probability': 0.0,
            'confidence': 0.0,
            'stake_multiplier': 1.0
        }
        
        # Ensure we have enough data
        if len(ohlc_data) < 30:
            return result
        
        # Since we're not using the talib pattern recognition functions,
        # we'll implement a simple pattern detection system
        
        # Get recent candles
        open_prices = ohlc_data['open'].values
        close_prices = ohlc_data['close'].values
        high_prices = ohlc_data['high'].values
        low_prices = ohlc_data['low'].values
        
        # Get functions for technical indicators
        ema_func = get_ta_func('EMA')
        
        # Calculate EMAs for trend context
        if HAS_TALIB:
            ema20 = ema_func(close_prices, timeperiod=20)
        else:
            ema20 = ema_func(ohlc_data['close'], timeperiod=20).values
        
        # Current trend
        trend_bullish = close_prices[-1] > ema20[-1]
        
        # Check for hammer pattern (bullish)
        def is_hammer(i):
            body_size = abs(close_prices[i] - open_prices[i])
            if body_size == 0:
                return False
                
            lower_shadow = min(open_prices[i], close_prices[i]) - low_prices[i]
            upper_shadow = high_prices[i] - max(open_prices[i], close_prices[i])
            
            # Hammer: lower shadow should be at least 2x the body
            return (lower_shadow >= 2 * body_size and 
                    upper_shadow <= 0.2 * body_size and
                    close_prices[i] > open_prices[i])
        
        # Check for shooting star pattern (bearish)
        def is_shooting_star(i):
            body_size = abs(close_prices[i] - open_prices[i])
            if body_size == 0:
                return False
                
            lower_shadow = min(open_prices[i], close_prices[i]) - low_prices[i]
            upper_shadow = high_prices[i] - max(open_prices[i], close_prices[i])
            
            # Shooting star: upper shadow should be at least 2x the body
            return (upper_shadow >= 2 * body_size and 
                    lower_shadow <= 0.2 * body_size and
                    close_prices[i] < open_prices[i])
        
        # Check for engulfing patterns
        def is_bullish_engulfing(i):
            return (open_prices[i] < close_prices[i-1] and
                    close_prices[i] > open_prices[i-1] and
                    close_prices[i] > open_prices[i] and
                    open_prices[i-1] > close_prices[i-1])
        
        def is_bearish_engulfing(i):
            return (open_prices[i] > close_prices[i-1] and
                    close_prices[i] < open_prices[i-1] and
                    close_prices[i] < open_prices[i] and
                    open_prices[i-1] < close_prices[i-1])
        
        # Look for patterns in the last few candles
        bullish_patterns = 0
        bearish_patterns = 0
        
        for i in range(len(ohlc_data) - 5, len(ohlc_data)):
            if i <= 0:  # Skip first candle since we need previous candle for some patterns
                continue
                
            if is_hammer(i):
                bullish_patterns += 1
            if is_shooting_star(i):
                bearish_patterns += 1
            if is_bullish_engulfing(i):
                bullish_patterns += 1
            if is_bearish_engulfing(i):
                bearish_patterns += 1
        
        # Generate signal based on detected patterns
        if bullish_patterns > 0 and trend_bullish:
            # Bullish signal
            if 'CALL' in trade_types:
                result['trade_type'] = 'CALL'
                result['probability'] = 0.6 + (0.05 * bullish_patterns)
                result['confidence'] = 0.65
                
            elif 'RISE' in trade_types:
                result['trade_type'] = 'RISE'
                result['probability'] = 0.6 + (0.05 * bullish_patterns)
                result['confidence'] = 0.65
                
        elif bearish_patterns > 0 and not trend_bullish:
            # Bearish signal
            if 'PUT' in trade_types:
                result['trade_type'] = 'PUT'
                result['probability'] = 0.6 + (0.05 * bearish_patterns)
                result['confidence'] = 0.65
                
            elif 'FALL' in trade_types:
                result['trade_type'] = 'FALL'
                result['probability'] = 0.6 + (0.05 * bearish_patterns)
                result['confidence'] = 0.65
        
        # Adjust confidence based on pattern strength
        pattern_count = max(bullish_patterns, bearish_patterns)
        if pattern_count >= 3:
            result['confidence'] = 0.8
            result['stake_multiplier'] = 1.5
        elif pattern_count >= 2:
            result['confidence'] = 0.7
            result['stake_multiplier'] = 1.2
        else:
            result['stake_multiplier'] = 1.0
            
        return result
    
    def trend_following_strategy(self, 
                                ohlc_data: pd.DataFrame,
                                ohlc_data_dict: Dict[str, pd.DataFrame],
                                market: str, 
                                trade_types: List[str]) -> Dict[str, Union[str, float]]:
        """
        Execute trend-following trading strategy
        
        Args:
            ohlc_data: OHLC price data for primary timeframe
            ohlc_data_dict: Dictionary of OHLC data for multiple timeframes
            market: Market being traded
            trade_types: Available trade types
            
        Returns:
            Dictionary with strategy results
        """
        # Create a signal result
        result = {
            'trade_type': None,
            'probability': 0.0,
            'confidence': 0.0,
            'stake_multiplier': 1.0
        }
        
        # Ensure we have enough data
        if len(ohlc_data) < 30:
            return result
        
        # Calculate Moving Averages
        close_prices = ohlc_data['close'].values
        
        # Use our function getter instead of direct talib import
        sma_func = get_ta_func('SMA')
        ema_func = get_ta_func('EMA')
        
        # Calculate moving averages
        if HAS_TALIB:
            sma20 = sma_func(close_prices, timeperiod=20)
            ema10 = ema_func(close_prices, timeperiod=10)
        else:
            sma20 = sma_func(ohlc_data['close'], timeperiod=20).values
            ema10 = ema_func(ohlc_data['close'], timeperiod=10).values
        
        # Get current values
        current_price = close_prices[-1]
        current_sma20 = sma20[-1]
        current_ema10 = ema10[-1]
        
        # Determine if we're in an uptrend or downtrend
        uptrend = current_price > current_sma20 and current_ema10 > current_sma20
        downtrend = current_price < current_sma20 and current_ema10 < current_sma20
        
        # Generate trade signal based on trend and price momentum
        if uptrend:
            # In uptrend, look for call/buy opportunities
            if 'CALL' in trade_types:
                result['trade_type'] = 'CALL'
                result['probability'] = 0.65
                result['confidence'] = 0.7
                
            elif 'RISEFALL' in trade_types:
                result['trade_type'] = 'RISEFALL'
                result['probability'] = 0.65
                result['confidence'] = 0.7
                
            # For digit options in uptrend, even digits tend to appear more often
            elif 'DIGITEVEN' in trade_types:
                result['trade_type'] = 'DIGITEVEN'
                result['probability'] = 0.55  # Lower probability for digit
                result['confidence'] = 0.6
                
        elif downtrend:
            # In downtrend, look for put/sell opportunities
            if 'PUT' in trade_types:
                result['trade_type'] = 'PUT'
                result['probability'] = 0.65
                result['confidence'] = 0.7
                
            elif 'FALL' in trade_types:
                result['trade_type'] = 'FALL'
                result['probability'] = 0.65
                result['confidence'] = 0.7
                
            # For digit options in downtrend, odd digits tend to appear more often
            elif 'DIGITODD' in trade_types:
                result['trade_type'] = 'DIGITODD'
                result['probability'] = 0.55  # Lower probability for digit
                result['confidence'] = 0.6
        
        # Calculate stake multiplier based on signal strength
        if result['probability'] > 0.7:
            result['stake_multiplier'] = 1.5
        elif result['probability'] > 0.6:
            result['stake_multiplier'] = 1.2
        else:
            result['stake_multiplier'] = 1.0
        
        return result
    
    def mean_reversion_strategy(self, 
                              ohlc_data: pd.DataFrame,
                              ohlc_data_dict: Dict[str, pd.DataFrame],
                              market: str, 
                              trade_types: List[str]) -> Dict[str, Union[str, float]]:
        """
        Execute mean reversion trading strategy
        
        Args:
            ohlc_data: OHLC price data for primary timeframe
            ohlc_data_dict: Dictionary of OHLC data for multiple timeframes
            market: Market being traded
            trade_types: Available trade types
            
        Returns:
            Dictionary with strategy results
        """
        # Initialize empty result
        result = {
            'trade_type': None,
            'probability': 0.0,
            'confidence': 0.0,
            'stake_multiplier': 1.0
        }
        
        # Ensure we have enough data
        if len(ohlc_data) < 30:
            return result
        
        # Calculate RSI
        close_prices = ohlc_data['close'].values
        
        # Get appropriate RSI function
        rsi_func = get_ta_func('RSI')
        
        # Calculate RSI with proper handling for TA-Lib or fallback
        if HAS_TALIB:
            rsi = rsi_func(close_prices, timeperiod=14)
        else:
            rsi = rsi_func(ohlc_data['close'], timeperiod=14).values
        
        # Get current RSI
        current_rsi = rsi[-1]
        
        # Check for overbought/oversold conditions
        oversold = current_rsi <= 30
        overbought = current_rsi >= 70
        
        # Generate signals based on RSI conditions
        if oversold:
            # Oversold condition suggests a potential rise
            if 'CALL' in trade_types:
                result['trade_type'] = 'CALL'
                result['probability'] = 0.7
                result['confidence'] = 0.65
                
            elif 'RISE' in trade_types:
                result['trade_type'] = 'RISE'
                result['probability'] = 0.7
                result['confidence'] = 0.65
                
            # For digit options, even digits are more common in rising markets
            elif 'DIGITEVEN' in trade_types:
                result['trade_type'] = 'DIGITEVEN'
                result['probability'] = 0.55
                result['confidence'] = 0.6
                
        elif overbought:
            # Overbought condition suggests a potential fall
            if 'PUT' in trade_types:
                result['trade_type'] = 'PUT'
                result['probability'] = 0.7
                result['confidence'] = 0.65
                
            elif 'FALL' in trade_types:
                result['trade_type'] = 'FALL'
                result['probability'] = 0.7
                result['confidence'] = 0.65
                
            # For digit options, odd digits are more common in falling markets
            elif 'DIGITODD' in trade_types:
                result['trade_type'] = 'DIGITODD'
                result['probability'] = 0.55
                result['confidence'] = 0.6
        
        # Determine stake size based on RSI extremity
        if current_rsi <= 20 or current_rsi >= 80:
            # More extreme RSI values suggest higher confidence
            result['stake_multiplier'] = 1.5
            result['confidence'] = min(0.8, result['confidence'] + 0.1)
        elif current_rsi <= 25 or current_rsi >= 75:
            result['stake_multiplier'] = 1.2
        else:
            result['stake_multiplier'] = 1.0
        
        return result
    
    def breakout_strategy(self, 
                         ohlc_data: pd.DataFrame,
                         ohlc_data_dict: Dict[str, pd.DataFrame],
                         market: str, 
                         trade_types: List[str]) -> Dict[str, Union[str, float]]:
        """
        Implements a breakout strategy based on support/resistance levels
        
        Args:
            ohlc_data: OHLC price data
            ohlc_data_dict: Dictionary mapping timeframe to OHLC data
            market: Market being traded
            trade_types: List of available trade types
            
        Returns:
            Dictionary with strategy results
        """
        # Initialize empty result
        result = {
            'trade_type': None,
            'probability': 0.0,
            'confidence': 0.0,
            'stake_multiplier': 1.0
        }
        
        # Ensure we have enough data
        if len(ohlc_data) < 30:
            return result
            
        # Get price data
        close_prices = ohlc_data['close'].values
        high_prices = ohlc_data['high'].values
        low_prices = ohlc_data['low'].values
        
        # Get SMA for trend direction
        sma_func = get_ta_func('SMA')
        
        if HAS_TALIB:
            sma50 = sma_func(close_prices, timeperiod=50)
        else:
            sma50 = sma_func(ohlc_data['close'], timeperiod=50).values
            
        # Identify recent highs and lows (simple approach)
        window = 10
        resistance_level = max(high_prices[-window:-1])
        support_level = min(low_prices[-window:-1])
        
        # Current price and SMA
        current_price = close_prices[-1]
        current_sma = sma50[-1]
        
        # Check for breakouts
        resistance_breakout = current_price > resistance_level * 1.005  # 0.5% breakout
        support_breakout = current_price < support_level * 0.995  # 0.5% breakout
        
        # Confirm with trend direction
        uptrend = current_price > current_sma
        
        # Generate signals based on breakouts
        if resistance_breakout and uptrend:
            # Bullish breakout
            if 'CALL' in trade_types:
                result['trade_type'] = 'CALL'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
            elif 'RISE' in trade_types:
                result['trade_type'] = 'RISE'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
        elif support_breakout and not uptrend:
            # Bearish breakout
            if 'PUT' in trade_types:
                result['trade_type'] = 'PUT'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
            elif 'FALL' in trade_types:
                result['trade_type'] = 'FALL'
                result['probability'] = 0.7
                result['confidence'] = 0.75
        
        # Determine stake size based on breakout strength
        breakout_strength = (current_price - resistance_level) / resistance_level if resistance_breakout else (support_level - current_price) / support_level
        
        if breakout_strength > 0.01:  # 1% strong breakout
            result['stake_multiplier'] = 1.5
            result['confidence'] = min(0.85, result['confidence'] + 0.1)
        else:
            result['stake_multiplier'] = 1.0
            
        return result
    
    def multi_timeframe_strategy(self, 
                            ohlc_data: pd.DataFrame,
                            ohlc_data_dict: Dict[str, pd.DataFrame],
                            market: str, 
                            trade_types: List[str]) -> Dict[str, Union[str, float]]:
        """
        Implements a strategy that analyzes multiple timeframes for confluence
        
        Args:
            ohlc_data: OHLC price data for primary timeframe
            ohlc_data_dict: Dictionary of OHLC data for multiple timeframes
            market: Market being traded
            trade_types: Available trade types
            
        Returns:
            Dictionary with strategy results
        """
        # Initialize empty result
        result = {
            'trade_type': None,
            'probability': 0.0,
            'confidence': 0.0,
            'stake_multiplier': 1.0
        }
        
        # Ensure we have data for at least 3 timeframes
        required_timeframes = ['1m', '5m', '15m']
        for tf in required_timeframes:
            if tf not in ohlc_data_dict or len(ohlc_data_dict[tf]) < 30:
                return result
        
        # Get functions for technical indicators
        rsi_func = get_ta_func('RSI')
        ema_func = get_ta_func('EMA')
        
        # Track signals across timeframes
        bullish_signals = 0
        bearish_signals = 0
        
        # Analyze each timeframe
        for timeframe in required_timeframes:
            tf_data = ohlc_data_dict[timeframe]
            close_prices = tf_data['close'].values
            
            # Calculate indicators
            if HAS_TALIB:
                rsi = rsi_func(close_prices, timeperiod=14)
                ema20 = ema_func(close_prices, timeperiod=20)
                ema50 = ema_func(close_prices, timeperiod=50)
            else:
                rsi = rsi_func(tf_data['close'], timeperiod=14).values
                ema20 = ema_func(tf_data['close'], timeperiod=20).values
                ema50 = ema_func(tf_data['close'], timeperiod=50).values
            
            # Get current values
            current_price = close_prices[-1]
            current_rsi = rsi[-1]
            current_ema20 = ema20[-1]
            current_ema50 = ema50[-1]
            
            # Check for bullish signals
            if current_price > current_ema20 and current_ema20 > current_ema50:
                bullish_signals += 1
            
            # Check for bearish signals
            if current_price < current_ema20 and current_ema20 < current_ema50:
                bearish_signals += 1
            
            # Add RSI confirmation
            if current_rsi > 60:
                bullish_signals += 0.5
            elif current_rsi < 40:
                bearish_signals += 0.5
        
        # Determine overall signal based on timeframe confluence
        if bullish_signals >= 2.5 and bullish_signals > bearish_signals:
            # Strong bullish signal
            if 'CALL' in trade_types:
                result['trade_type'] = 'CALL'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
            elif 'RISE' in trade_types:
                result['trade_type'] = 'RISE'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
        elif bearish_signals >= 2.5 and bearish_signals > bullish_signals:
            # Strong bearish signal
            if 'PUT' in trade_types:
                result['trade_type'] = 'PUT'
                result['probability'] = 0.7
                result['confidence'] = 0.75
                
            elif 'FALL' in trade_types:
                result['trade_type'] = 'FALL'
                result['probability'] = 0.7
                result['confidence'] = 0.75
        
        # Adjust confidence based on signal strength
        signal_strength = max(bullish_signals, bearish_signals)
        if signal_strength >= 4:
            result['confidence'] = 0.85
            result['stake_multiplier'] = 1.5
        elif signal_strength >= 3:
            result['confidence'] = 0.75
            result['stake_multiplier'] = 1.2
        else:
            result['stake_multiplier'] = 1.0
            
        return result
    
    def set_strategy(self, strategy_name: str) -> bool:
        """
        Set the current trading strategy
        
        Args:
            strategy_name: Name of the strategy to use
            
        Returns:
            True if strategy was set successfully
        """
        if strategy_name in self.strategies:
            self.current_strategy = strategy_name
            return True
        return False
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategies
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())