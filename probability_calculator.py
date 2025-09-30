import numpy as np
import pandas as pd
from typing import Dict, Union, List, Tuple
from advanced_pattern_recognition import PatternRecognition
from multi_timeframe_analyzer import MultiTimeframeAnalyzer

class ProbabilityCalculator:
    """Calculate probabilities for binary options outcomes"""
    
    def __init__(self):
        """Initialize the probability calculator"""
        self.pattern_recognition = PatternRecognition()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        
    def calculate_digit_probability(self, digit_history: List[int], target_digit: int) -> float:
        """
        Calculate the probability of a specific digit occurring next
        
        Args:
            digit_history: List of past digits
            target_digit: The digit to calculate probability for
            
        Returns:
            Probability (0 to 1)
        """
        if not digit_history:
            return 0.1  # Default to 10% for each digit (0-9)
            
        # Count occurrences of each digit
        counts = np.zeros(10)
        for digit in digit_history:
            if 0 <= digit <= 9:
                counts[digit] += 1
                
        # Calculate probabilities
        total = sum(counts)
        probabilities = counts / total if total > 0 else np.ones(10) / 10
        
        return probabilities[target_digit]
        
    def calculate_pattern_probability(self, ohlc_data: pd.DataFrame, 
                                     trade_type: str, 
                                     market: str) -> Tuple[float, float]:
        """
        Calculate probability based on price patterns and indicators
        
        Args:
            ohlc_data: DataFrame with OHLC price data
            trade_type: Type of trade (e.g., 'CALL', 'PUT', 'DIGITEVEN', etc.)
            market: Market being traded
            
        Returns:
            Tuple of (probability, confidence)
        """
        # Get pattern recognition signals
        pattern_signals = self.pattern_recognition.get_pattern_signals(ohlc_data)
        
        # Process signals based on trade type
        if trade_type in ['CALL', 'RISEFALL', 'HIGHERLOWER', 'TOUCHNOTOUCH']:
            # Bullish trades want upward movement
            bullish_bias = sum(v for k, v in pattern_signals.items()) / len(pattern_signals)
            probability = (bullish_bias + 1) / 2  # Convert from [-1, 1] to [0, 1]
            
        elif trade_type in ['PUT', 'EXPIRYMISS']:
            # Bearish trades want downward movement
            bearish_bias = -sum(v for k, v in pattern_signals.items()) / len(pattern_signals)
            probability = (bearish_bias + 1) / 2  # Convert from [-1, 1] to [0, 1]
            
        elif trade_type in ['DIGITEVEN']:
            # Check last few digits for even/odd patterns
            if 'close' in ohlc_data.columns:
                last_prices = ohlc_data['close'].values[-10:]
                # Extract the last digit of each price and check if it's even
                last_digits = [int(str(price).replace('.', '')[-1]) for price in last_prices]
                even_count = sum(1 for d in last_digits if d % 2 == 0)
                probability = even_count / len(last_digits)
                
        elif trade_type in ['DIGITODD']:
            # Check last few digits for even/odd patterns
            if 'close' in ohlc_data.columns:
                last_prices = ohlc_data['close'].values[-10:]
                # Extract the last digit of each price and check if it's odd
                last_digits = [int(str(price).replace('.', '')[-1]) for price in last_prices]
                odd_count = sum(1 for d in last_digits if d % 2 == 1)
                probability = odd_count / len(last_digits)
                
        elif trade_type.startswith('DIGIT'):
            # For specific digit prediction (DIGIT0, DIGIT1, etc.)
            digit = int(trade_type.replace('DIGIT', ''))
            if 'close' in ohlc_data.columns:
                last_prices = ohlc_data['close'].values[-20:]
                # Extract the last digit of each price
                last_digits = [int(str(price).replace('.', '')[-1]) for price in last_prices]
                digit_count = sum(1 for d in last_digits if d == digit)
                probability = digit_count / len(last_digits)
                
        else:
            # Default calculation for other trade types
            probability = 0.5  # Neutral probability
            
        # Calculate confidence based on pattern consistency
        signal_values = list(pattern_signals.values())
        signal_abs = [abs(v) for v in signal_values]
        confidence = sum(signal_abs) / len(signal_abs) if signal_abs else 0.5
        
        return probability, confidence
    
    def calculate_multi_timeframe_probability(self, 
                                             ohlc_data_dict: Dict[str, pd.DataFrame],
                                             trade_type: str,
                                             market: str) -> Tuple[float, float]:
        """
        Calculate probability using multi-timeframe analysis
        
        Args:
            ohlc_data_dict: Dictionary mapping timeframe to OHLC data
            trade_type: Type of trade
            market: Market being traded
            
        Returns:
            Tuple of (probability, confidence)
        """
        # Use the multi-timeframe analyzer
        timeframe_signals = self.mtf_analyzer.analyze_timeframes(ohlc_data_dict)
        weighted_signals = self.mtf_analyzer.get_voting_signal(timeframe_signals)
        aggregated_signal = self.mtf_analyzer.get_aggregated_signal(weighted_signals)
        
        # Convert to probability
        probability = self.mtf_analyzer.get_probability_estimate(aggregated_signal)
        
        # Adjust probability based on trade type
        if trade_type in ['PUT', 'EXPIRYMISS']:
            # Invert probability for bearish trades
            probability = 1 - probability
            
        # Calculate confidence based on signal strength
        confidence = min(0.95, 0.5 + abs(aggregated_signal) / 2)
        
        return probability, confidence
    
    def get_final_probability(self, 
                             ohlc_data: pd.DataFrame,
                             ohlc_data_dict: Dict[str, pd.DataFrame],
                             trade_type: str,
                             market: str) -> Tuple[float, float]:
        """
        Get the final probability combining single and multi-timeframe analysis
        
        Args:
            ohlc_data: OHLC data for single timeframe
            ohlc_data_dict: Dictionary of OHLC data for multiple timeframes
            trade_type: Type of trade
            market: Market being traded
            
        Returns:
            Tuple of (probability, confidence)
        """
        # Get probabilities from different methods
        pattern_prob, pattern_conf = self.calculate_pattern_probability(ohlc_data, trade_type, market)
        
        if ohlc_data_dict:
            mtf_prob, mtf_conf = self.calculate_multi_timeframe_probability(ohlc_data_dict, trade_type, market)
            
            # Combine probabilities with emphasis on multi-timeframe analysis
            combined_prob = pattern_prob * 0.3 + mtf_prob * 0.7
            combined_conf = pattern_conf * 0.3 + mtf_conf * 0.7
            
            return combined_prob, combined_conf
        else:
            # Fallback to pattern probability only
            return pattern_prob, pattern_conf


