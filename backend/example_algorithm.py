"""
Example trading algorithm template.

This is a basic template that can be used as a starting point for your trading algorithm.
Copy and modify this code in the algorithm editor.
"""

import asyncio
import time
from datetime import datetime

# Algorithm context provides:
# - profile: Profile object
# - exchange: DeltaExchangeClient instance
# - db: Database session
# - log(level, message, **kwargs): Logging function
# - place_order(...): Order placement function
# - get_positions(): Get current positions
# - get_balance(): Get account balance
# - get_ticker(symbol): Get ticker data
# - parameters: Dictionary of runtime parameters
# - state: Dictionary for persistent state
# - running(): Function that returns True if algorithm should continue

async def main():
    """Main algorithm loop."""
    log("INFO", "Algorithm started", profile_id=profile.id)
    
    # Example: Get account balance
    balance = await get_balance()
    log("INFO", f"Account balance: {balance}")
    
    # Example: Get ticker for BTCUSD
    try:
        ticker = await get_ticker("BTCUSD")
        log("INFO", f"BTCUSD price: {ticker.get('spot_price', 'N/A')}")
    except Exception as e:
        log("ERROR", f"Failed to get ticker: {e}")
    
    # Example: Simple trading logic
    # This is just a template - implement your own strategy
    
    while running():
        try:
            # Get current positions
            positions = await get_positions()
            log("INFO", f"Open positions: {len(positions)}")
            
            # Example: Place a limit order (commented out for safety)
            # order = await place_order(
            #     product_id=27,  # Replace with actual product ID
            #     side="buy",
            #     order_type="limit",
            #     size=0.1,
            #     price=50000.0,
            #     reduce_only=False
            # )
            # log("INFO", f"Order placed: {order}")
            
            # Wait before next iteration
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            log("ERROR", f"Algorithm error: {e}", exc_info=True)
            await asyncio.sleep(10)  # Wait before retrying
    
    log("INFO", "Algorithm stopped")

# Run the algorithm
if __name__ == "__main__":
    asyncio.run(main())

