# Wodify Auto-Signup Project

## Project Overview
Automated CrossFit class booking system for Wodify gym scheduling platform. Uses Playwright for browser automation, Ollama/LLM for intelligent class selection, and Pushover for notifications.

## Architecture

### Components
1. **Browser Automation** (`scripts/test2.py`)
   - Uses Playwright to login and navigate Wodify
   - Extracts class schedule data (time, name, coach, button IDs)
   - Books selected classes

2. **LLM Selection** (`scripts/test_llm_selection.py`)
   - Uses Ollama with qwen3:8b model for intelligent class selection
   - Reads preferences from `scripts/system_prompt.txt`
   - Returns JSON with selected class index, reasoning, and notify_user flag

3. **Notifications** (`scripts/test_pushover.py`)
   - Pushover integration for mobile alerts ($5 one-time app purchase)
   - Smart notifications: Only alerts when something unusual happens
   - Triggered by `notify_user` flag from LLM decision

### Docker Setup
- **Dev container**: Playwright-based container for running scripts
- **Ollama service**: Separate container for LLM inference
- **Volumes**:
  - `ollama-models`: Persistent model storage
  - `huggingface-cache`: HF cache (not currently used)

## Configuration

### Environment Variables (.env)
```bash
# Wodify credentials
EMAIL=ryan@balch.io
PASSWORD=your_password

# Pushover notifications
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token

# Ollama host (set in docker-compose)
OLLAMA_HOST=http://ollama:11434
```

### User Preferences
Located in `scripts/system_prompt.txt`:
- **Target time**: 7:00 AM - 8:00 AM
- **Class type**: CrossFit (avoid OPEN GYM)
- **Fallback logic**: Documented in prompt
- **Notification logic**: LLM sets `notify_user` flag when selection is unusual

## Key Files

### Scripts
- `scripts/test2.py` - Main Playwright automation (login, navigate, extract, book)
- `scripts/test_llm_selection.py` - Demo of LLM class selection
- `scripts/ollama_chat_test.py` - Interactive Ollama test
- `scripts/test_pushover.py` - Pushover notification test
- `scripts/system_prompt.txt` - LLM selection preferences and examples
- `scripts/playwright-recording.py` - Original Playwright recording (reference)

### Config
- `docker-compose.yml` - Dev container + Ollama service
- `Dockerfile` - Playwright-based dev environment
- `.env` - Credentials and config (gitignored)

## LLM Setup

### Model: qwen3:8b
- **Why**: Excellent at structured JSON output, good reasoning, runs on CPU
- **Inference time**: ~2-5 seconds on Xeon CPU
- **Installation**: Auto-pulled by docker-compose on startup
- **Manual pull**: `docker exec wodify-ollama ollama pull qwen3:8b`

### API Usage
```python
import ollama
client = ollama.Client(host="http://ollama:11434")
response = client.chat(
    model="qwen3:8b",
    messages=[...],
    format='json',  # Structured output
    options={'temperature': 0}  # Deterministic
)
```

## Wodify DOM Structure

### Class List Items
Each class is in a `.list-item[data-list-item]` div containing:
- **Time**: `.list-item-content-left .font-semi-bold`
- **Class name**: `.font-size-m span`
- **Coach**: `a[href='#']`
- **Button**: `button` with unique ID (e.g., `#b4-b5-l2-593_12-button_reservationOpen`)

### Button States
- `button_reservationOpen` - Available to book
- `button_classNoLimit` - Open gym (unlimited)
- `button_reservationNotOpenYet` - Future class not yet bookable
- `None` - Past class or unavailable

## Workflow

### Current Status (Testing Phase)
1. Manual: Run `scripts/test2.py` to test login and extraction
2. Manual: Run `scripts/test_llm_selection.py` to test LLM selection
3. Manual: Run `scripts/test_pushover.py` to test notifications

### Target Workflow (Production)
1. **Cron job** runs main script daily
2. **Login** to Wodify
3. **Navigate** to Class Calendar
4. **Select date** (if specified)
5. **Extract** class list
6. **LLM selection** based on preferences (returns selected_index, reasoning, notify_user)
7. **Book** selected class
8. **Notify** via Pushover if `notify_user: true` OR if booking failed

## Notes

### Login Issues
- Login link sometimes doesn't appear on first page load
- Solution: Retry with page refresh (implemented in `attempt_login()`)

### Wait Strategies
- `wait_for_timeout(5000)` works best for calendar loading
- `networkidle` alone is unreliable for this SPA

### Date Selection
- Set `DAY_TO_SELECT = "11/14"` to book specific date
- Uses regex pattern matching: `.*{date}$`

### LLM Selection Logic
- Prioritizes time match over class type
- Special workouts (CHAD, MURPH) are recognized as CrossFit WODs
- Falls back to closest available if no perfect match
- Returns JSON: `{"selected_index": N, "reasoning": "...", "notify_user": boolean}`

### Smart Notification System
The LLM includes a `notify_user` boolean in its response:

**`notify_user: false`** (Silent booking - no alert):
- Standard CrossFit class at expected time (7am, 6am, or 8am)
- Regular class like "CrossFit: 7:00 AM"
- Business as usual

**`notify_user: true`** (Send Pushover alert):
- OPEN GYM selected (fallback)
- Named WOD like CHAD, MURPH (unusual)
- No class at target time window
- Time significantly off (>2 hours)
- Long time ranges (e.g., "6:00 AM - 7:00 PM")
- Any compromised or unusual selection

This prevents notification fatigue - you only get alerts when something interesting or wrong happens.

## Future Enhancements
- [ ] Integrate all components into single production script
- [ ] Add cron job configuration
- [ ] Handle "MANAGE" button state (already booked)
- [ ] Add retry logic for booking failures
- [ ] Support multiple time preferences
- [ ] Add webhook for calendar monitoring