import asyncio
import websockets

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/notifications/"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket...")

                while True:
                    try:
                        message = await websocket.recv()
                        print(f"Received: {message}")
                    except websockets.exceptions.ConnectionClosed:
                        print("Server closed connection. Reconnecting in 5 seconds...")
                        break  # Reconnect

        except Exception as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")

        await asyncio.sleep(5)  # Retry after 5 seconds

if __name__ == "__main__":
    asyncio.run(test_websocket())
