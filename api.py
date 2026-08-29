
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel

import os
import sqlite3
from datetime import datetime



# CONFIG


BASE_DIR = "/content/drive/MyDrive/RecoverAI"

DB_PATH = os.path.join(
    BASE_DIR,
    "recoverai.db"
)



# FASTAPI


app = FastAPI(
    title="RecoverAI",
    description="AI Payment Recovery Agent",
    version="1.0"
)



# PAYMENT MODEL


class PaymentRequest(BaseModel):

    payment_id: str
    customer_id: str
    amount: float
    payment_method: str
    failure_reason: str

    previous_success: int
    previous_failure: int
    customer_age_days: int

    previous_recovery_attempts: int
    transaction_hour: int



# HOME


@app.get("/")
def home():

    return {
        "application": "RecoverAI",
        "status": "running",
        "version": "1.0"
    }



# HEALTH


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "RecoverAI"
    }



# RAZORPAY WEBHOOK


@app.post("/razorpay/webhook")
async def razorpay_webhook(

    request: Request,

    x_razorpay_signature:
        str = Header(None),

    x_razorpay_event_id:
        str = Header(None)

):

    from __main__ import verify_razorpay_webhook

    raw_body = await request.body()


    webhook_secret = os.environ.get(
        "RAZORPAY_WEBHOOK_SECRET",
        ""
    )


    if not webhook_secret:

        raise HTTPException(
            status_code=500,
            detail="RAZORPAY_WEBHOOK_SECRET not configured."
        )


    if not x_razorpay_signature:

        raise HTTPException(
            status_code=400,
            detail="Missing X-Razorpay-Signature."
        )


    valid = verify_razorpay_webhook(
        raw_body,
        x_razorpay_signature,
        webhook_secret
    )


    if not valid:

        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature."
        )


    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload."
        )


    event = payload.get(
        "event",
        ""
    )


    event_id = (
        x_razorpay_event_id
        or payload.get("id")
    )


    if not event_id:

        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay event ID."
        )


    conn = sqlite3.connect(DB_PATH)

    existing = conn.execute(
        """
        SELECT event_id
        FROM razorpay_webhook_events
        WHERE event_id = ?
        """,
        (event_id,)
    ).fetchone()

    conn.close()


    if existing:

        return {
            "success": True,
            "message": "Webhook already processed.",
            "event_id": event_id
        }


    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )


    razorpay_payment_id = (
        payment_entity.get("id")
    )


    razorpay_order_id = (
        payment_entity.get("order_id")
    )


    amount_paise = (
        payment_entity.get("amount", 0)
    )


    amount_rupees = (
        float(amount_paise) / 100
    )


    payment_id = None


    if razorpay_order_id:

        conn = sqlite3.connect(DB_PATH)

        row = conn.execute(
            """
            SELECT payment_id
            FROM razorpay_orders
            WHERE order_id = ?
            LIMIT 1
            """,
            (razorpay_order_id,)
        ).fetchone()

        conn.close()


        if row:

            payment_id = row[0]


    status = None
    recovered_amount = 0


    if event == "payment.captured":

        status = "SUCCESS"
        recovered_amount = amount_rupees


    elif event == "payment.failed":

        status = "FAILED"
        recovered_amount = 0


    if payment_id and status:

        customer_message = (

            "Payment successfully recovered through Razorpay."
            if status == "SUCCESS"
            else
            "Razorpay payment attempt failed."
        )


        conn = sqlite3.connect(DB_PATH)

        conn.execute(
            """
            UPDATE recovery_actions

            SET
                gateway_status = ?,
                transaction_id = ?,
                amount_recovered = ?,
                customer_message = ?

            WHERE payment_id = ?
            """,
            (
                status,
                razorpay_payment_id,
                recovered_amount,
                customer_message,
                payment_id
            )
        )

        conn.commit()
        conn.close()


    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT OR IGNORE INTO
        razorpay_webhook_events

        (
            event_id,
            event_type,
            razorpay_payment_id,
            razorpay_order_id,
            payment_id,
            processed_at
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event,
            razorpay_payment_id,
            razorpay_order_id,
            payment_id,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


    print("==========================================")
    print(" RAZORPAY WEBHOOK RECEIVED")
    print("Event:", event)
    print("Razorpay Payment ID:", razorpay_payment_id)
    print("Razorpay Order ID:", razorpay_order_id)
    print("RecoverAI Payment ID:", payment_id)
    print("Status:", status)
    print("Amount:", amount_rupees)
    print("==========================================")


    return {

        "success": True,

        "event": event,

        "payment_id": payment_id,

        "razorpay_payment_id":
            razorpay_payment_id,

        "razorpay_order_id":
            razorpay_order_id,

        "status": status
    }


print(" FINAL RecoverAI api.py CREATED")
