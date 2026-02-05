from pydantic import BaseModel, Field
from typing import List, Optional, Any

# 1. Nested Message Structure (Matching GUVI Request Format)
class MessageData(BaseModel):
    sender: str = Field(..., description="scammer or user")
    text: str = Field(..., description="The actual message content")
    timestamp: Optional[Any] = None

# 2. Metadata Structure
class MetaData(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

# 3. Main Scam Detection Request (Input)
class ScamDetectionRequest(BaseModel):
    sessionId: str = Field(..., description="Unique session ID")
    message: MessageData = Field(..., description="Nested message object from GUVI")
    conversationHistory: List[MessageData] = []
    metadata: Optional[MetaData] = None

# 4. Intelligence Data (Matching Strict GUVI Keys)
class IntelligenceData(BaseModel):
    upilds: List[str] = []
    bankAccounts: List[str] = []
    phoneNumbers: List[str] = []
    phishingLinks: List[str] = []
    suspiciousKeywords: List[str] = ["urgent", "verify", "block"]

# 5. Scam Detection Response (Output)
class ScamDetectionResponse(BaseModel):
    status: str = "success"
    reply: str = Field(..., description="AI generated response for the scammer")
    scamDetected: bool = True
    extractedIntelligence: Optional[IntelligenceData] = None

# 6. Final Callback Payload (Mandatory for Scoring)
class CallbackPayload(BaseModel):
    sessionId: str
    scamDetected: bool = True
    totalMessagesExchanged: int
    extractedIntelligence: IntelligenceData
    agentNotes: str = "Scammer used urgency tactics and requested verification."
