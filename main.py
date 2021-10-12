import json
import os
import re
import requests
import http.server
import socketserver

from slack_sdk.rtm_v2 import RTMClient

slack_token = os.environ.get("SLACK_TOKEN")
gpt3_token = os.environ.get("GPT3_TOKEN")

rtm = RTMClient(token=slack_token)
re_acronym = re.compile(r"\b[A-ZÄÖÜß]{2,}\b")


gpt3_contex = """
NYOB: None of Your Business
OFC: Of Course
OMG: Oh My God
PANS: Pretty Awesome New Stuff
PHAT: Pretty, Hot, And Tempting
POS: Parents Over Shoulder
ROFL: Rolling On the Floor Laughing
SMH: Shaking My Head
TTYL: Talk To You Later
YOLO: You Only Live Once
AXB: Acronym eXplanation Bot
WTH: What The Heck
"""


def gpt_3_define_acronym(acronym):
    url = "https://api.openai.com/v1/engines/davinci/completions"
    prompt = gpt3_contex + acronym + ":"
    payload = {"prompt": prompt, "max_tokens": 3 * len(acronym), "temperature": 0.5}
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {gpt3_token}",
            "Content-Type": "application/json",
        },
    )
    return response.json()["choices"][0]["text"].split("\n")[0]


def serve_status_page():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><body>Hello, world!</body></html>", "utf-8"))

    httpd = socketserver.TCPServer(("", 8080), Handler)
    httpd.serve_forever()


def start_in_new_thread(fn):
    import threading

    return threading.Thread(target=fn).start()


@rtm.on("message")
def handle(client: RTMClient, event: dict):
    if event.get("type") == "message":
        if acronyms := re_acronym.findall(event.get("text")):
            for acr in acronyms:
                client.web_client.chat_postMessage(
                    channel=event["channel"],
                    text=f"*{acr}*: {gpt_3_define_acronym(acr)}",
                    thread_ts=event["ts"],
                )


if __name__ == "__main__":
    print("Serving status page")
    start_in_new_thread(serve_status_page)
    print("Listenting to slack")
    rtm.start()
