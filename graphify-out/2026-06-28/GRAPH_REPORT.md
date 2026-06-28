# Graph Report - .  (2026-06-28)

## Corpus Check
- Corpus is ~4,043 words - fits in a single context window. You may not need a graph.

## Summary
- 144 nodes · 351 edges · 13 communities
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Payment & Notifications|Payment & Notifications]]
- [[_COMMUNITY_Database & Models|Database & Models]]
- [[_COMMUNITY_Client Management|Client Management]]
- [[_COMMUNITY_App Core & Config|App Core & Config]]
- [[_COMMUNITY_Content Planning|Content Planning]]
- [[_COMMUNITY_VK & AI Services|VK & AI Services]]
- [[_COMMUNITY_Telegram Bot UI|Telegram Bot UI]]

## God Nodes (most connected - your core abstractions)
1. `Client` - 21 edges
2. `Base` - 20 edges
3. `Message` - 16 edges
4. `Invoice` - 11 edges
5. `get_client_by_id()` - 10 edges
6. `Conversation` - 9 edges
7. `generate_reply()` - 9 edges
8. `Meeting` - 8 edges
9. `create_invoice()` - 8 edges
10. `content_actions_kb()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Client` --uses--> `Base`  [INFERRED]
  app/models/client.py → app/database.py
- `Conversation` --uses--> `Base`  [INFERRED]
  app/models/conversation.py → app/database.py
- `Message` --uses--> `Base`  [INFERRED]
  app/models/conversation.py → app/database.py
- `Invoice` --uses--> `Base`  [INFERRED]
  app/models/invoice.py → app/database.py
- `InvoiceStatus` --uses--> `Base`  [INFERRED]
  app/models/invoice.py → app/database.py

## Import Cycles
- None detected.

## Communities (13 total, 0 thin omitted)

### Community 0 - "Payment & Notifications"
Cohesion: 0.20
Nodes (21): CallbackQuery, FSMContext, AsyncSession, UUID, Decimal, invoice_create_start(), InvoiceStates, menu_invoices() (+13 more)

### Community 1 - "Database & Models"
Cohesion: 0.17
Nodes (15): run_async_migrations(), run_migrations_online(), Base, get_session(), AsyncSession, DeclarativeBase, MeetingStates, ClientStatus (+7 more)

### Community 2 - "Client Management"
Cohesion: 0.18
Nodes (18): CallbackQuery, AsyncSession, UUID, client_actions_kb(), client_list_kb(), Fernet, client_info(), cmd_clients() (+10 more)

### Community 3 - "App Core & Config"
Cohesion: 0.17
Nodes (12): yokassa_webhook(), Request, Settings, lifespan(), BaseSettings, start_bot(), stop_bot(), FastAPI (+4 more)

### Community 4 - "Content Planning"
Cohesion: 0.20
Nodes (16): CallbackQuery, FSMContext, content_actions_kb(), post_approve_kb(), cmd_plan(), content_drafts(), content_generate(), content_today() (+8 more)

### Community 5 - "VK & AI Services"
Cohesion: 0.23
Nodes (13): vk_callback(), Request, AsyncSession, Conversation, _build_message_history(), _classify_intent(), generate_commercial_proposal(), generate_reply() (+5 more)

### Community 6 - "Telegram Bot UI"
Cohesion: 0.21
Nodes (13): CallbackQuery, FSMContext, main_menu_kb(), cmd_payments(), cmd_meetings(), meeting_create_start(), menu_meetings(), process_datetime() (+5 more)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Client` connect `Payment & Notifications` to `Database & Models`, `Client Management`, `VK & AI Services`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `Message` connect `Telegram Bot UI` to `Payment & Notifications`, `Database & Models`, `Client Management`, `Content Planning`, `VK & AI Services`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `Base` connect `Database & Models` to `Payment & Notifications`, `VK & AI Services`, `Telegram Bot UI`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Base` (e.g. with `Client` and `ClientStatus`) actually correct?**
  _`Base` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Invoice` (e.g. with `InvoiceStates` and `Base`) actually correct?**
  _`Invoice` has 2 INFERRED edges - model-reasoned connections that need verification._