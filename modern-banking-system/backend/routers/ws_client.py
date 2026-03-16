import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed
import os

logger = logging.getLogger(__name__)

# Temporary test hub address
# To be changed when the actual target is known
HUB_URI = os.getenv("HUB_WS_URI", "ws://localhost:9999/ws/hub")
OUR_BANK_ID = os.getenv("BANK_ID", "MODERN_BANK")

class WSClientManager:
    def __init__(self):
        self.connection = None
        self.reconnect_delay = 5

    async def connect(self):
        """Establish connection to the central hub."""
        while True:
            try:
                logger.info(f"Connecting to Hub at {HUB_URI}...")
                async with websockets.connect(HUB_URI) as websocket:
                    self.connection = websocket
                    logger.info("Connected to WebSocket Hub successfully.")
                    
                    # Optional: Send a handshake/auth message here if required
                    await self._send_handshake()

                    # Start listening for messages
                    await self.listen()
                    
            except ConnectionClosed as e:
                logger.warning(f"Connection to Hub closed: {e}")
            except Exception as e:
                logger.error(f"WebSocket Error: {e}")
            
            self.connection = None
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)

    async def _send_handshake(self):
        """Send initial auth/identification message."""
        if not self.connection:
            return
        
        handshake_msg = {
            "type": "HANDSHAKE",
            "bank_id": OUR_BANK_ID
        }
        await self.connection.send(json.dumps(handshake_msg))

    async def listen(self):
        """Listen for incoming messages from the Hub."""
        if not self.connection:
            return
            
        async for message in self.connection:
            try:
                if isinstance(message, str) and message.strip().startswith("<?xml"):
                    logger.info("Received XML message")
                    await self.process_xml_message(message)
                else:
                    data = json.loads(message)
                    await self.process_message(data)
            except json.JSONDecodeError:
                logger.error(f"Received non-JSON/non-XML message: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def process_xml_message(self, xml_string: str):
        """Process incoming ISO 20022 PACS.008 messages."""
        try:
            from iso20022 import parse_pacs008_xml
            from database import SessionLocal
            import models
            
            data = parse_pacs008_xml(xml_string)
            logger.info(f"Incoming XML transfer received: {data}")
            
            db = SessionLocal()
            try:
                to_account = db.query(models.Account).filter(models.Account.iban == data["to_iban"]).first()
                if to_account and to_account.status == models.AccountStatusEnum.active:
                    to_account.balance += data["amount"]
                    new_ledger_entry = models.Ledger(
                        from_account_id=None,
                        to_account_id=to_account.id,
                        amount=data["amount"],
                        transaction_type=models.TransactionTypeEnum.deposit
                    )
                    db.add(new_ledger_entry)
                    db.commit()
                    logger.info(f"Successfully processed XML transfer for {data['amount']} {data['currency']}")
                else:
                    logger.warning(f"Target account not found or not active: {data['to_iban']}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to process XML message: {e}")

    async def process_message(self, data: dict):
        """Process business logic based on message type."""
        msg_type = data.get("type")
        
        if msg_type == "TRANSFER":
            logger.info(f"Incoming transfer received: {data}")
            # TODO: Call Database/Service layer to add money to user account
            # Example response
            # await self.send_message({"type": "TRANSFER_ACK", "tx_id": data.get("tx_id"), "status": "SUCCESS"})
        elif msg_type == "TRANSFER_ACK":
            logger.info(f"Transfer acknowledgment received: {data}")
            # TODO: Update local transaction state from PENDING to COMPLETED
        else:
            logger.debug(f"Unknown message type received: {data}")

    async def send_message(self, message: dict):
        """Send a dictionary as a JSON message to the Hub."""
        if not self.connection:
            logger.error("Cannot send message: WebSocket is not connected.")
            return False
            
        try:
            await self.connection.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
            
    async def send_xml_message(self, xml_string: str):
        """Send an XML string (like PACS.008) to the Hub."""
        if not self.connection:
            logger.error("Cannot send message: WebSocket is not connected.")
            return False
            
        try:
            await self.connection.send(xml_string)
            return True
        except Exception as e:
            logger.error(f"Failed to send XML message: {e}")
            return False

# Global instance for use in FastAPI app
ws_client = WSClientManager()
