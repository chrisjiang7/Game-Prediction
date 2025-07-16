import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv

def parse_tournament_date(date_str):
    """Convert Liquipedia date format to datetime object"""
    try:
        if not date_str or date_str == 'N/A':
            return None
        
        if '-' in date_str.split(',')[0]:  # Date range like "Feb 2-15, 2026"
            year = date_str.split(', ')[-1]
            month_day = date_str.split('-')[0].strip()
            return datetime.strptime(f"{month_day}, {year}", "%b %d, %Y")
        else:  # Single date like "May 10, 2025"
            return datetime.strptime(date_str, "%b %d, %Y")
    except ValueError:
        return None

def clean_location(location_str):
    """Clean location data by taking the first location if multiple exist"""
    if not location_str or location_str == 'N/A':
        return 'N/A'
    return location_str.split('|')[0].split('•')[0].split('\n')[0].strip()

def extract_team_name(team_div):
    """Enhanced team name extraction that handles Liquipedia's various formats"""
    if not team_div:
        return 'TBD'
    
    # Try different methods to extract team name
    name_sources = [
        team_div.find('a', class_=lambda x: x and ('team' in x.lower() or 'participant' in x.lower())),
        team_div.find('span', class_='team-template-text'),
        team_div.find('span', class_='name'),
        team_div.find('img', alt=True)
    ]
    
    for element in name_sources:
        if element:
            name = element.get('alt') if element.name == 'img' else element.text.strip()
            if name and name.upper() != 'TBD':
                return name
    
    tbd = team_div.find('abbr', title='To Be Decided')
    return tbd.text.strip() if tbd else 'TBD'

def export_to_csv(tournaments, filename='tournaments.csv'):
    """Export tournament data to CSV file"""
    if not tournaments:
        print("No data to export")
        return
        
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=tournaments[0].keys())
        writer.writeheader()
        writer.writerows(tournaments)
    print(f"Data exported to {filename}")

# Main script
url = "https://liquipedia.net/rainbowsix/S-Tier_Tournaments"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
current_date = datetime.now()

tournaments = []
for row in soup.find_all('div', class_=['gridRow', 'gridRow tournament-highlighted-bg']):
    tournament_div = row.find('div', class_='Tournament')
    if not tournament_div:
        continue
        
    try:
        # Extract basic info
        name_links = tournament_div.find_all('a')
        name = name_links[-1].text.strip() if name_links else 'N/A'
        
        # Date handling and filtering
        date_div = row.find('div', class_='Date')
        date_str = date_div.text.strip() if date_div else 'N/A'
        date_obj = parse_tournament_date(date_str)
        
        # Skip if no date or tournament is in the future
        if not date_obj or date_obj > current_date:
            continue
            
        # Extract other details
        prize = (row.find('div', class_='Prize').text.strip() 
                if row.find('div', class_='Prize') else 'N/A')
        prize = 'N/A' if prize in ('', 'Blank') else prize
        
        location = clean_location(
            row.find('div', class_='Location').text.strip() 
            if row.find('div', class_='Location') else 'N/A'
        )
        
        participants = (row.find('div', class_='PlayerNumber').text.strip().split()[0] 
                      if row.find('div', class_='PlayerNumber') else 'N/A')
        
        # Extract teams
        winner = extract_team_name(row.find('div', class_='FirstPlace'))
        runner_up = extract_team_name(row.find('div', class_='SecondPlace'))
        
        # Only include if winner is determined (not TBD)
        if winner == 'TBD':
            continue
            
        tournaments.append({
            'name': name,
            'date': date_obj.strftime("%Y-%m-%d"),
            'year': date_obj.year,
            'prize': prize,
            'location': location,
            'participants': participants,
            'winner': winner,
            'runner_up': runner_up,
            'url': f"https://liquipedia.net{name_links[-1]['href']}" if name_links else 'N/A'
        })
    except Exception as e:
        print(f"Skipping row due to error: {str(e)[:100]}...")
        continue

# Sort by date (newest first)
tournaments.sort(key=lambda x: x['date'], reverse=True)

# Print summary
print(f"\nFound {len(tournaments)} completed Rainbow Six Siege tournaments (all years)")
print("Sample of tournaments:")
for t in tournaments[:10]:  # Show first 10 as sample
    print(f"\n{t['name']} ({t['date']})")
    print(f"Winner: {t['winner']} | Runner-up: {t['runner_up']}")
    print(f"Location: {t['location']} | Prize: {t['prize']}")

# Export to CSV
export_to_csv(tournaments)

print(f"\nNote: Skipped {len(soup.find_all('div', class_='gridRow')) - len(tournaments)} upcoming/unconfirmed tournaments")