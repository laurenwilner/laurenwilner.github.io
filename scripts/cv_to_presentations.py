#!/usr/bin/env python3
"""
Extract presentations from CV LaTeX file and generate markdown pages.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

def clean_latex(text: str) -> str:
    """Clean LaTeX commands from text, converting to Markdown."""
    value = text
    
    # Handle formatting commands
    max_iterations = 30
    for _ in range(max_iterations):
        new_value = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', value)
        if new_value == value:
            break
        value = new_value
    
    for _ in range(max_iterations):
        new_value = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', value)
        if new_value == value:
            break
        value = new_value
    
    # Handle math mode - preserve subscripts
    value = re.sub(r'\$_{([^}]+)}\$', r'<sub>\1</sub>', value)
    value = re.sub(r'PM\$_{2\.5}', 'PM<sub>2.5</sub>', value)
    value = re.sub(r'\$([^$]+)\$', r'\1', value)
    value = re.sub(r'\\textsubscript\{([^}]+)\}', r'<sub>\1</sub>', value)
    
    # Handle simple escapes
    value = re.sub(r'\\&', '&', value)
    value = re.sub(r'\\%', '%', value)
    value = re.sub(r'\\#', '#', value)
    value = re.sub(r'\\\$', '$', value)
    value = re.sub(r'\\_', '_', value)
    value = re.sub(r'\\hfill', '', value)
    
    # Remove any remaining standalone braces
    value = re.sub(r'\{([^*{}]+)\}', r'\1', value)
    
    return value.strip()

def parse_presentation_line(line: str) -> Dict[str, str]:
    """Parse a single presentation line from the CV."""
    # Pattern: \textbf{Wilner LB}, coauthors. Title. \textit{Conference}. Location \hfill Year
    original_line = line
    
    # Extract year (last thing, after \hfill)
    year_match = re.search(r'\\hfill\s+(\d{4})', line)
    year = year_match.group(1) if year_match else ''
    
    # Extract conference (in \textit{...})
    conference_match = re.search(r'\\textit\{([^}]+)\}', line)
    conference = conference_match.group(1) if conference_match else ''
    conference = conference.rstrip('.').strip()
    
    # Extract location (after conference, before \hfill, pattern: City, ST or City, Country)
    # Remove conference and year first to isolate location
    temp_line = re.sub(r'\\textit\{[^}]+\}', '', line)
    temp_line = re.sub(r'\\hfill\s+\d{4}', '', temp_line)
    # Location is typically at the end: City, ST or City, Country
    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$', temp_line)
    location = ''
    if location_match:
        city = location_match.group(1)
        state_country = location_match.group(2)
        location = f"{city}, {state_country}"
    
    # Now extract authors and title from the beginning
    # Pattern: Authors. Title. Conference. Location
    # Remove conference and location markers first
    work_line = line
    # Remove \textit{Conference}.
    if conference_match:
        work_line = re.sub(r'\\textit\{[^}]+\}\.?', '', work_line)
    # Remove location (we already extracted it)
    if location:
        work_line = re.sub(re.escape(location), '', work_line)
    # Remove year
    work_line = re.sub(r'\\hfill\s+\d{4}', '', work_line)
    
    # Clean LaTeX but preserve structure
    # Split by periods - first is authors, second is title
    # But need to be careful about periods in the title
    # Authors end with first period after \textbf{...}
    authors_match = re.search(r'\\textbf\{([^}]+)\}([^.]*)\.', work_line)
    if authors_match:
        authors_start = authors_match.group(1)
        authors_rest = authors_match.group(2)
        authors = clean_latex(f"\\textbf{{{authors_start}}}{authors_rest}")
        # Get everything after authors period as title
        title_start = work_line.find('.', work_line.find('\\textbf'))
        if title_start != -1:
            title_text = work_line[title_start + 1:]
            # Remove any trailing location or conference remnants
            title_text = re.sub(r'\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*[A-Z]{2}?\s*$', '', title_text)
            title = clean_latex(title_text).rstrip('.').strip()
        else:
            title = ''
    else:
        # Fallback: split by first period
        cleaned = clean_latex(work_line)
        parts = cleaned.split('.', 1)
        if len(parts) >= 2:
            authors = parts[0].strip()
            title = parts[1].strip().rstrip('.').strip()
        else:
            authors = ''
            title = cleaned.strip()
    
    return {
        'authors': authors,
        'title': title,
        'conference': conference,
        'location': location,
        'year': year
    }

def extract_presentations(cv_path: Path) -> List[Dict[str, str]]:
    """Extract presentations section from CV."""
    with cv_path.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the presentations section
    section_match = re.search(r'\\section\{Conference presentations and posters\}(.*?)(?=\\section\{|\%---|\Z)', content, re.DOTALL)
    if not section_match:
        return []
    
    section_content = section_match.group(1)
    
    # Split by lines and parse each presentation
    presentations = []
    for line in section_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('%'):
            continue
        
        # Check if it's a presentation line (contains \textbf for author)
        if '\\textbf{' in line or 'Wilner' in line:
            parsed = parse_presentation_line(line)
            if parsed['year']:  # Only include if we found a year
                presentations.append(parsed)
    
    return presentations

def generate_presentations_markdown(presentations: List[Dict[str, str]], output_dir: Path):
    """Generate markdown files for presentations, preserving CV order."""
    # Generate a main index page
    index_content = "# Presentations\n\n"
    index_content += "<style>\n"
    index_content += ".presentation-item { margin-bottom: 1rem; font-size: 0.9em; }\n"
    index_content += ".presentation-item h2 { font-size: 1.1em; margin-top: 1.5rem; margin-bottom: 0.5rem; }\n"
    index_content += ".presentation-item p { margin: 0.25rem 0; }\n"
    index_content += "</style>\n\n"
    
    # Keep presentations in the order they appear in the CV (already in order)
    for pres in presentations:
        conference = pres['conference']
        year = pres['year']
        # Convert markdown bold to HTML in authors
        authors_html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', pres['authors'])
        
        index_content += f"<div class=\"presentation-item\">\n"
        index_content += f"<h2>{conference} ({year})</h2>\n"
        index_content += f"<p><strong>{pres['title']}</strong></p>\n"
        index_content += f"<p>{authors_html}</p>\n"
        if pres['location']:
            index_content += f"<p><em>{pres['location']}</em></p>\n"
        index_content += "</div>\n\n"
    
    # Write main index
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.md").write_text(index_content, encoding='utf-8')

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cv_to_presentations.py <cv_tex_file> <output_directory>")
        sys.exit(1)
    
    cv_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not cv_path.exists():
        print(f"Error: CV file not found at {cv_path}")
        sys.exit(1)
    
    presentations = extract_presentations(cv_path)
    print(f"Found {len(presentations)} presentations")
    
    generate_presentations_markdown(presentations, output_dir)
    print(f"Generated presentation pages in {output_dir}")

if __name__ == '__main__':
    main()

