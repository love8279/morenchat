#ACM
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = int(environ.get("API_ID", "24037760"))
API_HASH = environ.get("API_HASH", "dccc3070f1c12ab155011f14c3d6ae6a")
BOT_TOKEN = environ.get("BOT_TOKEN", "")

OWNER = int(environ.get("OWNER", "8499065407"))
CREDIT = environ.get("CREDIT", "༄ᶦᶰᵈ᭄『ƬG』ᎪຮᏂυ࿐")

TOTAL_USER = os.environ.get('TOTAL_USERS', '8499065407').split(',')
TOTAL_USERS = [int(user_id) for user_id in TOTAL_USER]

AUTH_USER = os.environ.get('AUTH_USERS', '8499065407').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set









