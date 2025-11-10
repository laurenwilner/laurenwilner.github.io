#!/usr/bin/env python3
"""
Extract workshops from CV LaTeX file and update workshops.md page.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

def clean_latex(text: str) -> str:
    """Clean LaTeX commands from text."""
    value = text
    
    # Remove LaTeX commands
    value = re.sub(r'\\textbf\{([^}]+)\}', r'\1', value)
    value = re.sub(r'\\textit\{([^}]+)\}', r'\1', value)
    value = re.sub(r'\\underline\{([^}]+)\}', r'\1', value)
    value = re.sub(r'\\&', '&', value)
    value = re.sub(r'\\%', '%', value)
    value = re.sub(r'\\#', '#', value)
    value = re.sub(r'\\\$', '$', value)
    value = re.sub(r'\\_', '_', value)
    value = re.sub(r'\\hfill', '', value)
    value = re.sub(r'\\parbox\[t\]\{\\linewidth\}[^}]*\{([^}]+)\}', r'\1', value)
    
    # Remove smart quotes - use replace instead of regex for single quotes
    value = value.replace('"', '"').replace('"', '"')
    value = value.replace(''', "'").replace(''', "'")
    
    # Remove standalone braces
    value = re.sub(r'\{([^*{}]+)\}', r'\1', value)
    
    return value.strip()

def parse_workshop_item(line: str) -> Dict[str, str]:
    """Parse a single workshop item from enumerate."""
    # Pattern: \item Location, Role, "Title." Date. Location
    # Example: \item Dr. Joan Casey's research lab at University of Washington, Workshop Instructor, "Git and GitHub for Public Health." November 2025. Seattle, WA
    
    cleaned = clean_latex(line)
    
    # Extract date (look for month year pattern or date pattern, including "May 3, 2025")
    date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})', cleaned)
    date = date_match.group(1) if date_match else ''
    
    # Extract location at the end (City, ST or City, Country or Virtual)
    # Try to match location pattern - could be at the very end or before a period
    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2}|Virtual)(?:\.|$)', cleaned)
    location = ''
    if location_match:
        city = location_match.group(1)
        state = location_match.group(2)
        location = f"{city}, {state}" if state != 'Virtual' else 'Virtual'
    
    # Remove date and location from cleaned
    if date_match:
        cleaned = re.sub(re.escape(date_match.group(0)), '', cleaned)
    if location_match:
        cleaned = re.sub(re.escape(location_match.group(0)), '', cleaned)
    
    # Extract role (Workshop Instructor, Workshop Co-Instructor)
    role_match = re.search(r'(Workshop\s+(?:Co-)?Instructor)', cleaned)
    role = role_match.group(1) if role_match else ''
    
    # Extract organization/location (everything before the role)
    if role_match:
        org = cleaned[:role_match.start()].rstrip(',').strip()
    else:
        # Try to find organization (everything before first comma or quote)
        parts = cleaned.split(',', 1)
        org = parts[0].strip() if parts else cleaned
    
    # Extract title (in quotes)
    title_match = re.search(r'"([^"]+)"', cleaned)
    title = title_match.group(1) if title_match else ''
    
    return {
        'organization': org,
        'role': role,
        'title': title,
        'date': date,
        'location': location
    }

def extract_workshops(cv_path: Path) -> List[Dict[str, str]]:
    """Extract workshops section from CV."""
    with cv_path.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the workshops section (under \underline{Workshops})
    # Look for the enumerate environment after \underline{Workshops}
    workshop_section = re.search(
        r'\\underline\{Workshops\}.*?\\begin\{enumerate\}(.*?)\\end\{enumerate\}',
        content,
        re.DOTALL
    )
    
    if not workshop_section:
        return []
    
    enumerate_content = workshop_section.group(1)
    
    # Extract each \item - split by \item to get all items
    items = re.split(r'\\item\s+', enumerate_content)
    workshops = []
    for item_text in items[1:]:  # Skip first empty element
        item_text = item_text.strip()
        # Remove everything after the next \item or \end{enumerate}
        item_text = re.sub(r'(?=\\item|\\end\{enumerate\}).*$', '', item_text, flags=re.DOTALL)
        # Remove newlines and extra whitespace
        item_text = ' '.join(item_text.split())
        if item_text:
            parsed = parse_workshop_item(item_text)
            if parsed['organization']:
                workshops.append(parsed)
    
    return workshops

def format_workshop_list(workshops: List[Dict[str, str]]) -> str:
    """Format workshops as a markdown list, grouped by organization."""
    if not workshops:
        return ""
    
    # Group by organization
    grouped = defaultdict(list)
    for workshop in workshops:
        org = workshop['organization']
        # Clean up organization name (remove trailing comma)
        org = org.rstrip(',').strip()
        grouped[org].append(workshop)
    
    # Format each organization's workshops
    lines = []
    for org in sorted(grouped.keys()):
        org_workshops = grouped[org]
        # Format dates more nicely
        dates = []
        for w in org_workshops:
            if w['date']:
                # Simplify date format - remove day if present for consistency
                date = w['date']
                # Convert "June 10, 2025" to "June 2025" for consistency
                date_simple = re.sub(r'(\w+)\s+\d{1,2},?\s+(\d{4})', r'\1 \2', date)
                dates.append(date_simple)
        
        if len(dates) > 1:
            # Group by year if multiple dates
            dates_str = ', '.join(sorted(set(dates), key=lambda x: (
                ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December'].index(x.split()[0]) if x.split()[0] in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] else 0,
                int(x.split()[-1])
            ), reverse=True))
            lines.append(f"- {org} ({dates_str})")
        elif len(dates) == 1:
            lines.append(f"- {org} ({dates[0]})")
        else:
            lines.append(f"- {org}")
    
    return '\n'.join(lines)

def update_workshops_page(workshops: List[Dict[str, str]], workshops_md_path: Path):
    """Update the workshops.md file with the extracted workshops list."""
    if not workshops_md_path.exists():
        print(f"Warning: {workshops_md_path} not found, creating new file")
        content = f"**Git and GitHub for Public Health**\n\n"
        content += f"*Co-developed with Dr. Corinne Riddell (UC Berkeley)*\n\n"
        content += f"This workshop has been taught at the following locations:\n\n"
        content += format_workshop_list(workshops)
        workshops_md_path.write_text(content, encoding='utf-8')
        return
    
    # Read existing content
    content = workshops_md_path.read_text(encoding='utf-8')
    
    # Find the section to replace (between "This workshop has been taught" and the next section)
    pattern = r'(This workshop has been taught at the following locations:\s*\n\n)(.*?)(\n\n\n)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Replace the list section
        new_list = format_workshop_list(workshops)
        new_content = content[:match.start(2)] + new_list + content[match.end(2):]
        workshops_md_path.write_text(new_content, encoding='utf-8')
    else:
        # Try alternative pattern
        pattern2 = r'(This workshop has been taught at the following locations:\s*\n\n)(.*?)(\n\nOpen source)'
        match2 = re.search(pattern2, content, re.DOTALL)
        if match2:
            new_list = format_workshop_list(workshops)
            new_content = content[:match2.start(2)] + new_list + content[match2.end(2):]
            workshops_md_path.write_text(new_content, encoding='utf-8')
        else:
            print(f"Warning: Could not find section to replace in {workshops_md_path}")
            print("Please manually update the workshops list.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cv_to_workshops.py <cv_tex_file> <workshops_md_file>")
        sys.exit(1)
    
    cv_path = Path(sys.argv[1])
    workshops_md_path = Path(sys.argv[2])
    
    if not cv_path.exists():
        print(f"Error: CV file not found at {cv_path}")
        sys.exit(1)
    
    workshops = extract_workshops(cv_path)
    print(f"Found {len(workshops)} workshops")
    
    update_workshops_page(workshops, workshops_md_path)
    print(f"Updated {workshops_md_path}")

if __name__ == '__main__':
    main()

