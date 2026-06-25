import cv2            # Library for image processing (OpenCV)
import numpy as np    # Library for mathematical operations (matrix calculations)
import time           # Library for tracking time
import asyncio        # Library for asynchronous operations (Telegram bot)
import requests       # Library for HTTP requests to trigger the buzzer on ESP32
from telegram import Bot # Library for Telegram Bot API

# --- SETTINGS ---
BOT_TOKEN = '' # Your bot's unique API token, DON'T FORGET TO CHANGE WITH YOURS‼️
CHAT_ID = '' # Your personal Telegram account ID to receive alerts, DON'T FORGET TO CHANGE WITH YOURS‼️
bot = Bot(token=BOT_TOKEN) # Initialize the bot object

URL = "http://192.168.x.xx:81/stream" # The IP address of your ESP32-CAM stream, DON'T FORGET TO CHANGE WITH YOURS‼️

async def main():
    cap = cv2.VideoCapture(URL) # Initialize the camera stream
    
    if not cap.isOpened(): # Exit if the camera cannot be connected
        print("ERROR: Could not connect to the camera!")
        return

    last_alarm_time = 0 # Timestamp to prevent continuous alarm triggering
    
    # Read the first frame and convert it to grayscale for initial motion analysis
    ret, frame = cap.read()
    if not ret: return
    prev_frame = cv2.resize(frame, (160, 120))
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    print("System active... Awaiting movement.")

    while True: # Main application loop
        ret, frame = cap.read() # Capture a new frame from the camera
        if not ret: 
            print("Connection lost, reconnecting...")
            cap = cv2.VideoCapture(URL) # Attempt to reconnect if stream drops
            await asyncio.sleep(1)
            continue
            
        # Resize frame to 160x120 to reduce processing load
        small_frame = cv2.resize(frame, (160, 120))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY) # Convert to grayscale
        # Motion detection: Calculate the difference between the current and previous frame
        diff = cv2.absdiff(gray, prev_gray)
        # Apply a threshold to highlight the changes (binary image)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        motion_amount = np.sum(thresh) # Calculate total number of changed pixels
        
        # Trigger alarm if motion exceeds the threshold and at least 1 second has passed
        if motion_amount > 50000 and (time.time() - last_alarm_time > 1):
            print("!!! Movement Detected! !!!")
            
            # Save the snapshot of the moment
            cv2.imwrite("hareket.jpg", frame)
            # Send the photo via Telegram
            with open("hareket.jpg", 'rb') as photo:
                await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="⚠️ ALARM: Movement detected!")
            
            # Send an HTTP request to the ESP32 server to trigger the buzzer
            try:
                requests.get("http://192.168.X.XX/alarm", timeout=5)   # DON'T FORGET TO CHANGE WITH YOURS‼️
            except:
                print("Buzzer could not be reached!")

            last_alarm_time = time.time() # Update the last alarm timestamp
            await asyncio.sleep(1) # Short delay to maintain system stability

        prev_gray = gray # Update the previous frame for the next iteration
        
        cv2.imshow("Security Cam - EO Embedded", frame) # Display the live stream
        if cv2.waitKey(1) == 27: break # Break loop if 'ESC' key is pressed

    cap.release() # Release camera resources
    cv2.destroyAllWindows() # Close all OpenCV windows

if __name__ == '__main__':
    asyncio.run(main()) # Run the main function asynchronously