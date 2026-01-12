from instagrapi import Client

username = "INSTAGRAM_USERNAME_HERE"
password = "INSTAGRAM_PASSWORD_HERE"

cl = Client()
try:
    print("Trying to log in...")
    cl.login(username, password)
    print("Login successful!")
    
    filename = f"session_{username}.json"
    cl.dump_settings(filename)
    print(f"File generated: {filename}")
    print("Now send this file to the bot's folder on the server.")
except Exception as e:
    print(f"Erro: {e}")