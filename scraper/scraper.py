# ==================================================
# Google Play Store Scraper
# Developer: Shanto
# Contact: dev@shanto.top
# ==================================================

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import pandas as pd
from google_play_scraper import app
from tabulate import tabulate
from playwright.sync_api import sync_playwright

def send_to_n8n(webhook_url, data):
    print(f"\n[*] Sending {len(data)} results to n8n webhook: {webhook_url}...")
    try:
        # Convert Python list of dicts to JSON bytes
        payload = json.dumps(data).encode("utf-8")
        
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Playstore-Scraper-Client"
            },
            method="POST"
        )
        
        # 15 second timeout for request
        with urllib.request.urlopen(req, timeout=15) as response:
            status_code = response.getcode()
            print(f"[+] Successfully sent to n8n! (HTTP {status_code})")
            
    except Exception as e:
        print(f"[!] Failed to send data to n8n webhook: {e}")


def clean_filename(keyword):
    # Lowercase, replace spaces/hyphens with underscores, remove non-alphanumeric characters
    name = keyword.strip().lower()
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'[^a-z0-9_]', '', name)
    if not name:
        name = "scraped_apps"
    return f"{name}.csv"


def scrape_search_results_playwright(keyword, limit=20, lang="en", country="us"):
    print(f"\n[*] Launching browser to search all results for: '{keyword}'...")
    app_ids = []
    
    # URL to search
    url = f"https://play.google.com/store/search?q={keyword}&c=apps&hl={lang}&gl={country}"
    
    try:
        with sync_playwright() as p:
            # Launch chromium in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            
            # Wait for search links to load
            page.wait_for_selector('a[href*="/store/apps/details?id="]', timeout=15000)
            
            last_height = page.evaluate("document.body.scrollHeight")
            no_change_count = 0
            
            while True:
                # Extract links loaded so far
                hrefs = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a[href*="/store/apps/details?id="]'));
                    return links.map(a => a.getAttribute('href'));
                }""")
                
                for href in hrefs:
                    if "id=" in href:
                        app_id = href.split("id=")[-1].split("&")[0]
                        if app_id not in app_ids:
                            app_ids.append(app_id)
                            
                if len(app_ids) >= limit:
                    break
                    
                # Scroll to bottom
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
                # Check height
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
                    
            browser.close()
            
    except Exception as e:
        print(f"[!] Browser automation error: {e}")
        
    return app_ids[:limit]


def scrape_playstore(keyword, limit=20, lang="en", country="us"):
    # 1. Fetch app IDs using Playwright search pagination
    app_ids = scrape_search_results_playwright(keyword, limit, lang, country)
    
    if not app_ids:
        print("[!] No apps found for this keyword.")
        return []

    print(f"\n[*] Found {len(app_ids)} apps. Fetching details for each...")
    
    detailed_apps = []
    try:
        for idx, app_id in enumerate(app_ids, 1):
            print(f"    [{idx}/{len(app_ids)}] Fetching details for: {app_id}... (Press Ctrl+C to save and exit)")
            
            try:
                # Fetch detailed app info
                details = app(app_id, lang=lang, country=country)
                
                dev_name = details.get("developer", "N/A")
                dev_email = details.get("developerEmail", "N/A")
                
                # Clean description (remove html tags, newlines, multiple spaces)
                description = details.get("description", "N/A")
                if description and description != "N/A":
                    description = re.sub(r'<[^>]*>', '', description)
                    description = re.sub(r'[\r\n]+', ' ', description)
                    description = re.sub(r'\s+', ' ', description).strip()
                    
                # Clean address (remove newlines and multiple spaces)
                dev_address = details.get("developerAddress", "N/A")
                if dev_address and dev_address != "N/A":
                    dev_address = re.sub(r'[\r\n]+', ' ', dev_address)
                    dev_address = re.sub(r'\s+', ' ', dev_address).strip()
                    
                app_data = {
                    "App Name": details.get("title"),
                    "App Link": f"https://play.google.com/store/apps/details?id={app_id}",
                    "Rating": details.get("score"),
                    "Downloads": details.get("installs"),
                    "Version": details.get("version", "N/A"),
                    "Released": details.get("released", "N/A"),
                    "Last Updated": details.get("lastUpdatedOn", "N/A"),
                    "Developer Name": dev_name,
                    "Developer Email": dev_email,
                    "Developer Website": details.get("developerWebsite", "N/A"),
                    "About the Developer / Address": dev_address,
                    "About the App / Description": description,
                }
                detailed_apps.append(app_data)
            except Exception as e:
                print(f"    [!] Failed to fetch details for {app_id}: {e}")
            
            # Sleep to be polite to Google servers
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n[!] Scrape interrupted by user. Saving the {len(detailed_apps)} apps scraped so far...")
        
    # Assign contiguous numbers for final output results
    final_apps = []
    for num, app_data in enumerate(detailed_apps, 1):
        numbered_app = {"#": num}
        numbered_app.update(app_data)
        final_apps.append(numbered_app)
        
    return final_apps

def main():
    parser = argparse.ArgumentParser(description="Google Play Store Keyword Scraper")
    parser.add_argument("-k", "--keyword", type=str, help="Search keyword")
    parser.add_argument("-l", "--limit", type=int, default=20, help="Number of app results to scrape (default: 20)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output CSV file path (default: based on keyword)")
    parser.add_argument("-w", "--webhook", type=str, default=None, help="n8n webhook URL to send scraped results")
    args = parser.parse_args()

    # If no keyword is provided, prompt the user
    keyword = args.keyword
    limit = args.limit
    
    if not keyword:
        try:
            # 1. Ask for keyword
            keyword = input("Enter search keyword: ").strip()
            if not keyword:
                print("[!] Keyword cannot be empty.")
                sys.exit(1)
                
            # Generate default output file name based on keyword
            default_output = clean_filename(keyword)
            
            # 2. Ask for output file name
            user_output = input(f"Enter output file name (default: {default_output}): ").strip()
            if user_output:
                if not user_output.endswith(".csv"):
                    user_output += ".csv"
                output_file = user_output
            else:
                output_file = default_output
                
            # 3. Ask for how many apps (all or custom)
            user_limit = input("How many apps to scrape? Enter 'all' or a custom number (default: 20): ").strip().lower()
            if user_limit == "all":
                limit = 10000
                print("[*] Set limit to retrieve all available apps (scrolling to the absolute end of Google Play search results).")
            elif user_limit.isdigit():
                limit = int(user_limit)
        except KeyboardInterrupt:
            print("\n[!] Exited by user.")
            sys.exit(0)
    else:
        # If running from CLI directly, construct output file name from keyword if not provided
        if args.output:
            output_file = args.output
        else:
            output_file = clean_filename(keyword)
            
    results = scrape_playstore(keyword, limit=limit)
    
    if not results:
        print("[!] No details retrieved. Exiting.")
        sys.exit(0)
        
    df = pd.DataFrame(results)
    
    # Ensure all output goes inside the 'output/' directory
    os.makedirs("output", exist_ok=True)
    filename = os.path.basename(output_file)
    output_file = os.path.join("output", filename)
    
    # Generate the contacts-only file name (e.g., output/playstore_apps_contacts.csv)
    contacts_file = output_file.replace(".csv", "_contacts.csv")
        
    # Save to CSV (All fields)
    try:
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n[+] Successfully saved {len(results)} apps details (All Fields) to: {output_file}")
    except Exception as e:
        print(f"[!] Error saving all fields CSV: {e}")
        
    # Save to CSV (App Name and Developer Email)
    try:
        contacts_df = df[["#", "App Name", "Developer Email"]]
        contacts_df.to_csv(contacts_file, index=False, encoding='utf-8')
        print(f"[+] Successfully saved contacts (App Name, Developer Email) to: {contacts_file}")
    except Exception as e:
        print(f"[!] Error saving contacts CSV: {e}")
        
    # Send results to n8n webhook if configured
    if args.webhook:
        send_to_n8n(args.webhook, results)
        
    # Display a beautiful, structured table of all scraped apps
    print(f"\n--- Scraped Apps ({len(results)} results) ---")
    
    # Select columns to display, including the `#` column
    preview_cols = ["#", "App Name", "Rating", "Downloads", "Developer Name", "Developer Email"]
    preview_df = df[preview_cols].copy()
    
    # Round ratings to 2 decimal places for clean display
    preview_df["Rating"] = preview_df["Rating"].apply(
        lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and not pd.isna(x) else x
    )
    
    # Use github table format for clean copy-paste compatibility and structure
    print(tabulate(preview_df, headers='keys', tablefmt='github', showindex=False))

if __name__ == "__main__":
    main()
