"""
Rate Limiting middleware for Rykard Banking API.
Uses slowapi (based on Flask-Limiter) for FastAPI.
IP-based rate limiting protects against brute force attacks.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# IP adresi bazlı rate limiter
limiter = Limiter(key_func=get_remote_address)

# Limit sabitleri (dakika başına)
LOGIN_LIMIT = "5/minute"         # Brute force koruması
REGISTER_LIMIT = "3/minute"      # Spam hesap koruması
TRANSFER_LIMIT = "10/minute"     # Transfer abuse koruması
TRADE_LIMIT = "10/minute"        # Trading abuse koruması
GENERAL_LIMIT = "60/minute"      # Genel API limiti
