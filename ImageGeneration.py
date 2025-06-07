import asyncio
import base64
from random import randint
from PIL import Image
import requests
import os
from time import sleep
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
API_KEY = os.getenv("HuggingFaceAPIKey")

if not API_KEY:
    raise ValueError("HuggingFaceAPIKey not found in .env")

# Constants
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {API_KEY}"}
DATA_DIR = "Data"
IMAGE_DATA_FILE = os.path.join("Frontend", "Files", "ImageGeneration.data")

os.makedirs(DATA_DIR, exist_ok=True)

def open_images(prompt):
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(DATA_DIR, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")

async def query(payload):
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"API error: {response.status_code} - {response.text}")
            return None

        output = response.json()

        # Some models return base64-encoded images
        if isinstance(output, list) and "generated_image" in output[0]:
            image_base64 = output[0]["generated_image"]
            return base64.b64decode(image_base64)
        elif "error" in output:
            print("API returned an error:", output["error"])
        else:
            print("Unexpected response format:", output)
        return None

    except Exception as e:
        print(f"API request failed: {str(e)}")
        return None

async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, 4K quality, ultra-detailed, high-resolution, seed={randint(0, 1000000)}"
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join(DATA_DIR, f"{prompt.replace(' ', '_')}{i + 1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            print(f"Image saved to: {file_path}")
        else:
            print(f"Image {i+1} failed to generate.")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# Main loop
while True:
    try:
        with open(IMAGE_DATA_FILE, "r") as f:
            data = f.read().strip()

        if not data:
            sleep(1)
            continue

        Prompt, Status = data.split(",")

        if Status.strip().lower() == "true":
            print("Generating Images...")
            GenerateImages(prompt=Prompt.strip())

            # Reset the data file
            with open(IMAGE_DATA_FILE, "w") as f:
                f.write("False,False")

            break
        else:
            sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user.")
        break
    except Exception as e:
        print(f"Error: {e}")
        sleep(1)
