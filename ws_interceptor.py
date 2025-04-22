# Run with command: mitmdump -s ws_interceptor.py
from mitmproxy import ctx
import json 
import requests
import threading
import asyncio
import httpx

SERVER_URL = "http://localhost:5000/news"  # Flask server URL

def post_news(news_data):
    """
    Post a single news item (dictionary) to the Flask /news endpoint.
    """
    try:
        asyncio.run(post_news_async(news_data))
    except Exception as e:
        try:
            ctx.log.info(f"Error posting news (NewsID {news_data.get('NewsID')}): {e}")
        except:
            pass


async def post_news_async(news_data):
    """
    Asynchronous function to post a single news item to the Flask /news endpoint.
    """
    try:
        if not news_data:
            return
        news_data = news_data[0]
        headers = {'Content-Type': 'application/json'}
        async with httpx.AsyncClient() as client:
            response = await client.post(SERVER_URL, json=news_data, headers=headers)
            ctx.log.info(f"Posted NewsID {news_data.get('NewsID')}: {response.status_code} - {response.text}")
    except Exception as e:
        try:
            ctx.log.info(f"Error posting news (NewsID {news_data.get('NewsID')}): {e}")
        except:
            pass


def websocket_message(flow):
    """
    This function is triggered when a WebSocket message is sent or received.
    """
    if hasattr(flow, "websocket") and hasattr(flow.websocket, "messages"):
        message = flow.websocket.messages[-1]  # Get the last WebSocket message
        # ctx.log.info(f"WebSocket message: {message.content}")
    else:
        ctx.log.info("Flow does not have WebSocket messages attribute")

    try:
        pass
        # print(flow.content)
    except:
        print("FLOW", flow)

    if hasattr(flow, "websocket") and hasattr(flow.websocket, "messages"):
        message = flow.websocket.messages[-1]  # Get the last WebSocket message
        if message:
            direction = "→" if message.from_client else "←"
            try:
                # ctx.log.info(f"JSON:::: WebSocket {direction} {json.loads(message.content)}")
                data = json.loads(message.content)
                if data.get("M"):
                    for item in data["M"]:
                        if item.get("H") == "NewsHub":
                            # print(item.get("A"))
                            try:
                                for news in item.get("A"):
                                    # Each news string is expected to be a JSON-formatted string.
                                    try:
                                        news_item = json.loads(news)
                                        # Log the news title (if available)
                                        ctx.log.info(f"NEWS: {direction}:{news_item}")
                                        # Post this news item to the Flask endpoint using threading.
                                        threading.Thread(target=post_news, args=(news_item,)).start()
                                    except Exception as e:
                                        ctx.log.info(f"Error processing news item: {e}")
                                        with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                                            file.write(str(e) + "\n")
                            except Exception as e:
                                ctx.log.info(f"Error iterating news items: {e}")
                                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                                    file.write(str(e) + "\n")
            except Exception as e:
                ctx.log.info(f"Error processing WebSocket message: {e}")
                with open("ErrorLog.txt", "a", encoding="utf-8") as file:
                    file.write(str(e) + "\n")



