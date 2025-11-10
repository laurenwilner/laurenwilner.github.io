#!/usr/bin/env python3
"""
Extract teaching assistant positions from CV LaTeX file and update courses.md page.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict

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
    value = re.sub(r'\\leftskip=0\.25cm', '', value)
    value = re.sub(r'\\\\', '', value)
    
    # Remove smart quotes
    value = value.replace('"', '"').replace('"', '"')
    value = value.replace(''', "'").replace(''', "'")
    
    # Remove standalone braces
    value = re.sub(r'\{([^*{}]+)\}', r'\1', value)
    
    return value.strip()

def parse_course_item(item_block: str) -> Dict[str, str]:
    """Parse a single course item including its description."""
    # Pattern: \item Course, Role. Date. Location.\\ \parbox{description}
    
    # Extract description from parbox
    description_match = re.search(r'\\parbox\[t\]\{\\linewidth\}.*?\\textit\{([^}]+)\}', item_block, re.DOTALL)
    description = description_match.group(1) if description_match else ''
    description = clean_latex(description)
    
    # Get the main item line (before parbox)
    main_line = item_block.split('\\parbox')[0] if '\\parbox' in item_block else item_block
    main_line = main_line.replace('\\item', '').strip()
    
    cleaned = clean_latex(main_line)
    
    # Extract date/term (Spring 2024, Winter 2024, Fall 2014, August 12-13, 2025, etc.)
    date_match = re.search(r'((?:Spring|Winter|Fall|Summer|August|January|February|March|April|May|June|July|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4}|(?:Spring|Winter|Fall|Summer)\s+\d{4})', cleaned)
    date = date_match.group(1) if date_match else ''
    
    # Extract institution (University of Washington, Tufts University School of Medicine, etc.)
    # Look for common patterns: "University of...", "School of...", "Tufts University..."
    institution_match = re.search(r'((?:Tufts University|University of|School of)[^,\.]+(?:School of[^,\.]+)?)', cleaned)
    institution = institution_match.group(1).rstrip(',').strip() if institution_match else ''
    
    # Extract location at the end (City, ST or Virtual)
    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2}|Virtual)(?:\.|$)', cleaned)
    location = ''
    if location_match:
        city = location_match.group(1)
        state = location_match.group(2)
        location = f"{city}, {state}" if state != 'Virtual' else 'Virtual'
    
    # Remove date, institution, and location from cleaned
    if date_match:
        cleaned = re.sub(re.escape(date_match.group(0)), '', cleaned)
    if institution_match:
        cleaned = re.sub(re.escape(institution_match.group(0)), '', cleaned)
    if location_match:
        cleaned = re.sub(re.escape(location_match.group(0)), '', cleaned)
    
    # Extract role (Teaching Assistant, TA) - handle "TA" at the start
    role = ''
    course = cleaned
    
    # Check if it starts with "TA"
    if re.match(r'^TA\s+', cleaned):
        role = 'TA'
        course = re.sub(r'^TA\s+', '', cleaned)
        # For TA entries, course name is everything before the first period
        course = course.split('.', 1)[0].strip()
    else:
        # Look for "Teaching Assistant" in the text
        role_match = re.search(r'(Teaching\s+Assistant)', cleaned)
        if role_match:
            role = role_match.group(1)
            course = cleaned[:role_match.start()].rstrip(',').strip()
        else:
            # No role found, try to extract course name (everything before first comma or period)
            parts = course.split(',', 1)
            course = parts[0].strip() if parts else course
            course = course.rstrip('.').strip()
    
    # Clean up course name - remove trailing commas, periods, and "Tufts" if it's just a duplicate
    course = course.rstrip(',').rstrip('.').strip()
    # Remove "Tufts" if it appears at the end (duplicate from course name)
    course = re.sub(r'\s+Tufts\.?\s*$', '', course)
    # Remove double periods and commas
    course = re.sub(r'\.\s*\.', '.', course)
    course = re.sub(r',\s*,', ',', course)
    course = course.strip()
    
    return {
        'course': course,
        'role': role,
        'date': date,
        'institution': institution,
        'location': location,
        'description': description
    }

def extract_courses(cv_path: Path) -> List[Dict[str, str]]:
    """Extract teaching assistant positions section from CV."""
    with cv_path.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the Teaching Assistant Positions section
    ta_section = re.search(
        r'\\underline\{Teaching Assistant Positions\}.*?\\begin\{enumerate\}(.*?)\\end\{enumerate\}',
        content,
        re.DOTALL
    )
    
    if not ta_section:
        return []
    
    enumerate_content = ta_section.group(1)
    
    # Extract each \item including its parbox description
    # Split by \item to get all items
    items = re.split(r'\\item\s+', enumerate_content)
    courses = []
    
    for item_block in items[1:]:  # Skip first empty element
        item_block = item_block.strip()
        # Remove everything after the next \item or \end{enumerate}
        # But keep the parbox content
        next_item_pos = item_block.find('\\item')
        end_pos = item_block.find('\\end{enumerate}')
        if next_item_pos != -1 and (end_pos == -1 or next_item_pos < end_pos):
            item_block = item_block[:next_item_pos]
        elif end_pos != -1:
            item_block = item_block[:end_pos]
        
        if item_block:
            parsed = parse_course_item(item_block)
            if parsed['course']:
                courses.append(parsed)
    
    return courses

def format_courses_markdown(courses: List[Dict[str, str]]) -> str:
    """Format courses as markdown matching presentations format."""
    if not courses:
        return ""
    
    # Start with CSS style matching presentations
    content = "<style>\n"
    content += ".presentation-item { margin-bottom: 1rem; font-size: 0.9em; }\n"
    content += ".presentation-item h2 { font-size: 1.1em; margin-top: 1.5rem; margin-bottom: 0.5rem; }\n"
    content += ".presentation-item p { margin: 0.25rem 0; }\n"
    content += "</style>\n\n"
    
    # Format each course entry
    for course in courses:
        course_name = course['course']
        
        # Build location string
        location_parts = []
        if course['institution']:
            location_parts.append(course['institution'])
        if course['location']:
            location_parts.append(course['location'])
        location_str = ', '.join(location_parts) if location_parts else ""
        
        # Build role/date string
        role_date_parts = []
        if course['role']:
            role_date_parts.append(course['role'])
        if course['date']:
            role_date_parts.append(course['date'])
        role_date_str = ', '.join(role_date_parts) if role_date_parts else ""
        
        content += f"<div class=\"presentation-item\">\n"
        content += f"<h2>{course_name}</h2>\n"
        
        if role_date_str:
            content += f"<p><strong>{role_date_str}</strong></p>\n"
        
        if location_str:
            content += f"<p>{location_str}</p>\n"
        
        if course['description']:
            content += f"<p>{course['description']}</p>\n"
        
        content += "</div>\n\n"
    
    return content

def update_courses_page(courses: List[Dict[str, str]], courses_md_path: Path):
    """Update the courses.md file with the extracted courses."""
    content = format_courses_markdown(courses)
    
    if not courses_md_path.exists():
        print(f"Warning: {courses_md_path} not found, creating new file")
        courses_md_path.write_text(content, encoding='utf-8')
        return
    
    # Replace entire content
    courses_md_path.write_text(content, encoding='utf-8')

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cv_to_courses.py <cv_tex_file> <courses_md_file>")
        sys.exit(1)
    
    cv_path = Path(sys.argv[1])
    courses_md_path = Path(sys.argv[2])
    
    if not cv_path.exists():
        print(f"Error: CV file not found at {cv_path}")
        sys.exit(1)
    
    courses = extract_courses(cv_path)
    print(f"Found {len(courses)} teaching positions")
    
    update_courses_page(courses, courses_md_path)
    print(f"Updated {courses_md_path}")

if __name__ == '__main__':
    main()

