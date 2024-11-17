from fastapi import APIRouter
from core.event import TradeEvent, Event, SyncEvent
from core.ledger import ledger

router = APIRouter()


@router.post("/on_trade/")
async def on_trade(event: TradeEvent):
            # insert order
            txns = await ledger.on_trade(event)
            # async_ops.on_insert(txns)


@router.post("/on_event/")
async def on_event(event: Event):
        await ledger.on_event(event)


@router.post("/on_sync/")
async def on_sync(event: SyncEvent):
             # insert account data
             await ledger.on_sync(event)


@router.get("/test")
async def test():
    return {"test": "test"}
