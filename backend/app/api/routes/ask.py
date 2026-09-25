"""Ask Questions About the Document (design doc section 2.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.rag import answer_question
from app.api.deps import get_owned_document
from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.db import get_db
from app.models import Citation, Conversation, Document, Message
from app.schemas import AskRequest, AskResponse, CitationOut

router = APIRouter(prefix="/api/documents/{document_id}", tags=["ask"])


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(rate_limiter("ask"))])
async def ask(
    payload: AskRequest,
    doc: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
) -> AskResponse:
    if doc.status != "ready":
        raise HTTPException(status_code=409, detail=f"Document is not ready (status: {doc.status}).")

    if payload.conversation_id:
        convo = db.get(Conversation, payload.conversation_id)
        if not convo or convo.document_id != doc.id:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        convo = Conversation(user_id=doc.user_id, document_id=doc.id)
        db.add(convo)
        db.flush()

    db.add(Message(conversation_id=convo.id, role="user", content=payload.question))

    result = await answer_question(db, doc.id, payload.question)

    assistant_msg = Message(
        conversation_id=convo.id, role="assistant", content=result.answer, state=result.confidence
    )
    db.add(assistant_msg)
    db.flush()
    for c in result.citations:
        db.add(
            Citation(
                message_id=assistant_msg.id,
                document_id=c["document_id"],
                page_number=c["page"],
                clause=c.get("clause"),
                quoted_text=c["quoted_text"],
            )
        )
    db.commit()

    return AskResponse(
        conversation_id=convo.id,
        message_id=assistant_msg.id,
        answer=result.answer,
        confidence=result.confidence,
        citations=[
            CitationOut(document_id=c["document_id"], page=c["page"], clause=c.get("clause"), quoted_text=c["quoted_text"])
            for c in result.citations
        ],
        disclaimer=get_settings().disclaimer,
    )


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    doc: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
) -> dict:
    convo = db.get(Conversation, conversation_id)
    if not convo or convo.document_id != doc.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {
        "id": convo.id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "state": m.state,
                "citations": [
                    {"page": c.page_number, "clause": c.clause, "quoted_text": c.quoted_text}
                    for c in m.citations
                ],
            }
            for m in convo.messages
        ],
    }
