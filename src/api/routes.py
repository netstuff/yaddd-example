from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from yaddd import EntityNotFoundError

from api.schemas import OrderResponse, PlaceOrderRequest
from application.commands import GetOrder, PlaceOrder
from application.dto import OrderDTO
from composition_root import CompositionRoot

router = APIRouter(prefix="/orders", tags=["orders"])


def get_composition_root(request: Request) -> CompositionRoot:
    return cast(CompositionRoot, request.app.state.composition_root)


@router.post("", status_code=201)
async def create_order(
    data: PlaceOrderRequest,
    root: Annotated[CompositionRoot, Depends(get_composition_root)],
) -> OrderResponse:
    order_id = cast(
        UUID,
        await root.command_bus.dispatch(PlaceOrder(total=data.total)),
    )
    return OrderResponse(order_id=str(order_id), total=data.total)


@router.get("/{order_id}")
async def read_order(
    order_id: UUID,
    root: Annotated[CompositionRoot, Depends(get_composition_root)],
) -> OrderResponse:
    try:
        dto = cast(
            OrderDTO,
            await root.query_bus.dispatch(GetOrder(order_id=order_id)),
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrderResponse(order_id=str(dto.order_id), total=dto.total)
