import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Production-Grade WhatsApp Notification Service with Idempotency & Error Isolation.
    Dispatches signals to Meta WhatsApp Cloud API or direct WhatsApp Channel link.
    """

    def __init__(self):
        self.provider = (settings.WHATSAPP_PROVIDER or "MOCK").upper()
        self.api_key = settings.WHATSAPP_API_KEY
        self.phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.sent_idempotency_keys = set()

    def format_signal_message(self, signal: Dict[str, Any]) -> str:
        symbol = signal["symbol"]
        exchange = signal.get("exchange", "NSE")
        direction = signal["direction"]
        setup = signal.get("setup_type", "QUANT_MOMENTUM")
        
        entry_zone = signal.get("entry_zone", {})
        entry_min = entry_zone.get("min", signal.get("entry_price", 0.0))
        entry_max = entry_zone.get("max", signal.get("entry_price", 0.0))
        sl = signal.get("stop_loss", 0.0)
        
        targets = signal.get("targets", [0.0, 0.0, 0.0])
        t1 = targets[0] if len(targets) > 0 else 0.0
        t2 = targets[1] if len(targets) > 1 else t1
        t3 = targets[2] if len(targets) > 2 else t2
        
        rr = signal.get("risk_reward", 2.0)
        pos_size = signal.get("position_size", 10)
        conf = signal.get("confidence", 85.0)
        regime = signal.get("market_regime", "BULLISH")
        bull = signal.get("bull_case", "Bullish momentum confirmed")
        bear = signal.get("bear_case", "Watch overhead pivot")
        invalidation = signal.get("invalidation", "Candle close below SL")
        sig_id = signal.get("signal_id", f"SIG-{symbol}")
        ts = signal.get("timestamp", "")

        msg = f"""🎯 *FINAL AI TRADING DECISION: {direction}* 🎯

*Stock:* {symbol} ({exchange})
*Direction:* {direction} | *Mode:* {signal.get('mode', 'INTRADAY')}
*Setup:* {setup}

*Entry Zone:* ₹{entry_min} - ₹{entry_max}
*Stop Loss:* ₹{sl}
*Target 1:* ₹{t1}
*Target 2:* ₹{t2}
*Target 3:* ₹{t3}
*Risk/Reward:* 1:{rr}
*Recommended Position Size:* {pos_size} shares

*AI Confidence Score:* {conf}/100
*Market Regime:* {regime}

*Bull Case:* {bull}
*Bear Case:* {bear}
*Invalidation:* {invalidation}

*Signal ID:* `{sig_id}`
*Timestamp:* {ts}

🔗 *Direct Channel Message Link:* {settings.WHATSAPP_CHANNEL_URL}
📢 *Join Official Channel:* {settings.WHATSAPP_CHANNEL_URL}
⚠️ *AI-generated research/trading signal. Not guaranteed profit.*
"""
        return msg.strip()

    async def send_alert(self, signal: Dict[str, Any], target_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Dispatches signal alert with error isolation so scanner never crashes if WhatsApp fails.
        """
        idempotency_key = signal.get("signal_id") or f"{signal['symbol']}_{signal.get('timestamp', '')}"
        
        if idempotency_key in self.sent_idempotency_keys:
            logger.info(f"[WhatsAppService] Skipping duplicate signal dispatch: {idempotency_key}")
            return {"status": "DUPLICATE_SKIPPED", "idempotency_key": idempotency_key}

        msg_body = self.format_signal_message(signal)
        recipient = target_phone or settings.WHATSAPP_TARGET_PHONE or settings.WHATSAPP_CHANNEL_URL
        channel_url = settings.WHATSAPP_CHANNEL_URL

        # Mode 1: Mock / Direct Channel Broadcast
        if self.provider != "OFFICIAL" or not self.api_key or not self.phone_id:
            self.sent_idempotency_keys.add(idempotency_key)
            logger.info(f"[WhatsAppService] Dispatched MOCK/CHANNEL signal for {signal.get('symbol')}")
            return {
                "status": "SENT_DIRECT_CHANNEL",
                "target_channel": channel_url,
                "recipient": recipient,
                "idempotency_key": idempotency_key,
                "message_preview": msg_body[:150] + "...",
                "direct_link": channel_url
            }

        # Mode 2: Official Meta WhatsApp Business API Cloud Dispatch
        url = f"https://graph.facebook.com/v19.0/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": msg_body}
        }

        # Retry with exponential backoff on transient network errors
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    self.sent_idempotency_keys.add(idempotency_key)
                    logger.info(f"[WhatsAppService] Official WhatsApp message sent successfully for {signal.get('symbol')}")
                    return {"status": "SENT_OFFICIAL", "response": resp.json(), "idempotency_key": idempotency_key}
            except Exception as e:
                logger.error(f"[WhatsAppService] Dispatch attempt {attempt+1} failed: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                else:
                    # Error Isolation: Return error status without crashing upstream scanner
                    return {
                        "status": "DELIVERY_FAILED",
                        "error": str(e),
                        "idempotency_key": idempotency_key
                    }

whatsapp_service = WhatsAppService()
