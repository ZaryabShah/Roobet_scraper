#!/usr/bin/env python3
"""
CLEAN MULTI-PROVIDER ROOBET SCRAPER
===================================
Uses the EXACT same process that worked perfectly with Pragmatic Play
- Fresh Chrome instance for each provider
- Same XPath patterns that worked
- Same Load More button clicking logic
- Checkpoint system after each provider
"""

import time
import os
import json
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

def close_all_chrome():
    """Close all Chrome processes completely"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
        time.sleep(2)
    except:
        pass

def scrape_single_provider(provider_url, provider_name):
    """Scrape games from a single provider using the EXACT same method as Pragmatic Play"""
    print(f"\n🚀 Starting scrape for: {provider_name}")
    print(f"📍 URL: {provider_url}")
    
    # Create fresh Chrome driver (same as original)
    driver = webdriver.Chrome()
    
    try:
        # Navigate to provider page (same as original)
        print("Navigating to provider page...")
        driver.get(provider_url)
        
        # Wait for page to load (same as original)
        print("Waiting for page to load...")
        time.sleep(15)
        
        # Click Load More button until it disappears (EXACT same logic)
        print("Clicking Load More button...")
        button_xpath = "/html/body/div[1]/div/main/div[1]/div/div/div[2]/div[2]/ul/div/div[2]/button"
        click_count = 0
        
        while click_count < 50:  # Safety limit
            try:
                button = driver.find_element(By.XPATH, button_xpath)
                button.click()
                click_count += 1
                print(f"Clicked Load More button #{click_count}")
                time.sleep(4)  # Wait for new games to load
            except:
                print("Load More button no longer found - all games loaded")
                break
        
        print(f"Finished clicking Load More button {click_count} times")
        
        # Extract game data (EXACT same method)
        print("Extracting game data...")
        games = []
        
        # Find the main UL element (same XPath as original)
        ul_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/main/div[1]/div/div/div[2]/div[2]/ul")
        # /html/body/div[1]/div/main/div[1]/div/div[2]/div/ul/div/div[1]/a[2]
        # /html/body/div[1]/div/main/div[1]/div/div[2]/div/ul/div/div[1]/a[1]

        # /html/body/div[1]/div/main/div[1]/div/div/div[2]/div[2]/ul/div/div/a[1]
        # /html/body/div[1]/div/main/div[1]/div/div/div[2]/div[2]/ul/div/div/a[2]
        # Find the first div child (same as original)
        main_div = ul_element.find_element(By.XPATH, "./div")
        
        # Find all anchor tags in this div (same as original)
        anchors = main_div.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(anchors)} games")
        
        # Extract data from each game (EXACT same logic)
        for i, anchor in enumerate(anchors, 1):
            try:
                # Find image in anchor
                img = anchor.find_element(By.TAG_NAME, "img")
                game_name = img.get_attribute("alt") or f"Game {i}"
                img_url = img.get_attribute("src") or ""
                game_link = anchor.get_attribute("href") or ""
                
                game_data = {
                    'index': i,
                    'name': game_name,
                    'image_url': img_url,
                    'game_link': game_link
                }
                games.append(game_data)
                
                if i <= 5:  # Show first 5 for verification
                    print(f"Game {i}: {game_name}")
                    
            except Exception as e:
                print(f"Error extracting game {i}: {e}")
        
        return {
            'success': True,
            'games': games,
            'click_count': click_count,
            'html': driver.page_source
        }
        
    except Exception as e:
        print(f"❌ Error scraping {provider_name}: {e}")
        return {
            'success': False,
            'error': str(e),
            'games': [],
            'click_count': 0,
            'html': ''
        }
        
    finally:
        driver.quit()
        print("Browser closed.")

def save_provider_data(provider_name, result):
    """Save provider data to files"""
    # Create provider directory
    provider_dir = f"New_Providers_data/{provider_name}"
    os.makedirs(provider_dir, exist_ok=True)
    
    # Save TXT file (same format as original)
    txt_file = f"{provider_dir}/{provider_name}_games_data.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"{provider_name} Games Data\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total games found: {len(result['games'])}\n")
        f.write(f"Load More clicks: {result['click_count']}\n")
        f.write(f"Extraction date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        for game in result['games']:
            f.write(f"Game #{game['index']}:\n")
            f.write(f"  Name: {game['name']}\n")
            f.write(f"  Image URL: {game['image_url']}\n")
            f.write(f"  Game Link: {game['game_link']}\n")
            f.write("-" * 40 + "\n")
    
    # Save JSON file
    json_file = f"{provider_dir}/{provider_name}_games_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'provider': provider_name,
            'total_games': len(result['games']),
            'load_more_clicks': result['click_count'],
            'extraction_date': datetime.now().isoformat(),
            'games': result['games']
        }, f, indent=2, ensure_ascii=False)
    
    # Save HTML file
    html_file = f"{provider_dir}/{provider_name}_complete.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(result['html'])
    
    print(f"✅ Data saved for {provider_name}:")
    print(f"   📄 TXT: {txt_file}")
    print(f"   📄 JSON: {json_file}")
    print(f"   📄 HTML: {html_file}")

def main():
    """Main scraping function"""
    # Provider list as specified by user
    providers = [
    ("https://roobet.com/casino/category/slots?providers=Ace+Roll&sort=pop_desc", "Ace Roll"),
    ("https://roobet.com/casino/category/slots?providers=Alchemy+Gaming&sort=pop_desc", "Alchemy Gaming"),
    ("https://roobet.com/casino/category/slots?providers=All41&sort=pop_desc", "All41"),
    ("https://roobet.com/casino/category/slots?providers=Bitpunch&sort=pop_desc", "Bitpunch"),
    ("https://roobet.com/casino/category/slots?providers=Boomerang+Studios&sort=pop_desc", "Boomerang Studios"),
    ("https://roobet.com/casino/category/slots?providers=Buck+Stakes+Entertainment&sort=pop_desc", "Buck Stakes Entertainment"),
    ("https://roobet.com/casino/category/slots?providers=Clawbuster&sort=pop_desc", "Clawbuster"),
    ("https://roobet.com/casino/category/slots?providers=Degen+Studios&sort=pop_desc", "Degen Studios"),
    ("https://roobet.com/casino/category/slots?providers=Electric+Elephant&sort=pop_desc", "Electric Elephant"),
    ("https://roobet.com/casino/category/slots?providers=Four+Leaf+Gaming&sort=pop_desc", "Four Leaf Gaming"),
    ("https://roobet.com/casino/category/slots?providers=Foxium&sort=pop_desc", "Foxium"),
    ("https://roobet.com/casino/category/slots?providers=Gameburger&sort=pop_desc", "Gameburger"),
    ("https://roobet.com/casino/category/slots?providers=Gaming+Corps&sort=pop_desc", "Gaming Corps"),
    ("https://roobet.com/casino/category/slots?providers=Iron+Dog+Studio&sort=pop_desc", "Iron Dog Studio"),
    ("https://roobet.com/casino/category/slots?providers=irondogstudio&sort=pop_desc", "irondogstudio"),
    ("https://roobet.com/casino/category/slots?providers=Just+For+The+Win&sort=pop_desc", "Just For The Win"),
    ("https://roobet.com/casino/category/slots?providers=Kalamba+Games&sort=pop_desc", "Kalamba Games"),
    ("https://roobet.com/casino/category/slots?providers=Kitsune+Gaming+Studios&sort=pop_desc", "Kitsune Gaming Studios"),
    ("https://roobet.com/casino/category/slots?providers=Microgaming&sort=pop_desc", "Microgaming"),
    ("https://roobet.com/casino/category/slots?providers=Neon+Valley+Studios&sort=pop_desc", "Neon Valley Studios"),
    ("https://roobet.com/casino/category/slots?providers=Northern+Lights+Gaming&sort=pop_desc", "Northern Lights Gaming"),
    ("https://roobet.com/casino/category/slots?providers=NowNow+Gaming&sort=pop_desc", "NowNow Gaming"),
    ("https://roobet.com/casino/category/slots?providers=Old+Skool&sort=pop_desc", "Old Skool"),
    ("https://roobet.com/casino/category/slots?providers=Reelplay&sort=pop_desc", "Reelplay"),
    ("https://roobet.com/casino/category/slots?providers=Slingshot+Studios&sort=pop_desc", "Slingshot Studios"),
    ("https://roobet.com/casino/category/slots?providers=SpinOn&sort=pop_desc", "SpinOn"),
    ("https://roobet.com/casino/category/slots?providers=SpinPlay+Games&sort=pop_desc", "SpinPlay Games"),
    ("https://roobet.com/casino/category/slots?providers=Stormcraft&sort=pop_desc", "Stormcraft"),
    ("https://roobet.com/casino/category/slots?providers=Triple+Edge&sort=pop_desc", "Triple Edge"),
    ("https://roobet.com/casino/category/slots?providers=Trusty+Gaming&sort=pop_desc", "Trusty Gaming"),
    ("https://roobet.com/casino/category/slots?providers=Yggdrasil&sort=pop_desc", "Yggdrasil"),
]
    
    print("🎯 CLEAN MULTI-PROVIDER ROOBET SCRAPER")
    print("=====================================")
    print(f"Total providers to scrape: {len(providers)}")
    print("Using EXACT same method that worked with Pragmatic Play")
    
    # Create main directory
    os.makedirs("New_Providers_data", exist_ok=True)
    
    # Checkpoint system
    checkpoint_file = "New_Providers_data/checkpoint.json"
    completed_providers = []
    
    # Load existing checkpoint
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                completed_providers = checkpoint_data.get('completed_providers', [])
                print(f"📂 Loaded checkpoint: {len(completed_providers)} providers already completed")
        except:
            print("⚠️ Could not load checkpoint, starting fresh")
    
    total_games = 0
    successful_providers = 0
    
    for i, (provider_url, provider_name) in enumerate(providers, 1):
        # Skip if already completed
        if provider_name in completed_providers:
            print(f"⏭️ Skipping {provider_name} (already completed)")
            continue
        
        print(f"\n{'='*60}")
        print(f"🎯 PROVIDER {i}/{len(providers)}: {provider_name}")
        print(f"{'='*60}")
        
        # Close any existing Chrome processes
        close_all_chrome()
        
        # Scrape provider using exact same method as Pragmatic Play
        result = scrape_single_provider(provider_url, provider_name)
        
        if result['success']:
            # Save data using same format as original
            save_provider_data(provider_name, result)
            
            # Update totals
            total_games += len(result['games'])
            successful_providers += 1
            
            print(f"✅ {provider_name}: {len(result['games'])} games, {result['click_count']} clicks")
            
            # Update checkpoint
            completed_providers.append(provider_name)
            checkpoint_data = {
                'completed_providers': completed_providers,
                'last_updated': datetime.now().isoformat(),
                'total_games_so_far': total_games,
                'successful_providers': successful_providers
            }
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            print(f"🔄 Checkpoint saved: {len(completed_providers)} providers completed")
            
        else:
            print(f"❌ {provider_name}: Failed - {result['error']}")
        
        # Wait between providers
        print("⏳ Waiting 5 seconds before next provider...")
        time.sleep(5)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 SCRAPING COMPLETE!")
    print(f"✅ Successful providers: {successful_providers}/{len(providers)}")
    print(f"🎮 Total games scraped: {total_games}")
    print(f"📁 Data saved in: New_Providers_data/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
