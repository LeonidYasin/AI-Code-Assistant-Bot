# AI Code Assistant - Deployment Package

## Quick Start

1. Install dependencies:
   `
   pip install -r requirements.txt
   `

2. Copy .env.example to .env and update with your configuration:
   `
   copy .env.example .env
   # Edit .env with your configuration
   `

3. Run the application:
   `
   python main.py
   `

## Project Structure

- config/ - Configuration files
- core/ - Core application code
- handlers/ - Message and command handlers
- main.py - Application entry point

## Configuration

Update the following environment variables in .env:

- TELEGRAM_BOT_TOKEN - Your Telegram bot token
- GIGACHAT_CREDENTIALS - GigaChat API credentials
- LOG_LEVEL - Logging level (INFO, DEBUG, etc.)

## License

This project is licensed under the MIT License.
