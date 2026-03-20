  Chat Interface Design

  1. Placement: Always-Visible Drawer

  Not a panel — a persistent bottom drawer that stays visible alongside Pipeline, Editor, etc. Like a terminal in VS Code. You need to see agents working AND chat
  simultaneously.

  ┌──────────┬──────────────────────────────────────────┐
  │ Sidebar  │  Active Panel (Pipeline/Editor/etc.)      │
  │          │                                            │
  │          │                                            │
  │          ├────────────────────────────────────────────┤
  │          │  ▾ Chat                          [─] [□]   │
  │          │  ┌─────────────────────────────────────┐  │
  │          │  │ 🤖 Architect: I'll design the API...│  │
  │          │  │ 🤖 Planner: Breaking into 4 tasks.. │  │
  │          │  │ ⚡ System: S3 Architecture started   │  │
  │          │  │ ❓ Clarifier: Which DB do you prefer?│  │
  │          │  │    [PostgreSQL] [MongoDB] [Let AI..] │  │
  │          │  ├─────────────────────────────────────┤  │
  │          │  │ Type a message...            [Send]  │  │
  │          │  └─────────────────────────────────────┘  │
  └──────────┴────────────────────────────────────────────┘

  2. Message Types

  ┌───────────────┬───────────────────────────────────────┬────────────────────────────┐
  │     Type      │                Visual                 │          Purpose           │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ user          │ Right-aligned blue bubble             │ User's text input          │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ agent         │ Left-aligned with agent avatar + name │ Agent responses            │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ system        │ Centered gray text                    │ Pipeline stage transitions │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ clarification │ Left with action buttons              │ Agent asking a question    │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ approval      │ Left with Approve/Reject buttons      │ Gate approval requests     │
  ├───────────────┼───────────────────────────────────────┼────────────────────────────┤
  │ error         │ Red border                            │ Failures                   │
  └───────────────┴───────────────────────────────────────┴────────────────────────────┘

  3. Backend: Socket.IO Events

  Client → Server:
    chat.send    { project_id, content, reply_to? }
    chat.approve { project_id, gate_id, approved }

  Server → Client (via project room):
    chat.message   { id, type, content, agent?, timestamp }
    chat.typing    { agent }
    chat.approval  { gate_id, stage, description }

  No REST endpoint for chat — it's all real-time over Socket.IO. Messages stored in the project's event log via the existing NATS bus.

  4. Frontend Components

  ┌────────────────────────────────────────┬───────────────────────────────────────────────┐
  │                  File                  │                    Purpose                    │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ stores/chat-store.ts                   │ Messages array, drawer open/collapsed state   │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ components/chat/chat-drawer.tsx        │ Resizable bottom drawer container             │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ components/chat/message-list.tsx       │ Scrolling message feed with auto-scroll       │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ components/chat/message-bubble.tsx     │ Renders each message type differently         │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ components/chat/chat-input.tsx         │ Text input + send button + keyboard shortcuts │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ components/chat/clarification-card.tsx │ Inline buttons for agent questions            │
  ├────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ hooks/use-chat.ts                      │ Socket.IO event bindings for chat             │
  └────────────────────────────────────────┴───────────────────────────────────────────────┘

  5. Data Flow

  User types → chat.send event → Socket.IO server
    → InputExtractor.extract() → requirements
    → Pipeline orchestrator routes to agents
    → Agents emit events → NATS → Bridge → chat.message → UI

  6. Modified Files

  - websocket/manager.py — add chat.send and chat.approve handlers
  - app.tsx — add ChatDrawer below ActivePanel
  - main-layout.tsx — adjust flex layout for drawer