# Google Play Store Scraper 🔍

A robust and efficient tool to scrape Google Play Store search results. Powered by browser automation, it bypasses standard search API limits, scrolls to retrieve all matching apps, and extracts details (name, installs, rating, developer email, website, description, release date, version, etc.) into structured CSV files.

## Project Structure

```text
├── run.sh              # Auto-launcher script (root level)
├── scraper/            # Source folder
│   ├── scraper.py      # Core python script
│   └── requirements.txt# Python dependency list
└── output/             # Output folder (auto-created, contains results)
    ├── {keyword}.csv   # All fields
    └── {keyword}_contacts.csv # Contacts only (Index, Name, Email)
```

---

## Setup & Launcher Instructions

The root folder contains a launcher script (`run.sh`) that automatically manages virtual environment setup, installs requirements from `scraper/requirements.txt`, checks/installs Playwright Chromium browser drivers, and boots the scraper.

### Run via Launcher:
Make the script executable (only needed once) and run it:
```bash
chmod +x run.sh && ./run.sh
```

It will guide you through three interactive input fields:
1. **Enter search keyword**: Type the keyword you want to search.
2. **Enter output file name**: Press Enter to use the default (derived from your keyword) or type a custom file name (e.g., `health_apps.csv`).
3. **How many apps to scrape**: Type `all` to retrieve all available search results from Google Play (scrolling all the way to the end), or specify a custom number (e.g., `50`).

The generated files will automatically be saved under the `output/` directory:
- `output/{keyword}.csv` (All detailed fields)
- `output/{keyword}_contacts.csv` (App index, Name, and Developer Email)

---

## Command-Line Arguments

You can also pass arguments directly to the launcher script to run it without prompts:
```bash
./run.sh --keyword "calisthenics" --limit 15
```

### Available Flags:
| Flag | Description | Default |
| :--- | :--- | :--- |
| `-k`, `--keyword` | The keyword to search for on Google Play | (Prompts if empty) |
| `-l`, `--limit` | The maximum number of apps to query | `20` (use `all` in interactive mode for no limit) |
| `-o`, `--output` | The destination file name (saved inside the `output/` directory) | (Derived from keyword) |

---

## Output Structure

All CSV files include a sequential `#` column. The full CSV contains:
1. **#**: contiguous sequential index.
2. **App Name**: The official title of the application.
3. **App Link**: URL to the app on the Google Play Store.
4. **Rating**: Average star rating.
5. **Downloads**: Total download range (e.g. `1,000,000+`).
6. **Version**: Current version of the app.
7. **Released**: Date the app was originally released.
8. **Last Updated**: Date of the last update on Google Play.
9. **Developer Name**: The name of the publisher or studio.
10. **Developer Email**: Developer support email.
11. **Developer Website**: Link to the developer's website.
12. **About the Developer / Address**: Physical registry address of the developer.
13. **About the App / Description**: Detailed description of the application.

