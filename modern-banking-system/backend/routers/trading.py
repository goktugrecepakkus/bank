from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import yfinance as yf
from datetime import datetime
from decimal import Decimal
from security import get_current_user
import math
import time
import requests
from rate_limiter import limiter, TRADE_LIMIT

router = APIRouter(prefix="/trading", tags=["Trading"])

# Mapping of our internal string codes to Yahoo Finance tickers
TICKER_MAP = {
    "USD": "USDTRY=X",   # USD to TRY
    "EUR": "EURTRY=X",   # EUR to TRY
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "XAU": "GC=F",       # Gold Futures (USD)
    "XAG": "SI=F",       # Silver Futures (USD)
}

# In-memory cache to avoid repeated API calls
_price_cache = {}
_CACHE_TTL = 120  # 2 dakika cache

def _get_from_cache(key: str):
    """Cache'den fiyat çek, TTL dolmuşsa None döndür"""
    if key in _price_cache:
        val, ts = _price_cache[key]
        if time.time() - ts < _CACHE_TTL:
            return val
    return None

def _set_cache(key: str, value):
    """Cache'e fiyat yaz"""
    _price_cache[key] = (value, time.time())

def _fetch_yahoo_price_raw(ticker: str) -> float:
    """Yahoo Finance'den fiyat çek - birden fazla yöntemle dene"""
    
    # Yöntem 1: Yahoo Finance v8 API (requests ile direkt)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"interval": "1d", "range": "1d"}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice", 0)
                if price and price > 0:
                    print(f"[Yahoo API] {ticker} = {price}")
                    return float(price)
    except Exception as e:
        print(f"[Yahoo API] v8 failed for {ticker}: {e}")
    
    # Yöntem 2: yfinance fast_info
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        price = fi.get("lastPrice", 0) or fi.get("last_price", 0)
        if price and not math.isnan(price) and price > 0:
            print(f"[yfinance fast_info] {ticker} = {price}")
            return float(price)
    except Exception as e:
        print(f"[yfinance fast_info] failed for {ticker}: {e}")
    
    # Yöntem 3: yfinance history (en yavaş)
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            if not math.isnan(price) and price > 0:
                print(f"[yfinance history] {ticker} = {price}")
                return float(price)
    except Exception as e:
        print(f"[yfinance history] failed for {ticker}: {e}")
    
    return 0.0

def _get_usd_try_rate() -> float:
    """USDTRY kurunu çek, cache'li"""
    cached = _get_from_cache("USDTRY")
    if cached:
        return cached
    
    rate = _fetch_yahoo_price_raw("USDTRY=X")
    if rate > 0:
        _set_cache("USDTRY", rate)
        return rate
    
    # Fallback
    return 38.0

def get_live_price_in_try(currency: str) -> Decimal:
    if currency == "TRY":
        return Decimal('1.00')
    
    # Cache kontrolü
    cached = _get_from_cache(f"price_try_{currency}")
    if cached:
        return cached

    ticker = TICKER_MAP.get(currency, currency)
    
    try:
        price = _fetch_yahoo_price_raw(ticker)
        
        if price <= 0:
            raise ValueError(f"Could not fetch price for {ticker}")
        
        # USD veya EUR/TRY direkt pariteler zaten TRY cinsinden
        if currency in ["USD", "EUR"]:
            # USDTRY=X ve EURTRY=X zaten TRY cinsinden döner
            result = Decimal(str(round(price, 4)))
        elif currency in ["XAU", "XAG", "BTC", "ETH", "SOL"]:
            # Bunlar USD cinsinden, TRY'ye çevir
            usd_try = _get_usd_try_rate()
            result = Decimal(str(round(price * usd_try, 2)))
        elif ticker.endswith(".IS"):
            # BIST hisseleri zaten TRY cinsinden
            result = Decimal(str(round(price, 2)))
        else:
            # S&P 500 ve diğer USD hisseleri
            usd_try = _get_usd_try_rate()
            result = Decimal(str(round(price * usd_try, 2)))
        
        _set_cache(f"price_try_{currency}", result)
        return result
    
    except Exception as e:
        print(f"[PRICE ERROR] {currency} (ticker: {ticker}): {e}")
        fallbacks = {
            "USD": Decimal('38.00'),
            "EUR": Decimal('41.50'),
            "BTC": Decimal('3200000.00'),
            "ETH": Decimal('135000.00'),
            "SOL": Decimal('5600.00'),
            "XAU": Decimal('110000.00'),
            "XAG": Decimal('1250.00')
        }
        return fallbacks.get(currency, Decimal('100.00'))

@router.get("/prices", response_model=list[schemas.MarketPriceResponse])
def get_all_prices():
    prices = []
    core_assets = ["USD", "EUR", "BTC", "ETH", "SOL", "XAU", "XAG"]
    for currency in core_assets:
        price = get_live_price_in_try(currency)
        prices.append(
            schemas.MarketPriceResponse(
                currency=currency,
                price_in_try=price,
                last_updated=datetime.now()
            )
        )
    return prices

@router.get("/stocks/bist100", response_model=list[schemas.MarketPriceResponse])
def get_bist100_prices():
    tickers = ["THYAO.IS", "KCHOL.IS", "TUPRS.IS", "AKBNK.IS", "YKBNK.IS", 
               "ISCTR.IS", "SAHOL.IS", "EREGL.IS", "ASELS.IS", "BIMAS.IS", 
               "GARAN.IS", "SISE.IS", "FROTO.IS", "ENKAI.IS", "PGSUS.IS"]
    return fetch_prices_for_tickers(tickers, is_usd=False)

