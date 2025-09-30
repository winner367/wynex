import random
import time
from collections import deque

# --- PHASE 1: Volatility Auto-Scanner ---
class VolatilityAutoScanner:
    def __init__(self, indices=None):
        self.indices = indices or [10, 25, 50, 75, 100, 150, 200]
        self.tick_history = {idx: deque(maxlen=100) for idx in self.indices}

    def update_ticks(self):
        # Mock: generate random ticks for each index
        for idx in self.indices:
            self.tick_history[idx].append(random.randint(0, 9))

    def predictability_index(self, idx):
        # Mock: higher variance = less predictable
        ticks = list(self.tick_history[idx])
        if len(ticks) < 10:
            return 0.5
        counts = [ticks.count(i) for i in range(10)]
        max_count = max(counts)
        pi = max_count / len(ticks)
        return pi

    def best_index(self):
        scores = {idx: self.predictability_index(idx) for idx in self.indices}
        best = max(scores, key=scores.get)
        return best, scores[best]

# --- PHASE 2: Multi-Strategy Signal Engine ---
class MultiStrategySignalEngine:
    def even_odd_signal(self, ticks):
        even = sum(1 for t in ticks if t % 2 == 0)
        odd = len(ticks) - even
        conf = abs(even - odd) / len(ticks)
        signal = 'Even' if even > odd else 'Odd'
        return signal, conf

    def matches_differs_signal(self, ticks):
        if len(ticks) < 2:
            return 'Differs', 0.0
        last = ticks[-1]
        prev = ticks[-2]
        signal = 'Matches' if last == prev else 'Differs'
        conf = 0.7 if signal == 'Differs' else 0.6
        return signal, conf

    def rise_fall_signal(self, ticks):
        if len(ticks) < 2:
            return 'Rise', 0.0
        rise = sum(1 for i in range(1, len(ticks)) if ticks[i] > ticks[i-1])
        fall = len(ticks) - 1 - rise
        conf = abs(rise - fall) / (len(ticks) - 1)
        signal = 'Rise' if rise > fall else 'Fall'
        return signal, conf

    def get_signals(self, ticks):
        eo, eo_conf = self.even_odd_signal(ticks)
        md, md_conf = self.matches_differs_signal(ticks)
        rf, rf_conf = self.rise_fall_signal(ticks)
        return {
            'Even/Odd': (eo, eo_conf),
            'Matches/Differs': (md, md_conf),
            'Rise/Fall': (rf, rf_conf)
        }

# --- PHASE 3: Smart Risk Engine ---
class SmartRiskEngine:
    def __init__(self):
        self.base_stake = 1.0
        self.max_loss = 10.0
        self.max_profit = 20.0
        self.consecutive_losses = 0
        self.max_consec_losses = 3
        self.cooldown = 0
        self.total_profit = 0.0

    def get_stake(self, conf, last_result):
        # Reverse Martingale: increase on win, reset on loss
        if last_result == 'win':
            return self.base_stake * 1.5
        else:
            return self.base_stake

    def should_stop(self):
        if self.total_profit <= -self.max_loss:
            return True, 'Max loss reached'
        if self.total_profit >= self.max_profit:
            return True, 'Max profit reached'
        if self.consecutive_losses >= self.max_consec_losses:
            return True, 'Max consecutive losses reached'
        if self.cooldown > 0:
            return True, f'Cooldown: {self.cooldown}s left'
        return False, ''

    def update(self, profit):
        self.total_profit += profit
        if profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        if self.consecutive_losses >= self.max_consec_losses:
            self.cooldown = 60  # 60s cooldown

    def tick_cooldown(self):
        if self.cooldown > 0:
            self.cooldown -= 1

# --- PHASE 4: Learning Memory System ---
class LearningMemorySystem:
    def __init__(self):
        self.memory = {}

    def log(self, index, strategy, result):
        key = (index, strategy)
        if key not in self.memory:
            self.memory[key] = {'wins': 0, 'losses': 0}
        if result == 'win':
            self.memory[key]['wins'] += 1
        else:
            self.memory[key]['losses'] += 1

    def best_strategy(self, index):
        # Return strategy with highest win rate for this index
        best = None
        best_rate = -1
        for (idx, strat), stats in self.memory.items():
            if idx == index:
                total = stats['wins'] + stats['losses']
                if total == 0:
                    continue
                rate = stats['wins'] / total
                if rate > best_rate:
                    best = strat
                    best_rate = rate
        return best or 'Even/Odd'

# --- PHASE 5: Trade Validator & Execution ---
def trade_validator(signal, conf, risk_ok):
    return conf > 0.2 and risk_ok

def execute_trade(signal, stake):
    # Mock: random win/loss
    result = random.choice(['win', 'loss'])
    profit = stake if result == 'win' else -stake
    return result, profit

# --- PHASE 6: Real-Time Statistics & Console UI ---
def print_stats(index, strategy, signal, conf, result, profit, risk_engine):
    print(f"[INDEX] Vol {index} | [STRATEGY] {strategy} | [SIGNAL] {signal} ({conf*100:.1f}%) | [RESULT] {result} | [P/L] {profit:+.2f} | [Total P/L] {risk_engine.total_profit:+.2f}")
    if risk_engine.cooldown > 0:
        print(f"[RISK] Cooldown active: {risk_engine.cooldown}s left")
    if risk_engine.consecutive_losses > 0:
        print(f"[RISK] Consecutive losses: {risk_engine.consecutive_losses}")

# --- MAIN LOOP (DEMO) ---
def main():
    scanner = VolatilityAutoScanner()
    signal_engine = MultiStrategySignalEngine()
    risk_engine = SmartRiskEngine()
    memory = LearningMemorySystem()
    last_result = None
    for step in range(30):
        scanner.update_ticks()
        best_index, pi = scanner.best_index()
        ticks = list(scanner.tick_history[best_index])
        signals = signal_engine.get_signals(ticks)
        # Use best strategy from memory, or default
        strategy = memory.best_strategy(best_index)
        signal, conf = signals[strategy]
        stake = risk_engine.get_stake(conf, last_result)
        stop, reason = risk_engine.should_stop()
        if stop:
            print(f"[STOP] {reason}")
            risk_engine.tick_cooldown()
            time.sleep(0.5)
            continue
        # Validate and execute trade
        if trade_validator(signal, conf, not stop):
            result, profit = execute_trade(signal, stake)
            risk_engine.update(profit)
            memory.log(best_index, strategy, result)
            last_result = result
            print_stats(best_index, strategy, signal, conf, result, profit, risk_engine)
        else:
            print(f"[SKIP] No valid trade (conf={conf:.2f})")
        time.sleep(0.5)

if __name__ == "__main__":
    main() 