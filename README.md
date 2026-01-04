# 🤖 A.Y.P.I Sertifikat Bot

Telegram bot for issuing official certificates to A.Y.P.I course graduates.

## 📋 Features

- ✅ Certificate request submission
- ✅ Admin approval system
- ✅ Manual certificate upload (PNG/JPG)
- ✅ Automatic Excel export
- ✅ Duplicate prevention
- ✅ User blocking system
- ✅ Professional admin panel

## 🚀 Deployment

### Option 1: Render.com (Recommended for 24/7)

1. Fork this repository
2. Go to [Render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Set environment variables:
   - `BOT_TOKEN`: Your bot token from @BotFather
   - `ADMIN_ID`: Your Telegram user ID
6. Click "Create Web Service"

### Option 2: Local Development

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/aypi-sertifikat-bot.git
cd aypi-sertifikat-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials

5. Run the bot:
```bash
python bot.py
```

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Bot token from @BotFather | `123456789:ABC...` |
| `ADMIN_ID` | Telegram user ID of admin | `817765302` |
| `EXCEL_FILE` | Excel export filename | `tasdiqlangan_sertifikatlar.csv` |

## 📊 Database

The bot uses SQLite database (`certificate_database.db`) to store:
- Certificate requests
- User information
- Request status
- Timestamps

## 📁 File Structure

```
aypi-sertifikat-bot/
├── bot.py                    # Main bot application
├── requirements.txt          # Python dependencies
├── Procfile                  # Render deployment config
├── render.yaml              # Render settings
├── .gitignore               # Git ignore rules
├── .env.example             # Environment variables template
├── README.md                # This file
├── certificate_database.db  # SQLite database (auto-created)
└── tasdiqlangan_sertifikatlar.csv  # Excel export (auto-created)
```

## 👨‍💼 Admin Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/kutish` | View pending requests |
| `/statistika` | View statistics |
| `/tasdiqlash` | Approve request |
| `/rad` | Reject request |
| `/yuborish` | Send certificate |
| `/export` | Download Excel file |

## 👤 User Flow

1. User sends `/start`
2. Accepts warning and terms
3. Submits name and details
4. Admin receives notification
5. Admin approves/rejects
6. Admin uploads certificate (PNG/JPG)
7. User receives certificate

## 🔒 Security Features

- ✅ One request per user
- ✅ Duplicate phone number detection
- ✅ Admin-only commands
- ✅ User blocking capability
- ✅ Strict input validation

## 📞 Support

Created by **Oybek Bozorov** - OYBEK YOUTUBER MCHJ

Bot: [@aypisertifikatbot](https://t.me/aypisertifikatbot)

## 📝 License

This project is created for A.Y.P.I platform.

---

**⚠️ Important:** Never commit your `.env` file or expose your bot token publicly!
