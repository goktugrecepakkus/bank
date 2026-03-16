import asyncio
import websockets
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ws_hub_mock")

connected_banks = set()

async def handler(websocket):
    logger.info("New connection established")
    connected_banks.add(websocket)
    try:
        async for message in websocket:
            if isinstance(message, str) and message.startswith("<?xml"):
                logger.info("Received XML Message (PACS.008):")
                print(message)
                # For testing, we can simulate an incoming XML transfer after receiving this by sending it back
                # after a short delay (echo it back) or just acknowledging it
                logger.info("Sending back an ACK-like message or echoing...")
            elif isinstance(message, str):
                logger.info(f"Received JSON/Text Message: {message}")
            else:
                logger.info(f"Received unknown message format")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed: {e}")
    finally:
        connected_banks.remove(websocket)

async def main():
    logger.info("Starting mock Hub on ws://localhost:9999/ws/hub")
    async with websockets.serve(handler, "localhost", 9999):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
