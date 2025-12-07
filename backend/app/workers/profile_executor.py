"""
Profile executor - runs trading algorithm for a single profile.
"""
import asyncio
import logging
import traceback
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import decrypt_api_key
from app.models.profile import Profile
from app.models.algorithm import AlgorithmVersion
from app.models.order import OrderRecord, OrderStatus, OrderSide, OrderType
from app.models.metric import Metric, LogEntry, LogLevel
from app.exchange.delta_client import DeltaExchangeClient
import json

logger = logging.getLogger(__name__)


class ProfileExecutor:
    """Executes trading algorithm for a profile."""
    
    def __init__(self, profile_id: int, db: Session):
        self.profile_id = profile_id
        self.db = db
        self.running = False
        self.profile: Optional[Profile] = None
        self.algorithm_code: Optional[str] = None
        self.exchange_client: Optional[DeltaExchangeClient] = None
        self.algorithm_context: Dict[str, Any] = {}
    
    async def run(self):
        """Run the executor."""
        self.running = True
        
        try:
            # Load profile and algorithm
            await self._load_profile()
            
            if not self.profile or not self.algorithm_code:
                logger.error(f"Profile {self.profile_id} not found or no algorithm")
                return
            
            # Initialize exchange client
            await self._init_exchange_client()
            
            if not self.exchange_client:
                logger.error(f"Failed to initialize exchange client for profile {self.profile_id}")
                return
            
            # Execute algorithm
            await self._execute_algorithm()
        
        except Exception as e:
            logger.error(f"Error in profile executor {self.profile_id}: {e}", exc_info=True)
            await self._log_error(f"Executor error: {str(e)}")
        finally:
            await self._cleanup()
    
    async def _load_profile(self):
        """Load profile and algorithm from database."""
        db = SessionLocal()
        try:
            self.profile = db.query(Profile).filter(Profile.id == self.profile_id).first()
            
            if not self.profile:
                return
            
            if self.profile.algorithm_version_id:
                algorithm = db.query(AlgorithmVersion).filter(
                    AlgorithmVersion.id == self.profile.algorithm_version_id
                ).first()
                if algorithm:
                    self.algorithm_code = algorithm.code
        finally:
            db.close()
    
    async def _init_exchange_client(self):
        """Initialize Delta Exchange client."""
        if not self.profile:
            return
        
        try:
            api_key = decrypt_api_key(self.profile.encrypted_api_key)
            api_secret = decrypt_api_key(self.profile.encrypted_api_secret)
            
            base_url = settings.DELTA_SANDBOX_URL if self.profile.environment == "sandbox" else settings.DELTA_LIVE_URL
            ws_url = settings.DELTA_WS_SANDBOX_URL if self.profile.environment == "sandbox" else settings.DELTA_WS_LIVE_URL
            
            self.exchange_client = DeltaExchangeClient(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url,
                ws_url=ws_url,
                sandbox=(self.profile.environment == "sandbox")
            )
        except Exception as e:
            logger.error(f"Failed to initialize exchange client: {e}")
            raise
    
    async def _execute_algorithm(self):
        """Execute the trading algorithm."""
        if not self.algorithm_code or not self.exchange_client:
            return
        
        # Create algorithm execution context
        context = {
            "profile_id": self.profile_id,
            "profile": self.profile,
            "exchange": self.exchange_client,
            "db": SessionLocal(),
            "log": self._log,
            "place_order": self._place_order,
            "get_positions": self._get_positions,
            "get_balance": self._get_balance,
            "get_ticker": self._get_ticker,
            "parameters": self.profile.parameters or {},
            "state": self.profile.state or {},
            "running": lambda: self.running,
        }
        
        self.algorithm_context = context
        
        # Execute algorithm in isolated namespace
        try:
            # Compile and execute algorithm code
            code = compile(self.algorithm_code, f"profile_{self.profile_id}_algorithm", "exec")
            exec(code, {"__builtins__": __builtins__, **context})
        except Exception as e:
            logger.error(f"Algorithm execution error: {e}", exc_info=True)
            await self._log_error(f"Algorithm error: {str(e)}\n{traceback.format_exc()}")
            raise
    
    async def _place_order(
        self,
        product_id: int,
        side: str,
        order_type: str,
        size: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """Place an order and record it in database."""
        if not self.exchange_client:
            raise Exception("Exchange client not initialized")
        
        # Check global kill switch
        if settings.GLOBAL_KILL_SWITCH:
            raise Exception("Global kill switch is active")
        
        # Place order on exchange
        order_result = await self.exchange_client.place_order(
            product_id=product_id,
            side=side,
            order_type=order_type,
            size=size,
            price=price,
            stop_price=stop_price,
            reduce_only=reduce_only
        )
        
        # Record order in database
        db = SessionLocal()
        try:
            order_record = OrderRecord(
                profile_id=self.profile_id,
                exchange_order_id=str(order_result.get("id", "")),
                product_id=product_id,
                product_symbol=order_result.get("product_symbol"),
                side=OrderSide(side.lower()),
                order_type=OrderType(order_type.lower()),
                size=size,
                price=price,
                stop_price=stop_price,
                status=OrderStatus.PENDING,
                reduce_only=reduce_only
            )
            db.add(order_record)
            db.commit()
            db.refresh(order_record)
            
            await self._log_info(f"Order placed: {side} {size} @ {price or 'market'}")
            
            return {
                "id": order_record.id,
                "exchange_order_id": order_result.get("id"),
                "status": order_record.status.value
            }
        finally:
            db.close()
    
    async def _get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        if not self.exchange_client:
            return []
        return await self.exchange_client.get_positions()
    
    async def _get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.exchange_client:
            return {}
        return await self.exchange_client.get_balance()
    
    async def _get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for a symbol."""
        if not self.exchange_client:
            return {}
        return await self.exchange_client.get_ticker(symbol)
    
    async def _log(self, level: str, message: str, **kwargs):
        """Log a message."""
        db = SessionLocal()
        try:
            log_entry = LogEntry(
                profile_id=self.profile_id,
                level=LogLevel(level.upper()),
                message=message,
                context=json.dumps(kwargs) if kwargs else None
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
        finally:
            db.close()
    
    async def _log_info(self, message: str, **kwargs):
        """Log info message."""
        await self._log("INFO", message, **kwargs)
    
    async def _log_error(self, message: str, **kwargs):
        """Log error message."""
        await self._log("ERROR", message, **kwargs)
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.exchange_client:
            await self.exchange_client.close()
        
        if self.algorithm_context.get("db"):
            self.algorithm_context["db"].close()
    
    async def stop(self):
        """Stop the executor."""
        self.running = False
        await self._cleanup()

