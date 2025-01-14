from fastapi import APIRouter
from core.event import TradeEvent, EquityEvent, SyncEvent
from core.trade.ledger import ledger
from core.ops.schema import Order, Experiment
from core.ops.operator import async_ops
from .login import get_current_user

router = APIRouter()


@router.post("/on_execute")
async def on_execute(event: TradeEvent):
    # execute trade
    order, txns = await ledger.on_trade(event)
    
    user = await get_current_user(event.token)
    experiment = Experiment(user_id=user.id, experiment_id=event.experiment_id)
    
    order.experiment = experiment
    order.transactions.extend(txns)
    await async_ops.on_insert_obj(order)

    txns.order = order
    await async_ops.on_insert_obj(txns)


@router.post("/on_event")
async def on_event(event: EquityEvent):
        avaiable = await ledger.on_event(event)
        return avaiable


@router.post("/on_sync")
async def on_sync(event: SyncEvent):
        obj_account, obj_metrics = await ledger.on_end_of_day(event)
        experiment = Experiment(**event.experiment.model_dump())
        obj_account.experiment = experiment
        await async_ops.on_insert_obj(obj_account)
        return obj_metrics


@router.get("/api")
def api():
    return {"trade": "trade"}

