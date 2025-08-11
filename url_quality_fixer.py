#!/usr/bin/env python3
"""
URL QUALITY FIXER FOR ALL PROVIDERS
====================================
Fixes ALL image URLs in New_Providers_data JSON files:
- quality=20 → quality=90
- blur=150 → blur=0  
- width=195,height=260 → width=400,height=600
- Then downloads high-quality images
"""

import os
import json
import requests
import csv
from PIL import Image
import io
import re
from datetime import datetime

def fix_image_url_quality(url):
    """Fix image URL to have high quality and no blur"""
    if not url:
        return url
    
    # Fix bad quality URLs: quality=20,blur=150 → quality=90,blur=0
    url = url.replace("quality=20,blur=150", "quality=90,blur=0")
    
    # Also upgrade good URLs to even better: quality=90 → quality=95, and resolution
    url = url.replace("width=195,height=260,quality=90,blur=0,fit=cover", 
                     "width=400,height=600,quality=95,blur=0,fit=contain")
    
    return url

def sanitize_filename(filename):
    """Sanitize filename for Windows filesystem"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = filename.strip('.')
    return filename

def download_and_convert_image(image_url, output_path):
    """Download image and convert to WebP format"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Open image with PIL
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save as WebP with high quality
        image.save(output_path, 'WEBP', quality=95, optimize=True)
        print(f"  ✅ Saved: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def process_provider_with_fixed_urls(provider_name, json_file_path):
    """Process provider data with URL quality fixes"""
    print(f"\n🎯 Processing: {provider_name}")
    
    # Read JSON data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        games = data.get('games', [])
        total_games = data.get('total_games', len(games))
        print(f"📊 Found {total_games} games for {provider_name}")
    except Exception as e:
        print(f"❌ Error reading {json_file_path}: {e}")
        return []
    
    if not games:
        print(f"⚠️ No games found for {provider_name}")
        return []
    
    # Create provider directory
    provider_dir = os.path.join("Final_Quality_Fixed", provider_name)
    os.makedirs(provider_dir, exist_ok=True)
    
    successful_downloads = 0
    processed_games = []
    bad_quality_fixed = 0
    
    # Process each game
    for i, game in enumerate(games, 1):
        game_name = game.get('name', f"Game {i}")
        original_image_url = game.get('image_url', '')
        game_link = game.get('game_link', '')
        
        if not original_image_url:
            print(f"  ⚠️ No image URL for: {game_name}")
            continue
        
        # Fix image URL quality
        fixed_image_url = fix_image_url_quality(original_image_url)
        
        # Check if we fixed a bad quality URL
        if "quality=20,blur=150" in original_image_url:
            bad_quality_fixed += 1
            print(f"  🔧 Fixed bad quality URL for: {game_name}")
        
        # Create sanitized filename
        sanitized_game_name = sanitize_filename(game_name)
        sanitized_provider_name = sanitize_filename(provider_name)
        filename = f"{sanitized_provider_name} - {sanitized_game_name}.webp"
        
        # Full path for the image
        image_path = os.path.join(provider_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(image_path):
            print(f"  ⏭️ Already exists: {filename}")
            successful_downloads += 1
        else:
            # Download and convert image
            if download_and_convert_image(fixed_image_url, image_path):
                successful_downloads += 1
        
        # Add to processed games list
        processed_games.append({
            'file_name': filename,
            'game_title': game_name,
            'game_provider': provider_name,
            'game_url': game_link,
            'original_url': original_image_url,
            'fixed_url': fixed_image_url,
            'local_path': image_path
        })
    
    print(f"✅ {provider_name}: {successful_downloads}/{len(games)} images processed")
    if bad_quality_fixed > 0:
        print(f"🔧 Fixed {bad_quality_fixed} bad quality URLs (quality=20,blur=150)")
    return processed_games

def create_metadata_files(all_games_data):
    """Create CSV and JSON metadata files"""
    print(f"\n📋 Creating metadata files...")
    
    # Create CSV file
    csv_file = "Final_Quality_Fixed/games_metadata.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['file_name', 'game_title', 'game_provider', 'game_url', 'original_url', 'fixed_url', 'local_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_games_data)
    
    # Create JSON file
    json_file = "Final_Quality_Fixed/games_metadata.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extraction_date': datetime.now().isoformat(),
            'total_games': len(all_games_data),
            'total_providers': len(set(game['game_provider'] for game in all_games_data)),
            'image_quality': 'High Quality Fixed (quality=90→95, blur=150→0, 400x600)',
            'fixes_applied': 'quality=20→90, blur=150→0, width=195→400, height=260→600',
            'games': all_games_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Metadata files created:")
    print(f"   📄 CSV: {csv_file}")
    print(f"   📄 JSON: {json_file}")

def main():
    """Main function to fix URLs and download high-quality images"""
    print("🎯 URL QUALITY FIXER FOR ALL PROVIDERS")
    print("======================================")
    print("Fixing quality=20,blur=150 → quality=90,blur=0")
    print("Upgrading resolution: 195x260 → 400x600")
    
    # Check if New_Providers_data directory exists
    if not os.path.exists("New_Providers_data"):
        print("❌ Error: New_Providers_data directory not found!")
        return
    
    # Create Final_Quality_Fixed directory
    os.makedirs("Final_Quality_Fixed", exist_ok=True)
    
    # Get all provider directories from New_Providers_data
    providers = []
    for item in os.listdir("New_Providers_data"):
        item_path = os.path.join("New_Providers_data", item)
        if os.path.isdir(item_path):
            # Look for JSON file
            json_files = [f for f in os.listdir(item_path) if f.endswith('_games_data.json')]
            if json_files:
                json_file_path = os.path.join(item_path, json_files[0])
                providers.append((item, json_file_path))
                print(f"✅ Found: {item}")
            else:
                print(f"⚠️ No JSON file found for: {item}")
    
    print(f"\n📁 Processing {len(providers)} providers with URL quality fixes:")
    
    all_games_data = []
    total_bad_urls_fixed = 0
    
    # Process each provider
    for provider_name, json_file_path in providers:
        games_data = process_provider_with_fixed_urls(provider_name, json_file_path)
        all_games_data.extend(games_data)
    
    # Create metadata files
    create_metadata_files(all_games_data)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 URL QUALITY FIXING COMPLETE!")
    print(f"✅ Total providers processed: {len(providers)}")
    print(f"🎮 Total games processed: {len(all_games_data)}")
    print(f"📁 High-quality images saved in: Final_Quality_Fixed/")
    print(f"🔧 Quality fixes applied:")
    print(f"   • quality=20 → quality=90")
    print(f"   • blur=150 → blur=0")
    print(f"   • 195x260 → 400x600 resolution")
    print(f"   • Enhanced to quality=95 for best results")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
