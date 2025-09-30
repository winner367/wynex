import numpy as np
import pandas as pd

class PatternRecognition:
    """A simplified pattern recognition class that doesn't require TA-Lib"""
    
    def __init__(self):
        self.detected_patterns = []
    
    def analyze(self, data):
        """
        Analyze price data for patterns (simplified version)
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            List of detected patterns
        """
        # Simple implementation without TA-Lib
        self.detected_patterns = []
        
        # Implement a basic pattern detection (e.g., looking for dojis)
        self._detect_doji(data)
        self._detect_engulfing(data)
        
        return self.detected_patterns
    
    def _detect_doji(self, data):
        """Detect doji candlestick pattern"""
        if len(data) < 1:
            return
            
        # A doji has a small body (open close are very close)
        body_sizes = abs(data['close'] - data['open'])
        shadow_sizes = data['high'] - data['low']
        
        # A doji has a body size less than 10% of the total range
        doji_condition = body_sizes < (0.1 * shadow_sizes)
        
        if doji_condition.any():
            self.detected_patterns.append({
                'name': 'Doji',
                'position': np.where(doji_condition)[0][-1],
                'strength': 'Medium',
                'direction': 'Neutral'
            })
    
    def _detect_engulfing(self, data):
        """Detect engulfing candlestick pattern"""
        if len(data) < 2:
            return
            
        for i in range(1, len(data)):
            prev_body_size = abs(data['close'].iloc[i-1] - data['open'].iloc[i-1])
            curr_body_size = abs(data['close'].iloc[i] - data['open'].iloc[i])
            
            prev_bullish = data['close'].iloc[i-1] > data['open'].iloc[i-1]
            curr_bullish = data['close'].iloc[i] > data['open'].iloc[i]
            
            # Bullish engulfing
            if (not prev_bullish and curr_bullish and
                data['open'].iloc[i] < data['close'].iloc[i-1] and
                data['close'].iloc[i] > data['open'].iloc[i-1] and
                curr_body_size > prev_body_size):
                
                self.detected_patterns.append({
                    'name': 'Bullish Engulfing',
                    'position': i,
                    'strength': 'High',
                    'direction': 'Bullish'
                })
                
            # Bearish engulfing
            elif (prev_bullish and not curr_bullish and
                  data['open'].iloc[i] > data['close'].iloc[i-1] and
                  data['close'].iloc[i] < data['open'].iloc[i-1] and
                  curr_body_size > prev_body_size):
                
                self.detected_patterns.append({
                    'name': 'Bearish Engulfing',
                    'position': i,
                    'strength': 'High',  
                    'direction': 'Bearish'
                })

    def get_pattern_statistics(self):
        """Get statistics about detected patterns"""
        if not self.detected_patterns:
            return pd.DataFrame()
            
        pattern_stats = {
            'Pattern': [p['name'] for p in self.detected_patterns],
            'Direction': [p['direction'] for p in self.detected_patterns],
            'Strength': [p['strength'] for p in self.detected_patterns]
        }
        
        return pd.DataFrame(pattern_stats)

    def detect_swing_points(self, prices: np.ndarray, window: int = 5) -> tuple:
        """
        Detect swing high and low points in price data
        
        Args:
            prices: numpy array of price values
            window: lookback window for detecting swings
            
        Returns:
            Tuple of (swing_highs, swing_lows) indices
        """
        swing_highs = []
        swing_lows = []
        
        if len(prices) < window * 2:
            return np.array(swing_highs), np.array(swing_lows)
        
        for i in range(window, len(prices) - window):
            # Get the window of prices before and after the current point
            left_window = prices[i - window:i]
            right_window = prices[i + 1:i + window + 1]
            current = prices[i]
            
            # Check for swing high
            if (current > np.max(left_window) and 
                current > np.max(right_window)):
                swing_highs.append(i)
            
            # Check for swing low
            if (current < np.min(left_window) and 
                current < np.min(right_window)):
                swing_lows.append(i)
        
        return np.array(swing_highs), np.array(swing_lows)