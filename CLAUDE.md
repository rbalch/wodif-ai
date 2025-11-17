# Wodify Auto-Signup Project

## Project Overview
Automated CrossFit class booking system for Wodify gym scheduling platform. Uses Playwright for browser automation, Ollama/qwen3:8b for intelligent class selection, and Pushover for notifications. Production-ready with proper error handling, logging, and smart notifications.

## Architecture

### Production Application (`/app`)
Clean, modular architecture with services, utilities, and proper separation of concerns:

```
/app
├── main.py                    # Entry point - orchestrates workflow
├── config.py                  # Environment configuration
├── models.py                  # Data classes (ClassInfo, LLMResponse)
├── services/
│   ├── browser.py            # Playwright automation
│   ├── llm.py                # Ollama integration
│   └── notification.py       # Pushover alerts
├── utils/
│   ├── logger.py             # Logging setup
│   └── date.py               # Date utilities
└── prompts/
    └── system_prompt.txt     # LLM preferences
```

### Components

1. **Browser Service** (`app/services/browser.py`)
   - Context manager for automatic cleanup
   - Login with retry logic (handles intermittent login link issues)
   - Calendar navigation and date selection
   - Class extraction from DOM
   - Booking with confirmation

2. **LLM Service** (`app/services/llm.py`)
   - Ollama client with qwen3:8b model
   - Structured JSON output
   - Returns: selected_index, reasoning, notify_user flag
   - Temperature=0 for deterministic results

3. **Notification Service** (`app/services/notification.py`)
   - Pushover integration ($5 one-time app)
   - Smart notifications (only when unusual)
   - Error notifications with details
   - Graceful degradation if Pushover not configured

4. **Main Orchestrator** (`app/main.py`)
   - 7-step workflow with logging
   - Proper error handling with notifications
   - Exit codes (0=success, 1=failure)
   - Configuration validation

### Docker Setup

**Two Services:**
- `dev`: Playwright container, runs Python app, exits after completion
- `ollama`: LLM server, stays running for fast subsequent runs

**Key Behavior:**
- `docker-compose run --rm dev python /app/main.py` runs the booking script
- `--rm` flag removes dev container after exit
- Ollama service stays running (intentional - faster, model in memory)
- Uses ~4-8GB RAM when running

**Volumes:**
- `ollama-models`: Persistent model storage (external)
- `./app:/app`: Production app code
- `./:/workspace`: Full workspace for development

**Timezone:**
- Container set to `America/New_York` (US Eastern)
- Ensures "tomorrow" calculation is correct
- Matches host cron schedule

## Configuration

### Environment Variables (.env)
```bash
# Wodify credentials (required)
EMAIL=ryan@balch.io
PASSWORD=your_password

# Pushover notifications (optional)
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token

# Optional overrides
DAYS_AHEAD=1              # Days to book ahead (default: 1)
HEADLESS=true             # Browser mode (default: true)
OLLAMA_MODEL=qwen3:8b     # LLM model (default: qwen3:8b)
OLLAMA_HOST=http://ollama:11434  # Set in docker-compose
```

### User Preferences (`app/prompts/system_prompt.txt`)
- **Target time**: 7:00 AM - 8:00 AM
- **Class type**: CrossFit (avoid OPEN GYM)
- **Fallback logic**: Closest time if no exact match
- **Notification rules**: Only alert on unusual selections

## Running the Application

### Quick Commands
```bash
make run           # Test run booking script
make build         # Rebuild containers
make shell         # Open dev container shell
make logs          # View Ollama logs
make start-ollama  # Start Ollama service
make stop-ollama   # Stop Ollama (frees memory)
```

### Production Cron Job
Runs 7pm Sunday-Thursday to book tomorrow's class:
```cron
0 19 * * 0-4 cd /home/ryan/code/wodify-signup && docker-compose run --rm dev python /app/main.py >> /var/log/wodify.log 2>&1
```

## LLM Setup

### Model: qwen3:8b
- **Why**: Best structured JSON output, good reasoning, runs on CPU
- **Inference time**: ~2-5 seconds on Xeon CPU
- **Installation**: Auto-pulled on first Ollama startup
- **CPU-only**: Works great for daily cron job (no GPU needed)

### API Usage Pattern
```python
import ollama
client = ollama.Client(host="http://ollama:11434")
response = client.chat(
    model="qwen3:8b",
    messages=[system_prompt, user_message],
    format='json',         # Structured output
    options={'temperature': 0}  # Deterministic
)
```

### Ollama Service Management
- **Stays running** after script completes (by design)
- **Auto-starts** if stopped when dev container runs
- **Manual control**: `make stop-ollama`, `make start-ollama`
- **Memory usage**: ~4-8GB RAM
- **Why keep running**: 30s+ faster, model stays in memory

## Wodify DOM Structure

### Class List Items
Each class is a `.list-item[data-list-item]` div:
- **Time range**: `.list-item-content-left` → split on newline, first element
- **Class name**: `.font-size-m span`
- **Coach**: `a[href='#']`
- **Button**: `button` with unique ID (e.g., `button_reservationOpen`)

### Button States
- `button_reservationOpen` - Available to book
- `button_classNoLimit` - Open gym (unlimited spots)
- `button_reservationNotOpenYet` - Future, not bookable yet
- `MANAGE` text - Already booked
- `None` - Past class or unavailable

## Production Workflow

### 7-Step Process (app/main.py)
1. **Validate config** - Check credentials, system prompt exists
2. **Calculate target date** - Tomorrow (or DAYS_AHEAD) in Eastern time
3. **Login to Wodify** - Retry with page refresh if needed
4. **Navigate to calendar** - Click "Class Calendar" menu
5. **Select date** - Click tomorrow's date button
6. **Extract classes** - Parse DOM into ClassInfo objects
7. **LLM selection** - Get best class + notify_user flag
8. **Book class** - Click button + confirm
9. **Handle notifications** - Send Pushover if unusual or error

