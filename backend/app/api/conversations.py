from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.application.conversation.conversation_input import (
    CreateConversationInput,
    EndConversationInput,
    GetConversationInput,
    ListConversationsInput,
    SendMessageInput,
    UpdateSettingsInput,
)
from app.application.media.media_command import materialize_conversation_message_audio
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.config import get_settings
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
from app.services.ai.openai_provider import AIProviderError, get_stt_provider
from app.services.conversation.sse import encode_sse_error, stream_conversation_sse
from app.services.storage.responses import storage_stream_response

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _conversation_app(container: AppContainer = Depends(get_container)):
    return container.conversation


@router.post("", response_model=ConversationDetail)
async def create_conversation(
    body: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    try:
        detail = await app.create_session.execute(
            CreateConversationInput(
                user_id=user.id,
                scenario_id=body.scenario_id,
                level=body.level,
                theme=body.theme,
                word_count=body.word_count,
                show_chinese_hint=body.show_chinese_hint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConversationDetail(**asdict(detail))


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    app=Depends(_conversation_app),
):
    skip = (page - 1) * page_size
    result = app.list_sessions.execute(
        ListConversationsInput(user_id=user.id, skip=skip, limit=page_size)
    )
    return ConversationListResponse(
        items=[ConversationBrief(**asdict(item)) for item in result.items],
        total=result.total,
    )


@router.get("/{session_id}", response_model=ConversationDetail)
def get_conversation(
    session_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    detail = app.get_session.execute(GetConversationInput(session_id=session_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(**asdict(detail))


@router.patch("/{session_id}/settings", response_model=ConversationDetail)
def update_conversation_settings(
    session_id: int,
    body: ConversationSettingsRequest,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    try:
        detail = app.update_settings.execute(
            UpdateSettingsInput(
                session_id=session_id,
                user_id=user.id,
                show_chinese_hint=body.show_chinese_hint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConversationDetail(**asdict(detail))


@router.get("/{session_id}/messages", response_model=list[ConversationMessageResponse])
def list_messages(
    session_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    messages = app.list_messages.execute(GetConversationInput(session_id=session_id, user_id=user.id))
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [ConversationMessageResponse(**asdict(m)) for m in messages]


@router.post("/{session_id}/messages", response_model=ConversationMessageResponse)
async def send_message(
    session_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    try:
        message = await app.send_message.execute(
            SendMessageInput(
                session_id=session_id,
                user_id=user.id,
                content=body.content,
                show_chinese_hint=body.show_chinese_hint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ConversationMessageResponse(**asdict(message))


@router.post("/{session_id}/messages/stream")
async def stream_message(
    session_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    # Validate ownership before streaming
    detail = app.get_session.execute(GetConversationInput(session_id=session_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_generator():
        try:
            async for chunk in stream_conversation_sse(
                app.send_message.stream(
                    SendMessageInput(
                        session_id=session_id,
                        user_id=user.id,
                        content=body.content,
                        show_chinese_hint=body.show_chinese_hint,
                    ),
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
    app=Depends(_conversation_app),
):
    try:
        result = await app.end_session.execute(
            EndConversationInput(session_id=session_id, user_id=user.id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConversationSummaryResponse(**asdict(result))


@router.get("/{session_id}/messages/{message_id}/audio")
async def get_message_audio(
    session_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    detail = app.get_session.execute(GetConversationInput(session_id=session_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = next((m for m in detail.messages if m.id == message_id), None)
    if not message or message.role != "assistant":
        raise HTTPException(status_code=404, detail="Assistant message not found")

    settings = get_settings()
    try:
        audio_key = await materialize_conversation_message_audio(
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
    show_chinese_hint: bool | None = Form(None),
    user: User = Depends(get_current_user),
    app=Depends(_conversation_app),
):
    settings = get_settings()
    stt = get_stt_provider(settings)
    if not stt:
        raise HTTPException(status_code=503, detail="STT is not configured")

    detail = app.get_session.execute(GetConversationInput(session_id=session_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    hint = (
        show_chinese_hint
        if show_chinese_hint is not None
        else bool(detail.scene_brief.get("show_chinese_hint", True))
    )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio upload")

    try:
        transcript_raw = await stt.speech_to_text(audio_bytes, audio.filename or "recording.webm")
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=f"语音转写失败: {exc}") from exc

    transcript = (transcript_raw or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    try:
        assistant = await app.send_message.execute(
            SendMessageInput(
                session_id=session_id,
                user_id=user.id,
                content=transcript,
                show_chinese_hint=hint,
            )
        )
        detail = app.get_session.execute(GetConversationInput(session_id=session_id, user_id=user.id))
        if not detail:
            raise HTTPException(status_code=404, detail="Conversation not found")
        user_messages = [m for m in detail.messages if m.role == "user"]
        user_msg = user_messages[-1] if user_messages else None
        await materialize_conversation_message_audio(session_id, assistant.id, assistant.content, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    used_words = (user_msg.meta or {}).get("used_words", []) if user_msg else []

    return VoiceTurnResponse(
        user_message_id=user_msg.id if user_msg else 0,
        assistant_message_id=assistant.id,
        transcript=transcript,
        content=assistant.content,
        audio_url=f"/conversations/{session_id}/messages/{assistant.id}/audio",
        used_words=used_words,
    )
