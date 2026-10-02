from workshop.domain import ORDERS


def get_delivery_status(order_id: str) -> dict:
    """Look up delivery status for a demo order by exact ID."""
    order = ORDERS.get(order_id)
    if order is None:
        return {"status": "not_found"}
    return {"status": "found", "order_id": order_id, "delivery_status": order["status"]}
