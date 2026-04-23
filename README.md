# 🏆 FIFA World Cup 2026 Calendar

Multi-language `.ics` calendar subscriptions for the FIFA World Cup 2026 (United
States, Canada & Mexico). Updated automatically every day with the latest
fixtures, results, and schedule changes.

## 📅 Subscribe to a Calendar

Pick your language and add the URL to Google Calendar, Apple Calendar, Outlook,
or any app that supports `.ics` subscriptions.

| Language | URL |
|----------|-----|
| 🇺🇸 English | `https://raw.githubusercontent.com/baires/fifa-world-cup-2026-cal/main/calendars/en.ics` |
| 🇪🇸 Español | `https://raw.githubusercontent.com/baires/fifa-world-cup-2026-cal/main/calendars/es.ics` |
| 🇧🇷 Português | `https://raw.githubusercontent.com/baires/fifa-world-cup-2026-cal/main/calendars/pt.ics` |


You can also use the `webcal://` protocol prefix in most calendar apps:
```
webcal://raw.githubusercontent.com/baires/fifa-world-cup-2026-cal/main/calendars/en.ics
```

### Google Calendar
1. Open [Google Calendar](https://calendar.google.com)
2. Click **+** next to "Other calendars" → **From URL**
3. Paste the raw URL for your language
4. Click **Add calendar**

### Apple Calendar (macOS/iOS)
1. Go to **File → New Calendar Subscription…**
2. Paste the raw URL
3. Set refresh frequency to **Every day**

## ⚽ What's Included

- **All 104 matches** — Group stage, Round of 32, Round of 16, Quarter-finals,
  Semi-finals, Third Place Match, and Final
- **Automatic updates** — Results are added to past matches as the tournament
  progresses
- **Schedule changes** — If match times or venues change, your calendar will
  update automatically
- **Localized content** — Calendar names, phase names, and labels are translated
- **Reminders** — 30-minute notification before each match kicks off

## 🔄 How It Works

Every day a [GitHub Actions](.github/workflows/update-calendars.yml) workflow:

1. Fetches the latest match data from
   [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json)
   (public domain, no API key required)
2. Generates `.ics` files for English, Spanish, and Portuguese
3. Commits any changes back to the repository
4. Calendar apps pick up the changes on their next sync (typically every
   12–24 hours)

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Generate calendars manually
python scripts/generate.py

# Output is written to calendars/{en,es,pt}.ics
```

## 📝 Data Source

Match data is sourced from
[openfootball/worldcup.json](https://github.com/openfootball/worldcup.json),
a public domain (CC0) dataset maintained by the openfootball community.

During the tournament the dataset is updated with:
- Full-time and half-time scores
- Goal scorers
- Penalty shootout results

## 📄 License

This project is released into the public domain under
[CC0 1.0 Universal](LICENSE).
