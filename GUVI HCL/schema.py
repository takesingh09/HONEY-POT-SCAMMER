from pydantic import BaseModel, Field
from typing import List, Optional

# Scam Detection Request (Input from User/System)
class ScamDetectionRequest(BaseModel):
    sessionId: str = Field(..., description="Unique session ID for the conversation")
    message: str = Field(..., description="Incoming message from the potential scammer")
    platform: str = Field(..., description="Source platform (WhatsApp, SMS, Email)")
    senderId: str = Field(..., description="Sender's phone number or email")

# Intelligence Data (Extracted Info)
class IntelligenceData(BaseModel):
    upi_ids: List[str] = []
    bank_accounts: List[str] = []
    phone_numbers: List[str] = []
    links: List[str] = []

# Scam Detection Response (Output to User/System)
class ScamDetectionResponse(BaseModel):
    sessionId: str
    isScam: bool
    confidenceScore: float
    reply: str
    extractedIntelligence: IntelligenceData
    status: str

# Callback Payload (Sent to GUVI)
class CallbackPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    intelligence: IntelligenceData
    conversationHistory: List[dict]
