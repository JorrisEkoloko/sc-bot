import asyncio
from services.pricing.historical_price_service import HistoricalPriceService
from datetime import datetime

async def test():
    svc = HistoricalPriceService()
    result = await svc.fetch_ohlc_window(
        'PEAS', 
        datetime(2025, 9, 3, 19, 23, 47), 
        30, 
        '0x02f92800F57BCD74066F5709F1Daa1A4302Df875', 
        'ethereum'
    )
    print(f'Result: {result}')
    await svc.close()

asyncio.run(test())
