import os
from dotenv import load_dotenv, dotenv_values

def dev_id():
	return os.getenv("DEV_ID")

def is_dev(chat_id):
	if chat_id == "":
		return False
	if chat_id == dev_id():
		return True
	else:
		return False

