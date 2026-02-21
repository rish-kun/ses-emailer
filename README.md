# SES Email Sender TUI

A powerful Terminal User Interface (TUI) application for sending bulk emails via AWS SES (Simple Email Service).

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 📧 **Compose Emails** - Create HTML or plain text emails with a user-friendly interface
- 📋 **Excel Import** - Load recipient lists from Excel files
- 📎 **Attachments** - Add file attachments to your emails
- 📊 **Batch Sending** - Send emails in configurable batches with rate limiting
- 📈 **Progress Tracking** - Real-time progress bars and activity logs during sending
- 📜 **History** - View all sent emails with search and statistics
- ⚙️ **Configuration** - Easy AWS credentials and sender settings management
- 🎨 **Modern UI** - Sleek interface inspired by Atom One Dark Pro with improved typography and layout

## Installation

### Prerequisites

- Python 3.12 or higher
- AWS SES account with verified sender email
- `uv` package manager (recommended) or `pip`

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ses-email
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

   Or using `pip`:
   ```bash
   pip install -e .
   ```

3. Run the application:
   ```bash
   # Using uv
   uv run ses-email

   # Or directly with Python
   python -m tui.app
   ```

## Configuration

### AWS Credentials

Before sending emails, you need to configure your AWS SES credentials:

1. Launch the application
2. Go to **Settings** (press `S` or click the Settings button)
3. In the **AWS Credentials** tab, enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region (e.g., `us-east-1`)
   - Source Email (must be verified in SES)

4. Click **Save**

> ⚠️ **Security Note**: Your credentials are stored locally in `config/settings.json`. This file is excluded from git by default. Never commit your credentials to version control.

### Sender Settings

Configure how your emails appear to recipients:

- **Sender Display Name**: The name shown in the "From" field
- **Reply-To Email**: Where replies will be sent
- **Default TO Address**: Usually the same as your source email (for BCC mode)

### Batch Settings

Control how emails are sent:

- **Batch Size**: Number of emails per batch (default: 50)
- **Delay Between Batches**: Seconds to wait between batches (default: 60)
- **Send as BCC**: Recommended for bulk emails to protect recipient privacy

## Usage

### Sending Emails

1. **Compose**: Press `C` or click "Compose Email"
2. **Add Recipients**:
   - Load from Excel file: Enter the file path and column index, then click "Load"
   - Or enter emails manually, one per line
3. **Write Content**:
   - Enter the subject line
   - Choose HTML or Plain Text format
   - Write your email body
4. **Add Attachments** (optional):
   - Use the file browser or enter paths manually
5. **Preview**: Check the Preview tab to verify your email
6. **Send**: Click "Proceed to Send" and then "Start Sending"

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit application |
| `Ctrl+H` | Go to Home screen |
| `?` | Show help |
| `Tab` / `Shift+Tab` | Navigate between elements |
| `Enter` | Select/Activate |
| `Escape` | Go back / Cancel |

#### Screen-Specific Shortcuts

**Home Screen:**
- `C` - Compose new email
- `S` - Open Settings
- `H` - View History
- `Q` - Quit

**Compose Screen:**
- `Ctrl+Enter` - Proceed to send
- `Ctrl+S` - Save draft

**History Screen:**
- `/` - Focus search
- `R` - Refresh data

## Project Structure

```
ses-email/
├── tui/                    # TUI application
│   ├── app.py              # Main application entry point
│   ├── styles.tcss         # Textual CSS styles
│   └── screens/            # Screen definitions
│       ├── home.py         # Home/menu screen
│       ├── config.py       # Configuration screen
│       ├── compose.py      # Email composition screen
│       ├── send.py         # Sending screen with progress
│       └── history.py      # Email history screen
├── sending/                # Email sending logic
│   ├── db.py               # SQLite database operations
│   ├── emails.py           # Email message classes
│   ├── email_list.py       # Excel scraping utilities
│   ├── senders.py          # Email sender classes
│   └── final_mail.py       # SES sending functions
├── config/                 # Configuration
│   ├── settings.py         # Configuration management
│   └── settings.json       # User settings (not in git)
├── files/                  # Attachments directory
├── data/                   # Data files
└── emails.db               # SQLite database (auto-created)
```

## AWS SES Setup

1. **Create an AWS Account** if you don't have one
2. **Navigate to SES** in the AWS Console
3. **Verify your sender email address** or domain
4. **Request production access** if you're in sandbox mode
5. **Create IAM credentials** with SES send permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ses:SendEmail",
           "ses:SendRawEmail"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

## Database

The application uses SQLite to store email history:

- **emails** table: Stores email templates (subject, body, sender, attachments)
- **sent_emails** table: Stores individual send records (recipient, timestamp, type)

The database is automatically created at `emails.db` on first run.

## Troubleshooting

### "AWS credentials not configured"

Go to Settings and enter your AWS credentials. Make sure the source email is verified in SES.

### "Access Denied" errors

Check that your IAM user has the correct SES permissions and that you're using the correct region.

### Emails not being delivered

1. Check if you're in SES sandbox mode (can only send to verified emails)
2. Verify your sender email address in SES console
3. Check the activity log for error messages

### Excel file not loading

1. Ensure the file exists at the specified path
2. Check that `openpyxl` is installed (`uv add openpyxl`)
3. Verify the column index is correct (0-based)

## Dependencies

- **textual** - TUI framework
- **boto3** - AWS SDK for Python
- **pandas** - Data manipulation (Excel reading)
- **openpyxl** - Excel file support
- **python-dotenv** - Environment variable management

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.