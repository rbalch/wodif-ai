# Wodify Auto-Signup Production App

## Running the Application

### One-Time Setup
```bash
# Make sure Ollama is running and model is downloaded
docker-compose up -d ollama

# Wait for model to download (check logs)
docker logs -f wodify-ollama
```

### Manual Run (Testing)
```bash
# Run from host machine
cd /home/ryan/code/wodify-signup
docker-compose run --rm dev python /app/main.py

# Run from inside dev container
python /app/main.py
```

### Production Run (Cron Job)

**Option 1: Docker Compose Run (Recommended)**
```bash
# Add to crontab (crontab -e)
0 19 * * 0-4 cd /home/ryan/code/wodify-signup && docker-compose run --rm dev python /app/main.py >> /var/log/wodify.log 2>&1
```

This runs:
- At 7:00 PM (19:00)
- Sunday through Thursday (0-4)
- Books tomorrow's class
- Logs to /var/log/wodify.log
- `--rm` flag removes container after completion
- Ollama service stays running (faster, keeps model in memory)

**Option 2: Full Start/Stop**
```bash
# If you want to stop everything after each run
0 19 * * 0-4 cd /home/ryan/code/wodify-signup && docker-compose up -d && docker-compose exec dev python /app/main.py && docker-compose down >> /var/log/wodify.log 2>&1
```

## Environment Variables

Required in `.env` file:
```bash
# Wodify credentials
EMAIL=your_email@example.com
PASSWORD=your_password

# Pushover (optional but recommended)
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token

# Optional overrides
DAYS_AHEAD=1              # Days in advance to book (default: 1)
HEADLESS=true             # Run browser headless (default: true)
OLLAMA_MODEL=qwen3:8b     # LLM model (default: qwen3:8b)
```

## Customizing Preferences

Edit `app/prompts/system_prompt.txt` to change:
- Target time window
- Class type preferences
- Notification logic

## Logs and Debugging

View logs:
```bash
# If using cron with log file
tail -f /var/log/wodify.log

# If running docker-compose directly
docker-compose logs -f dev
```

Screenshots (if enabled) saved to:
```
/home/ryan/code/wodify-signup/screenshots/
```

## Exit Codes

- `0`: Success - class booked
- `1`: Failure - error occurred (triggers notification if Push over configured)

## Troubleshooting

### "No classes found"
- Check that the date format matches Wodify's calendar
- Verify the calendar loaded properly (run with `HEADLESS=false`)

### "Failed to login"
- Verify EMAIL and PASSWORD in .env
- Check if Wodify login page changed

### "LLM returned invalid JSON"
- Model might need more time (check Ollama logs)
- Try increasing temperature or using different model

### "Pushover notifications not working"
- Verify PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN are correct
- Check Pushover API status

## Architecture

```
main.py                  # Orchestrates the workflow
├── Config               # Environment configuration
├── BrowserService       # Playwright automation
├── LLMService           # Ollama class selection
└── NotificationService  # Pushover alerts
```

See `/home/ryan/code/wodify-signup/CLAUDE.md` for full technical documentation.
