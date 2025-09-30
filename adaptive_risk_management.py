import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class AdaptiveRiskManager:
    """
    Manages risk dynamically based on market conditions and account performance
    """
    
    def __init__(self, initial_balance=1000.0, risk_tolerance=0.5):
        """
        Initialize the adaptive risk manager
        
        Args:
            initial_balance: Starting account balance
            risk_tolerance: Base risk tolerance (0.1 to 1.0)
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_tolerance = max(0.1, min(1.0, risk_tolerance))
        
        # Performance tracking
        self.trades = []
        self.win_streak = 0
        self.loss_streak = 0
        self.daily_results = {}
        
        # Risk settings
        self.base_risk_percent = 0.02  # 2% risk per trade as baseline
        self.max_risk_percent = 0.05   # 5% maximum risk per trade
        self.min_risk_percent = 0.005  # 0.5% minimum risk per trade
        
    def update_balance(self, new_balance):
        """
        Update the current account balance
        
        Args:
            new_balance: New account balance
        """
        self.current_balance = max(0, new_balance)
        
    def record_trade(self, trade_result):
        """
        Record a trade result for risk calculation
        
        Args:
            trade_result: Dictionary with trade details
            {
                'timestamp': datetime,
                'profit_loss': float,
                'win': bool,
                'market': str,
                'stake': float
            }
        """
        self.trades.append(trade_result)
        
        # Update win/loss streaks
        if trade_result['win']:
            self.win_streak += 1
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.win_streak = 0
            
        # Update daily results
        trade_date = trade_result['timestamp'].strftime('%Y-%m-%d')
        
        if trade_date not in self.daily_results:
            self.daily_results[trade_date] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'profit_loss': 0.0
            }
            
        daily = self.daily_results[trade_date]
        daily['trades'] += 1
        daily['profit_loss'] += trade_result['profit_loss']
        
        if trade_result['win']:
            daily['wins'] += 1
        else:
            daily['losses'] += 1
            
    def get_optimal_stake(self, market_volatility=0.5, probability=0.5, market=None):
        """
        Calculate optimal stake based on current conditions
        
        Args:
            market_volatility: Market volatility rating (0.1 to 1.0)
            probability: Estimated win probability (0.1 to 1.0)
            market: Optional market identifier for market-specific adjustments
            
        Returns:
            Recommended stake amount
        """
        # Base risk percentage adjusted for risk tolerance
        risk_pct = self.base_risk_percent * self.risk_tolerance
        
        # Adjust for market volatility (reduce risk in high volatility)
        volatility_factor = 1.0 - (market_volatility * 0.5)
        risk_pct *= volatility_factor
        
        # Adjust for win probability (increase risk with higher probability)
        probability_factor = (probability - 0.5) * 2
        risk_adjustment = 1.0 + max(-0.5, min(1.0, probability_factor))
        risk_pct *= risk_adjustment
        
        # Adjust for win/loss streaks
        if self.win_streak > 2:
            # Increase risk during win streaks (but cap the increase)
            streak_factor = min(1.5, 1.0 + (self.win_streak * 0.1))
            risk_pct *= streak_factor
        elif self.loss_streak > 1:
            # Decrease risk during loss streaks
            streak_factor = max(0.5, 1.0 - (self.loss_streak * 0.2))
            risk_pct *= streak_factor
            
        # Enforce limits
        risk_pct = max(self.min_risk_percent, min(self.max_risk_percent, risk_pct))
        
        # Calculate stake based on balance and risk percentage
        stake = self.current_balance * risk_pct
        
        # Round to 2 decimal places
        stake = round(stake, 2)
        
        # Ensure minimum stake of $1
        return max(1.0, stake)
        
    def should_stop_trading(self):
        """
        Determine if trading should be stopped based on risk management rules
        
        Returns:
            Tuple of (should_stop, reason)
        """
        # Check for severe drawdown
        if self.current_balance < self.initial_balance * 0.75:
            return True, "Severe drawdown detected (>25% of initial balance)"
            
        # Check for excessive consecutive losses
        if self.loss_streak >= 5:
            return True, f"Excessive consecutive losses ({self.loss_streak})"
            
        # Check daily loss limit
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.daily_results:
            daily_loss = self.daily_results[today]['profit_loss']
            if daily_loss < -self.initial_balance * 0.1:
                return True, "Daily loss limit exceeded (>10% of initial balance)"
                
        return False, None
        
    def get_performance_metrics(self):
        """
        Calculate key performance metrics
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_loss': 0,
                'win_streak': 0,
                'loss_streak': 0,
                'average_win': 0,
                'average_loss': 0
            }
            
        total_trades = len(self.trades)
        wins = sum(1 for t in self.trades if t['win'])
        losses = total_trades - wins
        
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        profit_loss = sum(t['profit_loss'] for t in self.trades)
        
        # Calculate averages
        average_win = sum(t['profit_loss'] for t in self.trades if t['win']) / wins if wins > 0 else 0
        average_loss = sum(-t['profit_loss'] for t in self.trades if not t['win']) / losses if losses > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_loss': profit_loss,
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak,
            'average_win': average_win,
            'average_loss': average_loss
        }