### Smart Notification System

**`notify_user: false`** (Silent booking):
- Standard "CrossFit: 7:00 AM" class
- Regular 6am, 7am, or 8am slot
- Business as usual

**`notify_user: true`** (Alert sent):
- OPEN GYM selected (fallback)
- Named WOD (CHAD, MURPH) - unusual
- Wrong time (>2 hours off)
- Long time range (6am-7pm)
- Any compromise

**Always notify:**
- Booking errors
- Login failures
- No classes found

## Development Scripts (`/scripts`)

Test scripts used during development:
- `test2.py` - Playwright automation testing (interactive)
- `test_llm_selection.py` - LLM selection with dummy data
- `ollama_chat_test.py` - Interactive Ollama chat
- `test_pushover.py` - Notification testing
- `playwright-recording.py` - Original Playwright recording (reference)

**Note:** Production app in `/app` supersedes these scripts.

## Key Implementation Details

### Login Retry Logic
Login link sometimes doesn't appear on first load:
```python
def attempt_login() -> bool:
    # Try text selector
    # Try role selector
    return success

# Main flow
if not attempt_login():
    page.reload()
    if not attempt_login():
        raise Exception("Failed after 2 attempts")
```

### Wait Strategies
- **Calendar load**: `wait_for_timeout(5000)` works best
- **networkidle**: Unreliable alone (SPA keeps making requests)
- **Date selection**: 3 second timeout after click

### Date Calculation
- Uses Python datetime with timedelta
- Formats as "M/D" for Wodify (no leading zeros)
- Timezone-aware (container in US Eastern)

### Context Managers
Browser service uses context manager for automatic cleanup:
```python
with BrowserService(logger) as browser:
    # Do work
    # Automatically closes on exit or exception
```

## Data Models

### ClassInfo
```python
@dataclass
class ClassInfo:
    index: int
    time_range: str          # "7:00 AM - 8:00 AM"
    class_name: str          # "CrossFit: 7:00 AM"
    coach: str               # "Devin Leishman"
    button_id: Optional[str] # "b4-b5-l2-593_12-button_reservationOpen"
    button_text: str         # "BOOK"
```

### LLMResponse
```python
@dataclass
class LLMResponse:
    selected_index: int      # Index in classes list
    reasoning: str           # Why this class was chosen
    notify_user: bool        # Send alert?
```

## Logging

Structured logging with timestamps:
```
[2025-11-17 19:00:00] [INFO] Wodify Auto-Signup Starting
[2025-11-17 19:00:01] [INFO] Target date: Monday, November 18 (11/18)
[2025-11-17 19:00:02] [INFO] Step 1: Logging in to Wodify...
```

Logs to stdout (captured by Docker/cron).

## Error Handling

- Try/catch around entire workflow
- Detailed error messages
- Pushover notification on failure
- Exit code 1 for cron monitoring
- Screenshots saved on errors (if enabled)

## Troubleshooting

### "No classes found"
- Calendar didn't load properly
- Check with `HEADLESS=false` to see browser
- Verify date selection worked

### "Failed to login"
- Check EMAIL/PASSWORD in .env
- Wodify may have changed login flow
- Check screenshots if saved

### "LLM returned invalid JSON"
- Ollama not ready (check `make logs`)
- Model still downloading
- Restart Ollama: `make restart-ollama`

### Timezone issues
- Container set to US Eastern
- Rebuild if Dockerfile changed: `make build`
- Check with: `docker exec wodify-signup-dev date`

### Ollama won't stop
- By design (keeps model ready)
- Manual stop: `make stop-ollama`
- Frees ~4-8GB RAM

## Security Notes

- `.env` file gitignored
- Screenshots may contain personal info (gitignored)
- Pushover tokens are sensitive
- Consider app-specific password for Wodify
- Docker socket mounted (required for docker-compose)

## Future Enhancements

- ✅ ~~Integrate components into production app~~
- ✅ ~~Add cron job configuration~~
- ✅ ~~Smart notification system~~
- [ ] Handle "MANAGE" button state (skip already booked)
- [ ] Retry logic for transient failures
- [ ] Support multiple time preferences
- [ ] Webhook integration for calendar changes
- [ ] Email fallback if Pushover fails
- [ ] Metrics/analytics (booking success rate)

## File Organization

```
.
├── app/                      # Production application
│   ├── main.py              # Entry point
│   ├── services/            # Browser, LLM, Notification
│   ├── utils/               # Logger, date helpers
│   └── prompts/             # System prompt
├── scripts/                  # Development/testing
├── screenshots/             # Debug screenshots (gitignored)
├── docker-compose.yml       # Service definitions
├── Dockerfile               # Dev container (US Eastern TZ)
├── Makefile                 # Convenience commands
├── README.md               # User documentation
├── CLAUDE.md               # Technical documentation (this file)
└── .env                     # Credentials (gitignored)
```

## Performance

- **First run**: ~30-40s (Ollama startup + model load)
- **Subsequent runs**: ~10-15s (Ollama already running)
- **Browser automation**: ~8-12s
- **LLM inference**: ~2-5s on Xeon CPU
- **Total cron job**: ~15-20s (Ollama warm)

## Dependencies

**Python packages:**
- `playwright` - Browser automation
- `ollama` - LLM client
- `requests` - Pushover API

**System:**
- Docker + Docker Compose
- Chromium (via Playwright)
- tzdata (timezone support)

All dependencies installed in Dockerfile.