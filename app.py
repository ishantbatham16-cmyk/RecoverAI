
import streamlit as st
import sqlite3
import pandas as pd
import joblib
import os
import streamlit.components.v1 as components
from datetime import datetime



# CONFIG


st.set_page_config(
    page_title="RecoverAI",
    page_icon="💳",
    layout="wide"
)


BASE_DIR = "/content/drive/MyDrive/RecoverAI"


MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "recovery_model.pkl"
)


DB_PATH = os.path.join(
    BASE_DIR,
    "recoverai.db"
)



# LOAD MODEL


model = joblib.load(
    MODEL_PATH
)



# DATABASE


def load_recovery_history():

    conn = sqlite3.connect(
        DB_PATH
    )

    df = pd.read_sql_query(
        """
        SELECT
            payment_id,
            probability,
            action,
            policy_reason,
            gateway_status,
            transaction_id,
            amount_recovered,
            customer_message,
            created_at
        FROM recovery_actions
        ORDER BY created_at DESC
        LIMIT 20
        """,
        conn
    )

    conn.close()

    return df



# ML PREDICTION


def predict_probability(payment):

    data = pd.DataFrame([{

        "amount":
            payment["amount"],

        "payment_method":
            payment["payment_method"],

        "failure_reason":
            payment["failure_reason"],

        "previous_success":
            payment["previous_success"],

        "previous_failure":
            payment["previous_failure"],

        "customer_age_days":
            payment["customer_age_days"],

        "previous_recovery_attempts":
            payment["previous_recovery_attempts"],

        "transaction_hour":
            payment["transaction_hour"]

    }])


    probability = model.predict_proba(
        data
    )[0][1]


    return float(
        probability
    )



# POLICY ENGINE


def policy_decision(
    payment,
    probability
):

    amount = payment["amount"]

    failure_reason = payment[
        "failure_reason"
    ]

    attempts = payment[
        "previous_recovery_attempts"
    ]


    if attempts >= 2:

        return {

            "action":
                "STOP",

            "reason":
                "Maximum recovery attempts reached."

        }


    if failure_reason == "card_expired":

        return {

            "action":
                "UPDATE_PAYMENT_METHOD",

            "reason":
                "Payment method has expired."

        }


    if amount >= 50000:

        return {

            "action":
                "HUMAN_REVIEW",

            "reason":
                "High-value payment requires human review."

        }


    if probability < 0.30:

        return {

            "action":
                "STOP",

            "reason":
                "Recovery probability is too low."

        }


    if probability >= 0.70:

        return {

            "action":
                "RETRY",

            "reason":
                "High probability of payment recovery."

        }


    return {

        "action":
            "REMINDER",

        "reason":
            "Moderate recovery probability."

    }



# GEMINI


def generate_ai_explanation(
    payment,
    probability,
    action,
    reason
):

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )


    if not api_key:

        return (
            "Gemini explanation unavailable because "
            "GEMINI_API_KEY is not configured."
        )


    prompt = f"""
You are RecoverAI, an AI payment recovery assistant.

Explain the recovery decision safely.

Rules:
- Never override the policy decision.
- Never request OTP, PIN, CVV or password.
- Never claim payment success unless gateway confirms it.
- Keep the explanation professional and concise.

Payment ID: {payment["payment_id"]}
Customer ID: {payment["customer_id"]}
Amount: ₹{payment["amount"]}
Payment Method: {payment["payment_method"]}
Failure Reason: {payment["failure_reason"]}

Previous Successful Payments:
{payment["previous_success"]}

Previous Failed Payments:
{payment["previous_failure"]}

Customer Age:
{payment["customer_age_days"]} days

Previous Recovery Attempts:
{payment["previous_recovery_attempts"]}

ML Recovery Probability:
{probability:.2%}

Policy Action:
{action}

Policy Reason:
{reason}

Return:

Why:
Customer Context:
Next Step:
Risk Note:
"""


    try:

        from google import genai


        client = genai.Client(
            api_key=api_key
        )


        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt

        )


        return response.text


    except Exception as e:

        return (
            "Gemini explanation could not be generated.\n\n"
            f"Reason: {str(e)}"
        )



# CUSTOMER MESSAGE


def customer_message(
    payment,
    action
):

    if action == "RETRY":

        return (
            f"We detected that your payment of "
            f"₹{payment['amount']:,.2f} failed temporarily. "
            "A recovery retry is recommended."
        )


    if action == "UPDATE_PAYMENT_METHOD":

        return (
            "Your payment method appears to require attention. "
            "Please use an active payment method."
        )


    if action == "HUMAN_REVIEW":

        return (
            "Your payment requires additional review. "
            "Our team will assist you."
        )


    if action == "REMINDER":

        return (
            "Your recent payment could not be completed. "
            "Please try again when convenient."
        )


    return (
        "The payment could not be recovered automatically. "
        "Please try another payment method."
    )



