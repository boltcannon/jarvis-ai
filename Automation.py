from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
import subprocess
import requests
import keyboard
import asyncio
import os
import webbrowser

# Load environment variables
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "User")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in .env file.")

# User agent for web scraping fallback
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Groq API wrapper
class Groq:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_completion(self, model, messages, max_tokens=1024, temperature=0.7, top_p=1.0, stream=False):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
        }

        # Debugging: Show request payload
        print("[DEBUG] Sending payload to Groq API:", data)

        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()


client = Groq(api_key=GroqAPIKey)

# System instruction for the assistant
SystemChatBot = [
    {
        "role": "system",
        "content": f"Hello, I am {Username}. You're a content writer. You have to write content like letters, articles, and responses professionally."
    }
]

# Content generation handler
def Content(topic):
    def OpenNotepad(file):
        subprocess.Popen(['notepad.exe', file])

    def ContentWriterAI(prompt):
        messages = [{"role": "user", "content": prompt}]
        completion = client.chat_completion(
            model="llama3-70b-8192",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
        )
        answer = completion["choices"][0]["message"]["content"]
        return answer

    topic = topic.replace("Content ", "").strip()
    content_by_ai = ContentWriterAI(topic)

    os.makedirs("Data", exist_ok=True)
    filepath = rf"Data\{topic.lower().replace(' ', '')}.txt"
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content_by_ai)

    OpenNotepad(filepath)
    return True

# Other task functions
def YouTubeSearch(topic):
    webbrowser.open(f"https://www.youtube.com/results?search_query={topic}")
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        def extract_links(html):
            soup = BeautifulSoup(html, 'html.parser') if html else None
            return [a.get('href') for a in soup.find_all('a', {'jsname': 'UWckNb'}) if a.get('href')] if soup else []

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            response = sess.get(url, headers={"User-Agent": useragent})
            return response.text if response.ok else None

        html = search_google(app)
        links = extract_links(html)
        if links:
            webopen(links[0])
        return True

def CloseApp(app):
    if "chrome" in app.lower():
        return True  # Prevent Chrome closure
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        return False

def System(command):
    actions = {
        "mute": lambda: keyboard.press_and_release("volume mute"),
        "unmute": lambda: keyboard.press_and_release("volume mute"),
        "volume up": lambda: keyboard.press_and_release("volume up"),
        "volume down": lambda: keyboard.press_and_release("volume down")
    }
    if command in actions:
        actions[command]()
        return True
    return False

def GoogleSearch(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return True

# Dispatcher for automation tasks
async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        cmd = command.lower().strip()
        if cmd.startswith("open ") and "open it" not in cmd and "open file" not in cmd:
            funcs.append(asyncio.to_thread(OpenApp, cmd.removeprefix("open ")))
        elif cmd.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, cmd.removeprefix("close ")))
        elif cmd.startswith("play "):
            funcs.append(asyncio.to_thread(PlayYoutube, cmd.removeprefix("play ")))
        elif cmd.startswith("content "):
            funcs.append(asyncio.to_thread(Content, cmd.removeprefix("content ")))
        elif cmd.startswith("google search "):
            funcs.append(asyncio.to_thread(GoogleSearch, cmd.removeprefix("google search ")))
        elif cmd.startswith("system "):
            funcs.append(asyncio.to_thread(System, cmd.removeprefix("system ")))
        else:
            print(f"[yellow]No Function Found for: {command}[/yellow]")

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    async for _ in TranslateAndExecute(commands):
        pass
    return True
