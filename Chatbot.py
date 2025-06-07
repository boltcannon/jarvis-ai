from json import load, dump
import datetime
import os
import random
import json
from dotenv import dotenv_values
import requests


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
        response = requests.post(self.base_url, headers=headers, json=data, stream=stream)
        response.raise_for_status()
        return response.iter_lines(decode_unicode=True) if stream else response.json()


# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

# Initialize chat history
chatlog_path = os.path.join("Data", "ChatLog.json")
if not os.path.exists("Data"):
    os.makedirs("Data")

# Load or initialize chat history
try:
    with open(chatlog_path, "r") as f:
        chat_history = load(f)
    # Ensure chat_history is a list
    if not isinstance(chat_history, list):
        chat_history = []
except (FileNotFoundError, json.JSONDecodeError):
    chat_history = []
    with open(chatlog_path, "w") as f:
        dump(chat_history, f)

System = f"""You are {Assistantname}, an advanced AI assistant. Follow these rules:
1. Respond concisely unless asked to elaborate
2. Always reply in English
3. Never mention your training data
4. For greetings, respond like a human would ("I'm good", etc.)
5. For factual questions, provide up-to-date information
6. Maintain context from previous messages in the conversation
"""

def is_time_query(query):
    time_keywords = ["time", "date", "day", "month", "year", "hour", "minute", "second"]
    return any(word in query.lower() for word in time_keywords)

def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        f"Current time: {now.strftime('%H:%M:%S')}\n"
        f"Today's date: {now.strftime('%A, %B %d, %Y')}"
    )

def is_greeting(query):
    greetings = ["hello", "hi", "hey", "hii", "heyy", "greetings"]
    return query.lower().strip() in greetings

def get_greeting_response():
    responses = [
        "I'm good, thanks! How about you?",
        "I'm doing great! What's up?",
        "I'm fine, how can I help you today?",
        "Doing well! How about yourself?",
        "All good here! What can I do for you?"
    ]
    return random.choice(responses)

def save_chat_history():
    try:
        with open(chatlog_path, "w") as f:
            dump(chat_history, f, indent=4)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def ChatBot(query):
    global chat_history
    
    # Handle greetings separately
    if is_greeting(query):
        response = get_greeting_response()
        # Add to chat history
        chat_history.extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": response}
        ])
        save_chat_history()
        print(response)
        return response

    try:
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": System}
        ]
        
        # Add time info if needed
        if is_time_query(query):
            messages.append({"role": "system", "content": RealtimeInformation()})
        
        # Add previous conversation history (last 6 exchanges)
        messages.extend(chat_history[-12:])  # Keep last 6 exchanges (each has user+assistant messages)
        
        # Add current query
        messages.append({"role": "user", "content": query})

        # Get streaming response
        stream_response = client.chat_completion(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
        )

        answer = ""
        for line in stream_response:
            if line.strip():
                if line.startswith("data: "):
                    line = line[len("data: "):]
                if line == "[DONE]":
                    break

                try:
                    chunk = json.loads(line)
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            content_piece = delta["content"]
                            print(content_piece, end="", flush=True)
                            answer += content_piece
                except json.JSONDecodeError:
                    continue

        print()  # Newline after streaming

        # Update chat history
        chat_history.extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer}
        ])
        
        # Limit chat history to prevent excessive memory usage
        if len(chat_history) > 20:  # Keep last 10 exchanges
            chat_history = chat_history[-20:]
        
        save_chat_history()
        return answer.strip()

    except Exception as e:
        print(f"Error: {e}")
        # Reset chat history on error
        chat_history = []
        save_chat_history()
        return "An error occurred. Please try again."

if __name__ == "__main__":
    print(f"{Assistantname}: Hi there! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print(f"{Assistantname}: Goodbye!")
            break
        print(f"{Assistantname}: ", end="")
        ChatBot(user_input)