# RAZORPAY ORDER MAPPING


def save_razorpay_order_mapping(
    order_id,
    payment_id,
    amount
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        INSERT OR REPLACE INTO razorpay_orders
        (
            order_id,
            payment_id,
            amount,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        order_id,
        payment_id,
        amount,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    conn = sqlite3.connect(
        DB_PATH
    )


    conn.execute(
        """
        INSERT OR REPLACE INTO
        razorpay_orders

        (
            order_id,
            payment_id,
            created_at
        )

        VALUES (?, ?, ?)
        """,

        (
            order_id,
            payment_id,
            datetime.now().isoformat()
        )

    )


    conn.commit()

    conn.close()



# UI HEADER


st.title(
    "💳 RecoverAI"
)


st.caption(
    "AI-Powered Payment Recovery Agent"
)


st.write(
    "Predict payment recovery probability, "
    "apply policy guardrails and generate "
    "an AI-assisted recovery decision."
)


st.divider()



# PAYMENT INPUT


st.subheader(
    "💰 Payment Information"
)


col1, col2, col3 = st.columns(3)


with col1:

    payment_id = st.text_input(
        "Payment ID",
        value="PAY-UI-001"
    )


    customer_id = st.text_input(
        "Customer ID",
        value="CUST-UI-001"
    )


    amount = st.number_input(
        "Amount (₹)",
        min_value=1.0,
        value=5000.0,
        step=100.0
    )


with col2:

    payment_method = st.selectbox(
        "Payment Method",

        [
            "UPI",
            "CARD",
            "NETBANKING",
            "WALLET"
        ]
    )


    failure_reason = st.selectbox(
        "Failure Reason",

        [
            "bank_timeout",
            "insufficient_funds",
            "card_expired",
            "network_error",
            "authentication_failed"
        ]
    )


    previous_success = st.number_input(
        "Previous Successful Payments",
        min_value=0,
        value=15
    )


with col3:

    previous_failure = st.number_input(
        "Previous Failed Payments",
        min_value=0,
        value=1
    )


    customer_age_days = st.number_input(
        "Customer Age (days)",
        min_value=1,
        value=500
    )


    previous_recovery_attempts = st.number_input(
        "Previous Recovery Attempts",
        min_value=0,
        value=0
    )


transaction_hour = st.slider(
    "Transaction Hour",
    0,
    23,
    14
)



# ANALYZE BUTTON


if st.button(
    "🤖 Analyze Payment",
    use_container_width=True
):


    payment = {

        "payment_id":
            payment_id,

        "customer_id":
            customer_id,

        "amount":
            amount,

        "payment_method":
            payment_method,

        "failure_reason":
            failure_reason,

        "previous_success":
            previous_success,

        "previous_failure":
            previous_failure,

        "customer_age_days":
            customer_age_days,

        "previous_recovery_attempts":
            previous_recovery_attempts,

        "transaction_hour":
            transaction_hour

    }


    with st.spinner(
        "RecoverAI is analyzing the payment..."
    ):

        probability = predict_probability(
            payment
        )


        policy = policy_decision(
            payment,
            probability
        )


        action = policy[
            "action"
        ]


        reason = policy[
            "reason"
        ]


        ai_explanation = generate_ai_explanation(

            payment,

            probability,

            action,

            reason

        )


        message = customer_message(

            payment,

            action

        )


    st.session_state["result"] = {

        "payment":
            payment,

        "probability":
            probability,

        "action":
            action,

        "reason":
            reason,

        "ai_explanation":
            ai_explanation,

        "message":
            message

    }



# DISPLAY RESULT


if "result" in st.session_state:


    result = st.session_state[
        "result"
    ]


    payment = result[
        "payment"
    ]


    probability = result[
        "probability"
    ]


    action = result[
        "action"
    ]


    st.divider()


    st.subheader(
        "📊 RecoverAI Decision"
    )


    c1, c2, c3 = st.columns(3)


    with c1:

        st.metric(

            "Recovery Probability",

            f"{probability:.2%}"

        )


    with c2:

        st.metric(

            "Policy Decision",

            action

        )


    with c3:

        st.metric(

            "Payment Amount",

            f"₹{payment['amount']:,.2f}"

        )


    st.progress(
        probability
    )


    st.info(
        f"""
**Payment ID:** {payment["payment_id"]}

**Customer ID:** {payment["customer_id"]}

**Failure Reason:** {payment["failure_reason"]}

**Policy Reason:** {result["reason"]}
"""
    )


    st.subheader(
        "🤖 AI Recovery Analysis"
    )


    st.write(
        result["ai_explanation"]
    )


    st.subheader(
        "💬 Customer Message"
    )


    st.success(
        result["message"]
    )


    # ========================================================
    # RAZORPAY TEST CHECKOUT
    # ========================================================

    if action == "RETRY":

        st.divider()


        st.subheader(
            "💳 Razorpay TEST Mode"
        )


        st.warning(
            "TEST MODE ONLY — No real money will be charged."
        )


        if st.button(
            "🔄 Create Razorpay Test Retry Order",
            use_container_width=True
        ):

            try:

                import razorpay


                key_id = os.environ.get(
                    "RAZORPAY_KEY_ID"
                )


                key_secret = os.environ.get(
                    "RAZORPAY_KEY_SECRET"
                )


                if not key_id or not key_secret:

                    st.error(
                        "Razorpay TEST credentials "
                        "are not configured."
                    )

                else:

                    rp_client = razorpay.Client(

                        auth=(

                            key_id,

                            key_secret

                        )

                    )


                    order = rp_client.order.create({

                        "amount":
                            int(
                                payment["amount"] * 100
                            ),

                        "currency":
                            "INR",

                        "receipt":
                            payment["payment_id"],

                        "notes": {

                            "source":
                                "RecoverAI",

                            "mode":
                                "TEST",

                            "payment_id":
                                payment["payment_id"]

                        }

                    })


                    # Save mapping
                    save_razorpay_order_mapping(
    order["id"],
    payment["payment_id"],
    payment["amount"]
)


                    st.session_state[
                        "razorpay_order"
                    ] = order


                    st.success(
                        "Razorpay TEST order created!"
                    )


            except Exception as e:

                st.error(
                    f"Razorpay error: {str(e)}"
                )


    
    # RAZORPAY CHECKOUT
    

    if "razorpay_order" in st.session_state:

        order = st.session_state[
            "razorpay_order"
        ]


        st.subheader(
            "🧾 Razorpay TEST Checkout"
        )


        st.metric(
            "Order Amount",
            f"₹{order['amount']/100:,.2f}"
        )


        st.code(
            order["id"]
        )


        key_id = os.environ.get(
            "RAZORPAY_KEY_ID"
        )


        if key_id:

            checkout_html = f"""

            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

            <button
                id="rzp-button"
                style="
                    background:#0d6efd;
                    color:white;
                    border:none;
                    padding:12px 24px;
                    border-radius:8px;
                    font-size:16px;
                    cursor:pointer;
                "
            >
                💳 Open Razorpay TEST Checkout
            </button>


            <script>

            document.getElementById(
                "rzp-button"
            ).onclick = function(e) {{

                var options = {{

                    "key":
                        "{key_id}",

                    "amount":
                        "{order['amount']}",

                    "currency":
                        "INR",

                    "name":
                        "RecoverAI",

                    "description":
                        "Payment Recovery TEST",

                    "order_id":
                        "{order['id']}",

                    "handler":
                        function(response) {{

                        alert(
                            "Payment submitted successfully!\\n\\n"
                            +
                            "Payment ID: "
                            +
                            response.razorpay_payment_id
                        );

                    }},

                    "prefill": {{

                        "name":
                            "{payment['customer_id']}"

                    }},

                    "theme": {{

                        "color":
                            "#0d6efd"

                    }}

                }};


                var rzp1 =
                    new Razorpay(options);


                rzp1.on(
                    "payment.failed",
                    function(response) {{

                    alert(
                        "TEST payment failed.\\n\\n"
                        +
                        "Reason: "
                        +
                        response.error.description
                    );

                }});


                rzp1.open();


                e.preventDefault();

            }};

            </script>

            """


            components.html(
                checkout_html,
                height=100
            )


            st.info(
                "Complete the payment using Razorpay TEST MODE. "
                "The final SUCCESS/FAILED status is confirmed "
                "by the Razorpay webhook."
            )


        else:

            st.error(
                "Razorpay TEST Key ID is not configured."
            )



# HISTORY


st.divider()


st.subheader(
    "📜 Recovery History"
)


try:

    history = load_recovery_history()


    if len(history) > 0:

        st.dataframe(

            history,

            use_container_width=True,

            hide_index=True

        )

    else:

        st.info(
            "No recovery events available."
        )


except Exception as e:

    st.warning(
        f"Could not load history: {str(e)}"
    )
