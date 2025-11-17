# Wodify Auto-Signup

Automated CrossFit class booking system for Wodify gym scheduling. Uses Playwright for browser automation, Ollama/qwen3:8b for intelligent class selection, and Pushover for mobile notifications.

## Features

- 🤖 **Intelligent Selection**: LLM-powered class selection based on your preferences
- 📱 **Smart Notifications**: Only alerts you when something unusual happens
- 🐳 **Docker-based**: Fully containerized setup with Ollama service
- ⏰ **Cron-ready**: Designed to run as a daily automated task
- 🔒 **Secure**: Credentials stored in `.env` file (gitignored)

## Quick Start

### 1. Clone and Setup

```bash
cd /home/ryan/code/wodify-signup
cp .env.example .env  # Create from example if exists, or create new
```

### 2. Configure Environment

Edit `.env` and add your credentials:

```bash
# Wodify credentials (required)
EMAIL=your_email@example.com
PASSWORD=your_password

# Pushover notifications (optional but recommended)
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token

# Optional settings
DAYS_AHEAD=1              # Book for tomorrow (default: 1)
HEADLESS=true             # Run browser headless (default: true)
OLLAMA_MODEL=qwen3:8b     # LLM model (default: qwen3:8b)
```

### 3. Start Services

```bash
# Build and start Ollama service
make build
docker-compose up -d ollama

# Wait for qwen3:8b model to download (first time only)
docker logs -f wodify-ollama
# Press Ctrl+C when you see "success"
```

### 4. Test Run

```bash
# Option 1: Using Makefile
make run

# Option 2: Direct docker-compose
docker-compose run --rm dev python /app/main.py

# Option 3: From inside dev container
make shell
python /app/main.py
```

## Customizing Preferences

Edit `app/prompts/system_prompt.txt` to customize:

- **Target time**: Default is 7:00 AM - 8:00 AM
- **Class type**: Prefers CrossFit classes, avoids OPEN GYM
- **Notification rules**: When to send alerts vs. silent booking

## Setting Up Cron Job

### Option 1: Using `crontab -e` (Recommended)

```bash
crontab -e
```

Add this line to run at 7pm Sunday-Thursday:

```cron
0 19 * * 0-4 cd /home/ryan/code/wodify-signup && docker-compose run --rm dev python /app/main.py >> /var/log/wodify.log 2>&1
```

### Option 2: System Cron File

Create `/etc/cron.d/wodify-signup`:

```bash
# Run at 7pm Sunday-Thursday to book tomorrow's class
0 19 * * 0-4 ryan cd /home/ryan/code/wodify-signup && docker-compose run --rm dev python /app/main.py >> /var/log/wodify.log 2>&1
```

Make it executable:
```bash
sudo chmod 0644 /etc/cron.d/wodify-signup
```

### Cron Schedule Explanation

- `0 19 * * 0-4`: Run at 19:00 (7pm)
  - `0-4` = Sunday through Thursday
  - Skips Friday (5) and Saturday (6)
- Books for "tomorrow" (DAYS_AHEAD=1)
- Perfect for Mon-Fri classes when scheduled Sun-Thu nights

### View Logs

```bash
# If using log file
tail -f /var/log/wodify.log

# Or use docker logs
docker logs -f wodify-signup-dev
```

## How It Works

1. **Starts browser** and logs into Wodify
2. **Navigates to Class Calendar** and selects tomorrow's date
3. **Extracts all classes** with times, names, coaches, and booking buttons
4. **Consults LLM** (qwen3:8b) to select best class based on preferences
5. **Books the class** by clicking the button and confirming
6. **Sends notification** via Pushover if:
   - Selection was unusual (OPEN GYM, named WOD, wrong time)
   - Booking failed
   - Never notifies for standard CrossFit bookings

## Docker Services

The app uses two Docker containers:

### `dev` Container
- Runs the Python application
- Includes Playwright and browser
- Mounts `/app` directory
- Depends on `ollama` service
- Exits when script completes (removed with `--rm` flag)

### `ollama` Container
- Runs Ollama LLM server
- Auto-downloads qwen3:8b model on first start
- **Stays running after `make run` completes** (by design)
- Persistent model storage in `ollama-models` volume
- Uses ~4-8GB RAM when running

### Why Ollama Stays Running

When you run `make run`, the `dev` container:
1. Starts (if `ollama` isn't running, it starts it first)
2. Executes the booking script
3. Exits and is removed (`--rm` flag)

The `ollama` service **stays running** because:
- ✅ **Faster subsequent runs** - No model reload (~30s saved)
- ✅ **Perfect for cron** - Ready for next day's booking
- ✅ **Keeps model in memory** - Instant LLM responses

**This is intentional and recommended behavior.**

### Managing Ollama Service

```bash
# Start Ollama
make start-ollama

# Stop Ollama (frees ~4-8GB RAM)
make stop-ollama

# Restart Ollama (if model update needed)
make restart-ollama

# Check if Ollama is running
docker ps | grep ollama

# View Ollama logs
make logs
```

**When to stop Ollama:**
- Going on vacation (won't run cron jobs)
- Need to free memory
- Weekends (if not booking then)
- Updating the model

**Note:** The next `make run` or cron job will automatically restart Ollama if it's stopped.

## Makefile Commands

```bash
make help          # Show available commands
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make shell         # Open shell in dev container
make run           # Run the booking script (test)
make logs          # View Ollama logs
make start-ollama  # Start Ollama service
make stop-ollama   # Stop Ollama service (frees memory)
make restart-ollama # Restart Ollama service
make clean         # Stop and remove containers
```

## Troubleshooting

### "No classes found"
- Check that the calendar loaded (run with `HEADLESS=false` in .env)
- Verify date format matches Wodify's display

### "Failed to login"
- Verify `EMAIL` and `PASSWORD` in `.env`
- Check if Wodify changed their login page

### "LLM returned invalid JSON"
- Check Ollama logs: `docker logs wodify-ollama`
- Ensure qwen3:8b model is fully downloaded
- Try restarting Ollama: `docker-compose restart ollama`

### "Pushover notifications not working"
- Verify credentials in `.env`
- App will still work, just won't send alerts
- Check Pushover API status

### Cron job not running
- Check cron logs: `grep CRON /var/log/syslog`
- Verify user has permission to run docker commands
- Test command manually first
- Make sure docker-compose is in PATH for cron

## Project Structure

```
.
├── app/                      # Production application
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── models.py            # Data models
│   ├── services/            # Browser, LLM, Notification services
│   ├── utils/               # Logger, date utilities
│   └── prompts/             # LLM system prompt
├── scripts/                  # Development/testing scripts
├── docker-compose.yml       # Docker service definitions
├── Dockerfile               # Dev container image
├── Makefile                 # Convenience commands
└── README.md               # This file
```

## Development

See `/app/README.md` for application-specific documentation.

See `CLAUDE.md` for technical architecture details.

## Testing

Individual components can be tested:

```bash
# Test Ollama connection
python scripts/ollama_chat_test.py

# Test LLM class selection (with dummy data)
python scripts/test_llm_selection.py

# Test Pushover notifications
python scripts/test_pushover.py

# Test full Playwright flow (interactive)
python scripts/test2.py
```

## Security Notes

- `.env` file is gitignored - never commit credentials
- Screenshots (if saved) may contain personal info
- Pushover tokens should be kept private
- Consider using app-specific passwords for Wodify

## License

Private project - not licensed for redistribution.
