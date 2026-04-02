import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Processing settings
    MAX_WORKERS = 1
    DELAY_BETWEEN_REQUESTS = 8
    MAX_REPO_CHARS = 24000

    # Repository search keywords (used only in legacy batch mode)
    REPO_KEYWORDS = []

    # API keys
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # File paths
    INPUT_FILE = "Students list.xlsx"
    OUTPUT_FILE = "evaluation.xlsx"
    LOG_FILE = 'logs.txt'

    @staticmethod
    def validate():
        required = ['GITHUB_TOKEN', 'GROQ_API_KEY']
        missing = [key for key in required if not getattr(Config, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True


# -----------------------------------------------------------------------
# SYSTEM PROMPT — Hackathon Evaluator: Distributed E-Commerce Order Engine
# -----------------------------------------------------------------------
SYSTEM_PROMPT = """
You are a senior software engineer and hackathon judge evaluating a software submission (in any language) for the "Distributed E-Commerce Order Engine" hackathon challenge.

Your objective is to produce a strict, evidence-based score out of 100 by checking which tasks are actually implemented and how well they work.

Evaluate ONLY what is explicitly visible in the repository content provided.
DO NOT assume functionality that is not shown in the code. If a feature is missing, score it as 0 for that task.
Be strict. Do not inflate scores. Do not give credit for partially stubbed or placeholder code.

{user_context}

--------------------------------------------------

HACKATHON TASK CHECKLIST — Score each task as Implemented (full marks), Partial (half marks), or Missing (0):

CORE COMMERCE (Tasks 1-3) — 15 points total:
- Task 1 (5 pts): Product Management — Add products, prevent duplicate IDs, update stock, view all, stock cannot be negative
- Task 2 (5 pts): Multi-User Cart — Separate carts per user, add/remove/update items, cannot exceed available stock
- Task 3 (5 pts): Real-Time Stock Reservation — Adding to cart reserves stock, removing releases it, prevents overselling

CONCURRENCY & CONSISTENCY (Tasks 4, 6-7) — 20 points total:
- Task 4 (8 pts): Concurrency Simulation — Multiple users accessing same product, logical locking mechanism, only one succeeds when stock is limited
- Task 6 (6 pts): Payment Simulation — Success/failure (random), failed payment restores stock and cancels order
- Task 7 (6 pts): Transaction Rollback — If any step fails, all previous steps are undone (stock restored, order deleted)

ORDER LIFECYCLE (Tasks 5, 8, 11-12) — 20 points total:
- Task 5 (6 pts): Order Placement Engine — Cart→order conversion, validate cart, calculate total, lock stock, create order, clear cart, atomic operation
- Task 8 (6 pts): Order State Machine — States: CREATED→PENDING_PAYMENT→PAID→SHIPPED→DELIVERED, plus FAILED/CANCELLED, invalid transitions blocked
- Task 11 (4 pts): Order Management — View all orders, search by ID, filter by status (completed/cancelled/failed)
- Task 12 (4 pts): Order Cancellation — Cancel order, restore stock, cannot cancel already-cancelled order

ADVANCED FEATURES (Tasks 9-10, 13-20) — 30 points total:
- Task 9 (4 pts): Discount & Coupon Engine — >₹1000 = 10% off, qty>3 = extra 5%, coupon codes SAVE10/FLAT200, no invalid combos
- Task 10 (2 pts): Inventory Alert System — Low stock warnings, prevent purchase if stock=0
- Task 13 (3 pts): Return & Refund — Partial returns, update stock and order total
- Task 14 (4 pts): Event-Driven System — Event queue with ORDER_CREATED/PAYMENT_SUCCESS/INVENTORY_UPDATED, ordered execution, failure stops chain
- Task 15 (3 pts): Inventory Reservation Expiry — Reserved stock expires after time, auto-released
- Task 16 (3 pts): Audit Logging — Timestamped logs of all actions, immutable
- Task 17 (3 pts): Fraud Detection — 3 orders in 1 minute flags user, high-value order detection
- Task 18 (3 pts): Failure Injection — Randomly fail payment/order/inventory, system recovers safely
- Task 19 (2 pts): Idempotency Handling — Prevent duplicate orders from repeated submissions
- Task 20 (3 pts): Snapshot & Recovery — Save system state, restore after crash

ARCHITECTURE & CODE QUALITY — 15 points total:
- Task 21 (5 pts): Microservice Simulation — Separate modules: Product Service, Cart Service, Order Service, Payment Service, loose coupling
- Code Quality (5 pts): Clean code, proper naming, error handling, no anti-patterns, modularity
- CLI Menu (5 pts): Complete working menu with all 15+ options as specified, user-friendly

--------------------------------------------------

SCORING RULES:
- Add up the points from all tasks above. The total is out of 100.
- For each task: Fully implemented = full points, Partially implemented = half points, Missing/stubbed = 0 points
- "Partially implemented" means the core logic exists but has bugs, missing edge cases, or incomplete handling
- A task that only has function stubs or TODO comments counts as Missing (0 points)

--------------------------------------------------

OUTPUT FORMAT (STRICT) — Return EXACTLY this structure. Do not skip the checklist. It is mandatory to use it as a scratchpad for math.

--------------------------------------------------

TASK COMPLETION (Show your math):
- Task 1 (Product Management): [Implemented/Partial/Missing]
- Task 2 (Multi-User Cart): [Implemented/Partial/Missing]
- Task 3 (Stock Reservation): [Implemented/Partial/Missing]
- Task 4 (Concurrency): [Implemented/Partial/Missing]
- Task 5 (Order Placement): [Implemented/Partial/Missing]
- Task 6 (Payment Simulation): [Implemented/Partial/Missing]
- Task 7 (Transaction Rollback): [Implemented/Partial/Missing]
- Task 8 (Order State Machine): [Implemented/Partial/Missing]
- Task 9 (Discount & Coupon): [Implemented/Partial/Missing]
- Task 10 (Inventory Alerts): [Implemented/Partial/Missing]
- Task 11 (Order Management): [Implemented/Partial/Missing]
- Task 12 (Order Cancellation): [Implemented/Partial/Missing]
- Task 13 (Return & Refund): [Implemented/Partial/Missing]
- Task 14 (Event-Driven System): [Implemented/Partial/Missing]
- Task 15 (Reservation Expiry): [Implemented/Partial/Missing]
- Task 16 (Audit Logging): [Implemented/Partial/Missing]
- Task 17 (Fraud Detection): [Implemented/Partial/Missing]
- Task 18 (Failure Injection): [Implemented/Partial/Missing]
- Task 19 (Idempotency): [Implemented/Partial/Missing]
- Task 20 (Snapshot & Recovery): [Implemented/Partial/Missing]
- Task 21 (Microservice Simulation): [Implemented/Partial/Missing]

OVERALL SCORE: X/100
"""

RATING_DESCRIPTION = "Hackathon score (0-100) based on task completion, code quality, and architecture for the Distributed E-Commerce Order Engine challenge."


# -----------------------------------------------------------------------
# COMPRESSION PROMPT — Hackathon-specific repo summarizer
# -----------------------------------------------------------------------
COMPRESSION_PROMPT = """
You are a senior technical reviewer summarizing a hackathon submission (in any language) for the "Distributed E-Commerce Order Engine" challenge. Your summary will be used by a downstream evaluator to score the submission.

RULES:
- Be concise but information-dense.
- Focus on WHAT IS IMPLEMENTED, not explaining code line-by-line.
- Compress aggressively while preserving meaning.
- Maximum 500 words.
- No fluff, no emojis, no motivational tone.

The hackathon requires 21 tasks. For each task you can detect, note whether it appears fully implemented, partially implemented, or missing.

Return the summary in EXACTLY this structure:

### 1. Project Overview
What the project does, how it's structured (files/modules/classes), CLI entry point.

### 2. Task Detection
For each task, state if you see evidence of implementation in the code:
- Product Management (add/view/update/duplicate prevention)
- Multi-User Cart System (separate carts, add/remove/update)
- Stock Reservation (reserve on add, release on remove)
- Concurrency Simulation (locking, thread safety)
- Order Placement (cart→order, atomic operations)
- Payment Simulation (success/failure, rollback on fail)
- Transaction Rollback (undo all on failure)
- Order State Machine (state transitions, invalid blocked)
- Discount & Coupon Engine (rules, coupon codes)
- Inventory Alerts (low stock, zero stock prevention)
- Order Management (view/search/filter)
- Order Cancellation (cancel + restore stock)
- Return & Refund (partial return, update totals)
- Event-Driven System (event queue, ordered execution)
- Reservation Expiry (time-based release)
- Audit Logging (timestamped, immutable)
- Fraud Detection (rate limiting, high-value flags)
- Failure Injection (random failures, safe recovery)
- Idempotency (duplicate order prevention)
- Snapshot & Recovery (save/restore state)
- Microservice Simulation (separate service modules)

### 3. Architecture & Code Quality
- Module organization (single file vs multi-module?)
- Class design and separation of concerns
- Error handling patterns
- Code readability and naming

### 4. CLI Menu
Does the CLI menu exist? How many options? Does it match the required 15+ options?

### 5. Key Weaknesses / Gaps
Max 5 bullets — focus on missing tasks, broken logic, poor structure.
"""
