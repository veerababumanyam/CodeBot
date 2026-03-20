import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC
from codebot.websocket.manager import chat_send

@pytest.mark.asyncio
async def test_chat_send_with_attachments():
    # Mock Socket.IO server and session
    mock_sio = AsyncMock()
    sid = "test_sid"
    mock_sio.get_session.return_value = {
        "user_id": "user_123",
        "project_id": "project_456"
    }

    # Test data with attachments
    data = {
        "content": "Check this image",
        "attachments": [
            {
                "type": "image",
                "url": "data:image/png;base64,xxxx",
                "name": "test.png"
            }
        ]
    }

    # Mock dependencies
    with patch("codebot.websocket.manager.sio", mock_sio), \
         patch("codebot.websocket.manager.get_event_bus", return_value=AsyncMock()), \
         patch("codebot.websocket.manager.publish_event", AsyncMock()) as mock_publish:
        
        # Execute
        await chat_send(sid, data)

        # Verify Socket.IO broadcast
        mock_sio.emit.assert_called_once()
        args, kwargs = mock_sio.emit.call_args
        event, message = args
        assert event == "chat.message"
        assert message["content"] == data["content"]
        assert message["attachments"] == data["attachments"]
        assert message["type"] == "user"
        assert kwargs["room"] == "project:project_456"

        # Verify NATS event publication
        mock_publish.assert_called_once()
        args, _ = mock_publish.call_args
        envelope = args[1]
        import json
        payload = json.loads(envelope.payload.decode())
        assert payload["content"] == data["content"]
        assert payload["attachments"] == data["attachments"]
        assert payload["project_id"] == "project_456"

@pytest.mark.asyncio
async def test_chat_send_only_attachments():
    # Mock Socket.IO server and session
    mock_sio = AsyncMock()
    sid = "test_sid"
    mock_sio.get_session.return_value = {
        "user_id": "user_123",
        "project_id": "project_456"
    }

    # Data with only attachments, NO content
    data = {
        "attachments": [
            {
                "type": "file",
                "url": "data:application/pdf;base64,yyyy",
                "name": "doc.pdf"
            }
        ]
    }

    with patch("codebot.websocket.manager.sio", mock_sio), \
         patch("codebot.websocket.manager.get_event_bus", return_value=AsyncMock()), \
         patch("codebot.websocket.manager.publish_event", AsyncMock()) as mock_publish:
        
        await chat_send(sid, data)

        # Should still broadcast/publish since attachments exist
        mock_sio.emit.assert_called_once()
        mock_publish.assert_called_once()