@router.get("/stocks/sp500", response_model=list[schemas.MarketPriceResponse])
def get_sp500_prices():
    tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "META", 
               "GOOGL", "TSLA", "BRK-B", "LLY", "AVGO", 
               "JPM", "V", "WMT", "UNH", "MA"]
    return fetch_prices_for_tickers(tickers, is_usd=True)

def fetch_prices_for_tickers(tickers: list[str], is_usd: bool):
    prices = []
    usd_to_try = _get_usd_try_rate() if is_usd else 1.0
    
    for t in tickers:
        try:
            cached = _get_from_cache(f"stock_{t}")
            if cached:
                prices.append(cached)
                continue
                
            price = _fetch_yahoo_price_raw(t)
            
            if price <= 0:
                raise ValueError(f"Zero/negative price for {t}")
            
            if is_usd:
                price = price * usd_to_try
            
            entry = schemas.MarketPriceResponse(
                currency=t,
                price_in_try=Decimal(str(round(price, 2))),
                last_updated=datetime.now()
            )
            _set_cache(f"stock_{t}", entry)
            prices.append(entry)
            
        except Exception as e:
            print(f"[STOCK ERROR] {t}: {e}")
            prices.append(
                schemas.MarketPriceResponse(
                    currency=t,
                    price_in_try=Decimal('0.00'),
                    last_updated=datetime.now()
                )
            )
    return prices

@router.post("/trade", response_model=schemas.LedgerResponse)
@limiter.limit(TRADE_LIMIT)
def execute_trade(request: Request, trade: schemas.TradeRequest, current_user: models.Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    """User wants to buy `to_currency` using `from_currency`. Amount is in `to_currency`."""
    
    if trade.from_currency == trade.to_currency:
        raise HTTPException(status_code=400, detail="Cannot trade same currency.")

    # Only support trading against TRY for simplicity.
    if trade.from_currency != "TRY" and trade.to_currency != "TRY":
         raise HTTPException(status_code=400, detail="All trades must be paired with TRY.")

    # 1. Fetch live price
    if trade.to_currency != "TRY":
         # Buying an asset with TRY
         asset_price_in_try = get_live_price_in_try(trade.to_currency)
         cost_in_try = trade.amount * asset_price_in_try
    else:
         # Selling an asset for TRY
         asset_price_in_try = get_live_price_in_try(trade.from_currency)
         cost_in_try = trade.amount * asset_price_in_try

    # 2. Get or Create Accounts
    from_account = db.query(models.Account).filter(models.Account.customer_id == current_user.id, models.Account.currency == trade.from_currency).first()
    to_account = db.query(models.Account).filter(models.Account.customer_id == current_user.id, models.Account.currency == trade.to_currency).first()

    if not from_account:
        from_account = models.Account(customer_id=current_user.id, currency=trade.from_currency, balance=0)
        db.add(from_account)
        db.commit()
    
    if not to_account:
        to_account = models.Account(customer_id=current_user.id, currency=trade.to_currency, balance=0)
        to_account = models.Account(customer_id=current_user.id, currency=trade.to_currency, balance=0, cost_basis_try=0)
        db.add(to_account)
        db.commit()

    # 3. Validation
    if trade.to_currency != "TRY":
         # Buying: deduct TRY, add Asset
         if from_account.balance < cost_in_try:
             raise HTTPException(status_code=400, detail=f"Insufficient funds. You need {cost_in_try} TRY, but have {from_account.balance} TRY.")
         
         from_account.balance -= cost_in_try
         
         # ZERO-COST BASIS NORMALIZATION: 
         # If the account has a balance but 0 cost basis (e.g., migrated), normalize it before adding the new cost
         if to_account.balance > 0 and (to_account.cost_basis_try is None or to_account.cost_basis_try == 0):
             to_account.cost_basis_try = to_account.balance * asset_price_in_try
             
         to_account.balance += trade.amount
         to_account.cost_basis_try += cost_in_try
         
         # Ledger (Deposit into Asset Account)
         ledger_entry = models.Ledger(
             from_account_id=from_account.id,
             to_account_id=to_account.id,
             amount=trade.amount,
             transaction_type=models.TransactionTypeEnum.transfer
         )

    else:
         # Selling: deduct Asset, add TRY
         if from_account.balance < trade.amount:
              raise HTTPException(status_code=400, detail=f"Insufficient funds. You need {trade.amount} {trade.from_currency}, but have {from_account.balance}.")
              
         original_asset_balance = from_account.balance # Balance before deduction
         
         # Proportional cost basis reduction
         if original_asset_balance > 0: # Avoid division by zero
             fraction = trade.amount / original_asset_balance
             from_account.cost_basis_try -= (from_account.cost_basis_try * fraction)
         
         from_account.balance -= trade.amount
         to_account.balance += cost_in_try

         # Ledger
         ledger_entry = models.Ledger(
             from_account_id=from_account.id,
             to_account_id=to_account.id,
             amount=cost_in_try, # Amount in TRY 
             transaction_type=models.TransactionTypeEnum.transfer
         )

    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)
    
    return ledger_entry