class MarketAnalyzer:
    """Market analysis tools for better trading decisions"""
    
    def __init__(self):
        """Initialize market analyzer"""
        self.pattern_recognition = PatternRecognition()
        
    def calculate_volatility(self, ohlc_data: pd.DataFrame, window: int = 20) -> float:
        """
        Calculate market volatility
        
        Args:
            ohlc_data: OHLC price data
            window: Window size for volatility calculation
            
        Returns:
            Volatility measure
        """
        if 'close' not in ohlc_data.columns or len(ohlc_data) < window:
            return 1.0  # Default value if insufficient data
            
        # Calculate daily returns
        returns = ohlc_data['close'].pct_change().dropna()
        
        # Calculate rolling volatility (standard deviation of returns)
        volatility = returns.rolling(window=window).std().iloc[-1]
        
        # Annualize volatility
        annualized_vol = volatility * np.sqrt(252)  # Assuming 252 trading days
        
        return annualized_vol
        
    def calculate_trend_strength(self, ohlc_data: pd.DataFrame) -> float:
        """
        Calculate the strength of the current trend using a simple method
        
        Args:
            ohlc_data: OHLC price data
            
        Returns:
            Trend strength from 0 (no trend) to 1 (strong trend)
        """
        if len(ohlc_data) < 30:
            return 0.5  # Default if insufficient data
            
        close_prices = ohlc_data['close'].values
        
        # Calculate trend strength using price momentum and direction consistency
        returns = np.diff(close_prices)
        positive_moves = np.sum(returns > 0)
        negative_moves = np.sum(returns < 0)
        
        # Calculate trend consistency
        total_moves = positive_moves + negative_moves
        if total_moves == 0:
            return 0.5
        
        # If mostly positive moves, trend is up. If mostly negative, trend is down
        trend_consistency = max(positive_moves, negative_moves) / total_moves
        
        # Calculate momentum
        momentum = abs(close_prices[-1] - close_prices[0]) / np.mean(close_prices)
        
        # Combine consistency and momentum for final trend strength
        trend_strength = min(1.0, (trend_consistency * 0.7 + momentum * 0.3))
        
        return trend_strength
        
    def calculate_support_resistance(self, ohlc_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate support and resistance levels
        
        Args:
            ohlc_data: OHLC price data
            
        Returns:
            Dictionary with support and resistance levels
        """
        if len(ohlc_data) < 20:
            return {'support': 0, 'resistance': 0, 'current': 0}
            
        # Detect swing points
        close_prices = ohlc_data['close'].values
        swing_highs, swing_lows = self.pattern_recognition.detect_swing_points(close_prices)
        
        # Get current price
        current_price = close_prices[-1]
        
        # Find closest support (swing low below current price)
        supports = [close_prices[i] for i in swing_lows if close_prices[i] < current_price]
        support = max(supports) if supports else current_price * 0.95
        
        # Find closest resistance (swing high above current price)
        resistances = [close_prices[i] for i in swing_highs if close_prices[i] > current_price]
        resistance = min(resistances) if resistances else current_price * 1.05
        
        return {
            'support': support,
            'resistance': resistance,
            'current': current_price
        }
        
    def analyze_market_condition(self, ohlc_data: pd.DataFrame) -> Dict[str, Union[float, str]]:
        """
        Perform comprehensive market condition analysis
        
        Args:
            ohlc_data: OHLC price data
            
        Returns:
            Dictionary with market condition analysis
        """
        # Initialize result dictionary
        result = {}
        
        # Calculate volatility
        result['volatility'] = self.calculate_volatility(ohlc_data)
        
        # Calculate trend strength
        result['trend_strength'] = self.calculate_trend_strength(ohlc_data)
        
        # Get support and resistance
        levels = self.calculate_support_resistance(ohlc_data)
        result.update(levels)
        
        # Determine market condition
        if result['trend_strength'] > 0.7:
            if levels['current'] > (levels['support'] + levels['resistance']) / 2:
                result['market_condition'] = 'strong_uptrend'
            else:
                result['market_condition'] = 'strong_downtrend'
        elif result['trend_strength'] > 0.4:
            if levels['current'] > (levels['support'] + levels['resistance']) / 2:
                result['market_condition'] = 'uptrend'
            else:
                result['market_condition'] = 'downtrend'
        elif result['volatility'] > 0.2:
            result['market_condition'] = 'volatile_sideways'
        else:
            result['market_condition'] = 'ranging'
            
        # Calculate risk rating (0-100, higher = riskier)
        risk_rating = result['volatility'] * 50 + (1 - result['trend_strength']) * 50
        result['risk_rating'] = min(100, risk_rating)
        
        return result