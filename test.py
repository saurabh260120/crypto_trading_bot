import requests
import json
import time
from datetime import datetime, time as dt_time
import pytz

# Delta Exchange API credentials (replace with your own)
API_KEY = "GZJhp5pJsYzed2CDsm2xIA3sSVNNI5"
API_SECRET = "6a0h2wSBrYGwuC5RqAGmnL1gbFqGF6xxNDliKUYGKSudB64n6c9O2gP7fVHj"
BASE_URL = "https://api.india.delta.exchange/v2"

# Global variables
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "api-key": API_KEY,
    "signature": API_SECRET,  # Simplified; in practice, sign requests as per Delta's docs
    "timestamp": str(int(time.time()))
}
ist = pytz.timezone("Asia/Kolkata")
max_trades = 2
lot_size = 1000  # 1000 lots of BTCUSD
stop_loss_points = 200
trail_points = 50

# Function to get current BTCUSD spot price
def get_spot_price():
    url = f"{BASE_URL}/tickers/BTCUSD"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data["success"]:
        return float(data["result"][0]["spot_price"])
    raise Exception("Failed to fetch spot price")

# Function to find ATM strike
def get_atm_strike(spot_price):
    # For simplicity, rounding to nearest 1000; adjust logic based on Delta's strike intervals
    atm_strike = round(spot_price / 1000) * 1000
    return atm_strike

# Function to place sell order for an option
def place_sell_order(strike, option_type, expiry):
    product_id = 27  # BTCUSD product ID; adjust as needed
    payload = {
        "product_id": product_id,
        "size": lot_size,
        "side": "sell",
        "order_type": "market_order",
        "strike_price": str(strike),
        "option_type": option_type,  # "call" or "put"
        "expiry": expiry  # Format: "ddMMYY", e.g., "100425" for April 10, 2025
    }
    url = f"{BASE_URL}/orders"
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()
    if data["success"]:
        return float(data["result"]["limit_price"])  # Assuming premium is returned
    raise Exception(f"Failed to place {option_type} sell order")

# Function to get combined premium of open positions
def get_combined_premium():
    url = f"{BASE_URL}/positions"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data["success"]:
        total_premium = sum(float(pos["mark_price"]) * lot_size for pos in data["result"])
        return total_premium
    raise Exception("Failed to fetch positions")

# Function to monitor and manage trades
def manage_trade(initial_premium, trade_count):
    stop_loss = initial_premium + stop_loss_points
    trailing_stop = stop_loss
    last_premium = initial_premium

    while trade_count < max_trades:
        current_premium = get_combined_premium()
        profit = initial_premium - current_premium  # Negative premium means profit for short

        # Trailing stop logic
        if profit > 0:
            points_profit = int(profit / trail_points) * trail_points
            if points_profit >= trail_points:
                trailing_stop = initial_premium - points_profit
                print(f"Trailing stop updated to {trailing_stop}")

        # Check stop loss
        if current_premium >= trailing_stop:
            print(f"Stop loss hit at {current_premium}. Closing trade.")
            close_positions()
            return current_premium, trade_count + 1

        last_premium = current_premium
        time.sleep(60)  # Check every minute

    return None, trade_count

# Function to close all positions
def close_positions():
    url = f"{BASE_URL}/positions"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data["success"]:
        for pos in data["result"]:
            payload = {
                "product_id": pos["product_id"],
                "size": pos["size"],
                "side": "buy" if pos["side"] == "sell" else "sell",
                "order_type": "market_order"
            }
            requests.post(f"{BASE_URL}/orders", headers=headers, data=json.dumps(payload))
    print("Positions closed.")

# Main trading logic
def main():
    trade_count = 0
    previous_premium = None

    while trade_count < max_trades:
        now = datetime.now(ist)
        target_time = ist.localize(datetime.combine(now.date(), dt_time(17, 35)))  # 5:35 PM IST

        # Wait until 5:35 PM IST
        if now < target_time:
            sleep_seconds = (target_time - now).total_seconds()
            print(f"Waiting until 5:35 PM IST. Sleeping for {sleep_seconds} seconds.")
            time.sleep(sleep_seconds)

        # Get spot price and ATM strike
        spot_price = get_spot_price()
        atm_strike = get_atm_strike(spot_price)
        expiry = now.strftime("%d%m%y")  # Use today's expiry; adjust as needed

        # Sell ATM call and put
        call_premium = place_sell_order(atm_strike, "call", expiry)
        put_premium = place_sell_order(atm_strike, "put", expiry)
        initial_premium = (call_premium + put_premium) * lot_size
        print(f"Sold ATM call and put. Combined premium: {initial_premium}")

        # Manage the trade
        last_premium, trade_count = manage_trade(initial_premium, trade_count)

        # Re-entry logic
        if trade_count < max_trades and last_premium:
            print(f"Monitoring for re-entry at {last_premium}")
            while True:
                current_premium = get_combined_premium()
                if abs(current_premium - last_premium) < 10:  # Small threshold for re-entry
                    print(f"Re-entering trade at {current_premium}")
                    break
                time.sleep(60)

if _name_ == "_main_":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")