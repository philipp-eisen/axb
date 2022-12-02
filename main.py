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
re_acronym = re.compile(r"\b[A-ZÅÄÖÜß0-9]{2,}\b")


gpt3_contex = """List of acronyms
MAKE SURE THAT THE LETTERS MATCH EXACTLY!
N Y O B | None of Your Business
O F C | Of Course
O M G | Oh My God
P A N S | Pretty Awesome New Stuff
P H A T | Pretty, Hot, And Tempting
P O S | Parents Over Shoulder
R O F L | Rolling On the Floor Laughing
S M H | Shaking My Head
T T Y L | Talk To You Later
Y O L O | You Only Live Once
A X B | Acronym eXplanation Bot
W T H | What The Heck
R O F L M A O S H I C A D | Rolling On Floor Laughing My Ass Off So Hard I Choke And Die
"""


def gpt_3_define_acronym(acronym):
    url = "https://api.openai.com/v1/engines/text-davinci-003/completions"
    prompt = gpt3_contex + " ".join(list(acronym)) + " |"
    payload = {"prompt": prompt, "max_tokens": 3 * len(acronym), "temperature": 0.0}
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
