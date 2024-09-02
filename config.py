import pyotp
import qrcode
import os
from datetime import timedelta

# TOTP configuration
key = "TopSecretKeyyyyy"
totp = pyotp.TOTP(key)

def verify_passcode(key, passcode):
    return totp.verify(passcode)

# Flask configuration settings
class Config:
    SECRET_KEY = 'your-secret-key'  # Replace with your actual secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'  # Database URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications for performance
    # Session management settings removed