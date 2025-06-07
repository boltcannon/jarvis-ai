from googlesearch import search
from json import load, dump
import datetime
from dotenv import dotenv_values
import requests
import os
import json

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

# Initialize chat history
chatlog_path = os.path.join("Data", "ChatLog.json")
if not os.path.exists("Data"):
    os.makedirs("Data")

try:
    with open(chatlog_path, "r") as f:
        chat_history = load(f)
    if not isinstance(chat_history, list):
        chat_history = []
except (FileNotFoundError, json.JSONDecodeError):
    chat_history = []
    with open(chatlog_path, "w") as f:
        dump(chat_history, f)

client = Groq(api_key=GroqAPIKey)

System = f"""You are {Assistantname}, an advanced AI assistant with access to real-time information.
Rules:
1. Provide professional, grammatically correct responses
2. Use proper punctuation and formatting
3. For factual questions, provide accurate, up-to-date information
4. Maintain context from previous messages
5. When using search results, summarize them clearly
"""

def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        search_data = f"Search results for '{query}':\n"
        for idx, result in enumerate(results, 1):
            search_data += f"\n{idx}. {result.title}\n   {result.description}\n   URL: {result.url}\n"
        return search_data
    except Exception as e:
        return f"Search error: {str(e)}"

def get_current_information():
    now = datetime.datetime.now()
    return (
        f"Current Date and Time:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
    )

def save_chat_history():
    try:
        with open(chatlog_path, "w") as f:
            dump(chat_history, f, indent=4)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def format_response(response):
    return response.strip().replace("</s>", "")

def RealtimeSearchEngine(prompt):
    global chat_history
    
    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": System},
        {"role": "system", "content": get_current_information()}
    ]
    
    # Add search results if the query seems to require web search
    if should_search(prompt):
        search_results = GoogleSearch(prompt)
        messages.append({"role": "system", "content": search_results})
    
    # Add conversation history (last 5 exchanges)
    messages.extend(chat_history[-10:])  # Keep last 5 exchanges (user + assistant pairs)
    
    # Add current prompt
    messages.append({"role": "user", "content": prompt})

    try:
        # Get streaming response
        stream_response = client.chat_completion(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=2048,
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
        formatted_answer = format_response(answer)
        chat_history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": formatted_answer}
        ])
        
        # Limit chat history to prevent excessive memory usage
        if len(chat_history) > 20:  # Keep last 10 exchanges
            chat_history = chat_history[-20:]
        
        save_chat_history()
        return formatted_answer

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while processing your request."

def should_search(query):
    # Determine if a query should trigger a web search
    search_keywords = [
        "current", "latest", "recent", "update", "news",
        "who is", "what is", "when did", "where is"
    ]
    return any(keyword in query.lower() for keyword in search_keywords)

if __name__ == "__main__":
    print(f"{Assistantname}: Hello! How can I assist you today?")
    while True:
        try:
            prompt = input("You: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ['exit', 'quit', 'bye']:
                print(f"{Assistantname}: Goodbye!")
                break
                
            print(f"{Assistantname}: ", end="")
            response = RealtimeSearchEngine(prompt)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")