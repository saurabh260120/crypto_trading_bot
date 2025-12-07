"""
Delta Exchange API client.
"""
import httpx
import websockets
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Callable
from app.core.security import sign_delta_request
import logging

logger = logging.getLogger(__name__)


class DeltaExchangeClient:
    """Delta Exchange REST and WebSocket client."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        ws_url: Optional[str] = None,
        sandbox: bool = True
    ):
        """
        Initialize Delta Exchange client.
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret
            base_url: REST API base URL
            ws_url: WebSocket URL (optional)
            sandbox: Whether to use sandbox environment
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.ws_url = ws_url or base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        self.sandbox = sandbox
        self.client = httpx.AsyncClient(timeout=30.0)
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
    
    def _get_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate authenticated headers for API request."""
        timestamp = str(int(time.time()))
        signature = sign_delta_request(self.api_secret, method, path, body, timestamp)
        
        return {
            "api-key": self.api_key,
            "signature": signature,
            "timestamp": timestamp,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make authenticated API request with retry logic."""
        path = endpoint
        body = json.dumps(data) if data else ""
        
        for attempt in range(retries):
            try:
                headers = self._get_headers(method, path, body)
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    response = await self.client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await self.client.post(url, headers=headers, json=data, params=params)
                elif method == "PUT":
                    response = await self.client.put(url, headers=headers, json=data, params=params)
                elif method == "DELETE":
                    response = await self.client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                if not result.get("success", False):
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"API error: {error_msg}")
                
                return result.get("result", {})
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        
        raise Exception("Request failed after retries")
    
    # Account endpoints
    async def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        return await self._request("GET", "/account")
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        return await self._request("GET", "/account/balances")
    
    # Market data endpoints
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for a symbol."""
        return await self._request("GET", f"/tickers/{symbol}")
    
    async def get_tickers(self) -> List[Dict[str, Any]]:
        """Get all tickers."""
        result = await self._request("GET", "/tickers")
        return result if isinstance(result, list) else result.get("tickers", [])
    
    async def get_products(self) -> List[Dict[str, Any]]:
        """Get all products."""
        result = await self._request("GET", "/products")
        return result if isinstance(result, list) else result.get("products", [])
    
    # Order endpoints
    async def place_order(
        self,
        product_id: int,
        side: str,
        order_type: str,
        size: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        reduce_only: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Place an order."""
        order_data = {
            "product_id": product_id,
            "side": side,
            "order_type": order_type,
            "size": str(size),
            "reduce_only": reduce_only,
            **kwargs
        }
        
        if price is not None:
            order_data["limit_price"] = str(price)
        if stop_price is not None:
            order_data["stop_price"] = str(stop_price)
        
        return await self._request("POST", "/orders", data=order_data)
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        return await self._request("DELETE", f"/orders/{order_id}")
    
    async def get_orders(
        self,
        product_id: Optional[int] = None,
        states: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get orders."""
        params = {}
        if product_id:
            params["product_id"] = product_id
        if states:
            params["states"] = ",".join(states)
        
        result = await self._request("GET", "/orders", params=params)
        return result if isinstance(result, list) else result.get("orders", [])
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific order."""
        return await self._request("GET", f"/orders/{order_id}")
    
    # Position endpoints
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions."""
        result = await self._request("GET", "/positions")
        return result if isinstance(result, list) else result.get("positions", [])
    
    async def get_position(self, product_id: int) -> Dict[str, Any]:
        """Get position for a specific product."""
        return await self._request("GET", f"/positions/{product_id}")
    
    # WebSocket methods
    async def connect_websocket(self):
        """Connect to WebSocket."""
        if self.ws_connection:
            return
        
        try:
            self.ws_connection = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info("WebSocket connected")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def subscribe_to_channel(self, channel: str, symbol: Optional[str] = None):
        """Subscribe to a WebSocket channel."""
        if not self.ws_connection:
            await self.connect_websocket()
        
        subscribe_msg = {
            "type": "subscribe",
            "channel": channel
        }
        
        if symbol:
            subscribe_msg["symbol"] = symbol
        
        await self.ws_connection.send(json.dumps(subscribe_msg))
    
    async def listen_for_updates(self, callback: Callable[[Dict], None]):
        """Listen for WebSocket updates."""
        if not self.ws_connection:
            await self.connect_websocket()
        
        while True:
            try:
                message = await self.ws_connection.recv()
                data = json.loads(message)
                callback(data)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                await self.connect_websocket()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(1)
    
    async def close(self):
        """Close connections."""
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
        await self.client.aclose()

