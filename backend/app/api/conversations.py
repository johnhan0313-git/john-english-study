from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationBrief,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationSettingsRequest,
    ConversationSummaryResponse,
    EndConversationRequest,
    SendMessageRequest,
    VoiceTurnResponse,
)
from app.services.ai.factory import build_providers
from app.services.ai.openai_provider import AIProviderError, get_stt_provider
from app.services.conversation.service import ConversationService
from app.services.conversation.sse import encode_sse_error, stream_conversation_sse
from app.services.media.tts_facade import ensure_conversation_message_audio
from app.services.storage.responses import storage_stream_response
from app.utils.json_helpers import parse_json_field

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _conversation_service(db: Session) -> ConversationService:
    return ConversationService(db, providers=build_providers())


def _get_user_session(service: ConversationService, session_id: int, user_id: int):
    session = service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return session


@router.post("", response_model=ConversationDetail)
async def create_conversation(
    body: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    try:
        session = await service.create_session(
            user_id=user.id,
            scenario_id=body.scenario_id,
            level=body.level,
            theme=body.theme,
            word_count=body.word_count,
            show_chinese_hint=body.show_chinese_hint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session = service.get_session(session.id, user.id)
    return ConversationDetail(**service.session_to_detail(session))


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    skip = (page - 1) * page_size
    items, total = service.list_sessions(user.id, skip=skip, limit=page_size)
    return ConversationListResponse(
        items=[ConversationBrief(**service.session_to_brief(item)) for item in items],
        total=total,
    )


@router.get("/{session_id}", response_model=ConversationDetail)
def get_conversation(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    return ConversationDetail(**service.session_to_detail(session))


@router.patch("/{session_id}/settings", response_model=ConversationDetail)
def update_conversation_settings(
    session_id: int,
    body: ConversationSettingsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    service.update_show_chinese_hint(session, body.show_chinese_hint)
    session = service.get_session(session_id, user.id)
    return ConversationDetail(**service.session_to_detail(session))


@router.get("/{session_id}/messages", response_model=list[ConversationMessageResponse])
def list_messages(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    return [ConversationMessageResponse(**service.message_to_dict(m)) for m in sorted(session.messages, key=lambda x: x.id)]


@router.post("/{session_id}/messages", response_model=ConversationMessageResponse)
async def send_message(
    session_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    try:
        message = await service.send_message(session, body.content, show_chinese_hint=body.show_chinese_hint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ConversationMessageResponse(**service.message_to_dict(message))


@router.post("/{session_id}/messages/stream")
async def stream_message(
    session_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)

    async def event_generator():
        try:
            async for chunk in stream_conversation_sse(
                service.stream_assistant_reply(
                    session,
                    body.content,
                    show_chinese_hint=body.show_chinese_hint,
                ),
            ):
                yield chunk
        except ValueError as exc:
            yield encode_sse_error(str(exc))
        except AIProviderError as exc:
            yield encode_sse_error(str(exc))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{session_id}/end", response_model=ConversationSummaryResponse)
async def end_conversation(
    session_id: int,
    body: EndConversationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    result = await service.end_session(session)
    return ConversationSummaryResponse(**result)


@router.get("/{session_id}/messages/{message_id}/audio")
async def get_message_audio(
    session_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)

    message = next((m for m in session.messages if m.id == message_id), None)
    if not message or message.role != "assistant":
        raise HTTPException(status_code=404, detail="Assistant message not found")

    settings = get_settings()
    try:
        audio_key = await ensure_conversation_message_audio(
            session_id,
            message_id,
            message.content,
            settings,
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return storage_stream_response(
        audio_key,
        media_type="audio/mpeg",
        filename=f"conversation_{session_id}_{message_id}.mp3",
    )


@router.post("/{session_id}/turns/voice", response_model=VoiceTurnResponse)
async def voice_turn(
    session_id: int,
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    stt = get_stt_provider(settings)
    if not stt:
        raise HTTPException(status_code=503, detail="STT is not configured")

    service = _conversation_service(db)
    session = _get_user_session(service, session_id, user.id)
    show_chinese_hint = ConversationService.get_show_chinese_hint(session)

    audio_bytes = await audio.read()
    transcript = await stt.speech_to_text(audio_bytes, audio.filename or "recording.webm")
    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    assistant = await service.send_message(session, transcript.strip(), show_chinese_hint=show_chinese_hint)
    db.refresh(session)
    user_messages = [m for m in session.messages if m.role == "user"]
    user_msg = user_messages[-1] if user_messages else None
    await ensure_conversation_message_audio(session_id, assistant.id, assistant.content, settings)

    used_words = parse_json_field(user_msg.meta, {}).get("used_words", []) if user_msg else []

    return VoiceTurnResponse(
        user_message_id=user_msg.id if user_msg else 0,
        assistant_message_id=assistant.id,
        transcript=transcript.strip(),
        content=assistant.content,
        audio_url=f"/conversations/{session_id}/messages/{assistant.id}/audio",
        used_words=used_words,
    )
