import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

def generate_robot_svg() -> str:
    """
    Generate an SVG of a robot for the dashboard logo
    
    Returns:
        String containing SVG markup
    """
    return """
    <div style='text-align: center;'>
    <svg width="80" height="80" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="120" height="120" fill="none"/>
        <path d="M60 20C37.91 20 20 37.91 20 60C20 82.09 37.91 100 60 100C82.09 100 100 82.09 100 60C100 37.91 82.09 20 60 20ZM60 90C43.43 90 30 76.57 30 60C30 43.43 43.43 30 60 30C76.57 30 90 43.43 90 60C90 76.57 76.57 90 60 90Z" fill="#39C6F0"/>
        <circle cx="45" cy="50" r="8" fill="#39C6F0"/>
        <circle cx="75" cy="50" r="8" fill="#39C6F0"/>
        <rect x="40" y="70" width="40" height="5" rx="2.5" fill="#39C6F0"/>
    </svg>
    </div>
    """

def apply_conditional_formatting(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply conditional formatting to a dataframe
    
    Args:
        df: DataFrame to format
        
    Returns:
        Formatted DataFrame
    """
    # Apply formatting based on Result column if it exists
    if 'Result' in df.columns:
        return df.style.apply(
            lambda x: ['background-color: #90EE90' if v == 'Win' else 
                      'background-color: #FFB6C1' if v == 'Loss' else 
                      'background-color: #F0F0F0' 
                      for v in x], 
            subset=['Result']
        )
    
    # If no Result column, return unformatted dataframe
    return df

def format_currency(value: float, currency: str = "$") -> str:
    """
    Format a value as currency
    
    Args:
        value: Numeric value to format
        currency: Currency symbol
        
    Returns:
        Formatted string
    """
    return f"{currency}{value:.2f}"

def format_percentage(value: float) -> str:
    """
    Format a value as percentage
    
    Args:
        value: Numeric value to format (0-1)
        
    Returns:
        Formatted string
    """
    return f"{value*100:.1f}%"

def calculate_win_rate(trade_history: List[Dict[str, Any]]) -> float:
    """
    Calculate win rate from trade history
    
    Args:
        trade_history: List of trade dictionaries
        
    Returns:
        Win rate as a fraction (0-1)
    """
    if not trade_history:
        return 0.0
    
    wins = sum(1 for trade in trade_history if trade.get('result') == 'win')
    return wins / len(trade_history)

def calculate_profit_factor(trade_history: List[Dict[str, Any]]) -> float:
    """
    Calculate profit factor from trade history
    (Gross profit / Gross loss)
    
    Args:
        trade_history: List of trade dictionaries
        
    Returns:
        Profit factor (returns 1.0 if no losses or no trades)
    """
    if not trade_history:
        return 1.0
    
    gross_profit = sum(trade.get('profit_loss', 0) for trade in trade_history 
                     if trade.get('profit_loss', 0) > 0)
    gross_loss = abs(sum(trade.get('profit_loss', 0) for trade in trade_history 
                      if trade.get('profit_loss', 0) < 0))
    
    if gross_loss == 0:
        return 1.0 if gross_profit == 0 else float('inf')
    
    return gross_profit / gross_loss

def calculate_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """
    Calculate maximum drawdown from equity curve
    
    Args:
        equity_curve: List of equity values
        
    Returns:
        Dictionary with max_drawdown and max_drawdown_pct
    """
    if not equity_curve or len(equity_curve) < 2:
        return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}
    
    # Convert to numpy array for easier calculations
    equity = np.array(equity_curve)
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(equity)
    
    # Calculate drawdown in currency units
    drawdown = running_max - equity
    
    # Find max drawdown
    max_drawdown = np.max(drawdown)
    
    # Calculate percentage drawdown
    drawdown_pct = drawdown / running_max
    max_drawdown_pct = np.max(drawdown_pct)
    
    return {
        "max_drawdown": float(max_drawdown),
        "max_drawdown_pct": float(max_drawdown_pct)
    }

def calculate_performance_metrics(trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics from trade history
    
    Args:
        trade_history: List of trade dictionaries
        
    Returns:
        Dictionary with various performance metrics
    """
    if not trade_history:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 1.0,
            "net_profit": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "consecutive_wins": 0,
            "consecutive_losses": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0
        }
    
    # Total trades
    total_trades = len(trade_history)
    
    # Win/loss counts
    wins = [t for t in trade_history if t.get('result') == 'win']
    losses = [t for t in trade_history if t.get('result') == 'loss']
    
    win_count = len(wins)
    loss_count = len(losses)
    
    # Win rate
    win_rate = win_count / total_trades if total_trades > 0 else 0.0
    
    # Profit metrics
    net_profit = sum(t.get('profit_loss', 0) for t in trade_history)
    
    # Average win/loss
    avg_win = sum(t.get('profit_loss', 0) for t in wins) / win_count if win_count > 0 else 0.0
    avg_loss = sum(t.get('profit_loss', 0) for t in losses) / loss_count if loss_count > 0 else 0.0
    
    # Largest win/loss
    largest_win = max([t.get('profit_loss', 0) for t in wins]) if wins else 0.0
    largest_loss = min([t.get('profit_loss', 0) for t in losses]) if losses else 0.0
    
    # Consecutive wins/losses
    consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    
    current_consecutive_wins = 0
    current_consecutive_losses = 0
    
    for trade in trade_history:
        if trade.get('result') == 'win':
            current_consecutive_wins += 1
            current_consecutive_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
        else:
            current_consecutive_losses += 1
            current_consecutive_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
    
    # Profit factor
    profit_factor = calculate_profit_factor(trade_history)
    
    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "net_profit": net_profit,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "consecutive_wins": current_consecutive_wins,
        "consecutive_losses": current_consecutive_losses,
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses
    }