from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import yfinance as yf
from datetime import datetime
from decimal import Decimal
from security import get_current_user

router = APIRouter(prefix="/trading", tags=["Trading"])

# Mapping of our internal string codes to Yahoo Finance tickers
TICKER_MAP = {
    "USD": "TRY=X",      # USD to TRY
    "EUR": "EURTRY=X",
    "BTC": "BTC-TRY",
    "ETH": "ETH-TRY",
    "SOL": "SOL-TRY",
    "XAU": "GC=F",       # Gold Futures (USD)
    "XAG": "SI=F",       # Silver Futures (USD)
}

def get_live_price_in_try(currency: str) -> Decimal:
    if currency == "TRY":
        return Decimal('1.00')

    # If it's a known crypto/forex, use the mapped ticker. 
    # Otherwise, assume the currency string IS the stock ticker.
    ticker = TICKER_MAP.get(currency, currency)
    
    try:
        data = yf.Ticker(ticker)
        # Using history to get the latest close price
        price = data.history(period="1d")['Close'].iloc[-1]
        
        # Determine if we need to convert to TRY.
        # USD-based: XAU, XAG, and any S&P 500 stock (no .IS suffix and not EUR/Crypto/USD).
        needs_usd_conversion = False
        if currency in ["XAU", "XAG"] or (not ticker.endswith(".IS") and currency not in ["EUR", "BTC", "ETH", "SOL", "TRY", "USD"]):
            needs_usd_conversion = True
            
        if needs_usd_conversion:
            # Fetch USDTRY rate
            usd_data = yf.Ticker("TRY=X")
            usd_to_try = usd_data.history(period="1d")['Close'].iloc[-1]
            price = price * usd_to_try
            
        return Decimal(str(round(price, 2)))
    
    except Exception as e:
        print(f"Error fetching price for {currency} (ticker: {ticker}): {e}")
        # In case API fails (weekends, rate limits), provide generic fallbacks
        fallbacks = {
            "USD": Decimal('32.50'),
            "EUR": Decimal('35.10'),
            "BTC": Decimal('2050000.00'),
            "ETH": Decimal('100000.00'),
            "SOL": Decimal('4500.00'),
            "XAU": Decimal('80000.00'),
            "XAG": Decimal('1000.00')
        }
        # Generic fallback for unmapped stocks
        return fallbacks.get(currency, Decimal('100.00'))

@router.get("/prices", response_model=list[schemas.MarketPriceResponse])
def get_all_prices():
    prices = []
    # Core crypto/forex assets
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
    try:
        # yf.download is much faster for batches but returns a DataFrame that's trickier to parse.
        # Using threads or just downloading directly:
        data = yf.download(tickers, period="1d", group_by='ticker', progress=False)
        
        usd_to_try = 1.0
        if is_usd:
            usd_data = yf.Ticker("TRY=X")
            usd_to_try = usd_data.history(period="1d")['Close'].iloc[-1]
            
        for t in tickers:
            try:
                if len(tickers) == 1:
                    price = data['Close'].iloc[-1]
                else:
                    # Depending on yfinance version, the MultiIndex might differ
                    if ('Close', t) in data.columns:
                        price = data['Close', t].iloc[-1]
                    else:
                        price = data[t]['Close'].iloc[-1]
                
                # Convert to scalar python float if it's a pandas/numpy object
                price = float(price)

                if is_usd:
                    price = price * usd_to_try
                    
                prices.append(
                    schemas.MarketPriceResponse(
                        currency=t,
                        price_in_try=Decimal(str(round(price, 2))),
                        last_updated=datetime.now()
                    )
                )
            except Exception as e:
                print(f"Error parsing dataframe for {t}: {e}")
                # Fallback to sequential if dataframe parsing fails for one
                prices.append(
                    schemas.MarketPriceResponse(
                        currency=t,
                        price_in_try=get_live_price_in_try(t),
                        last_updated=datetime.now()
                    )
                )
        return prices
    except Exception as e:
        print(f"Batch download failed: {e}")
        # Complete fallback
        for t in tickers:
            prices.append(
                schemas.MarketPriceResponse(
                    currency=t,
                    price_in_try=get_live_price_in_try(t),
                    last_updated=datetime.now()
                )
            )
        return prices

@router.post("/trade", response_model=schemas.LedgerResponse)
def execute_trade(trade: schemas.TradeRequest, current_user: models.Customer = Depends(get_current_user), db: Session = Depends(get_db)):
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
        db.add(to_account)
        db.commit()

    # 3. Validation
    if trade.to_currency != "TRY":
         # Buying: deduct TRY, add Asset
         if from_account.balance < cost_in_try:
             raise HTTPException(status_code=400, detail=f"Insufficient funds. You need {cost_in_try} TRY, but have {from_account.balance} TRY.")
         
         from_account.balance -= cost_in_try
         to_account.balance += trade.amount
         
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
