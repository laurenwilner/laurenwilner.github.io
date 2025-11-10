#!/usr/bin/env python3
"""
Convert BibTeX file to Markdown format for publications page.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

def clean_latex(text: str) -> str:
    """Clean LaTeX commands from text, converting to Markdown."""
    value = text
    
    # Handle formatting commands - process from innermost to outermost
    # First handle \textbf{...} - need to escape backslash properly
    max_iterations = 30
    for _ in range(max_iterations):
        # Match \textbf{content} - the backslash needs to be escaped in the pattern
        new_value = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', value)
        if new_value == value:
            break
        value = new_value
    
    for _ in range(max_iterations):
        new_value = re.sub(r'\\textit\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'*\1*', value)
        if new_value == value:
            break
        value = new_value
        new_value2 = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', value)
        if new_value2 != value:
            value = new_value2
    
    # Handle text commands
    value = re.sub(r'\\text\{([^}]+)\}', r'\1', value)
    
    # Handle simple escapes
    value = re.sub(r'\\&', '&', value)
    value = re.sub(r'\\%', '%', value)
    value = re.sub(r'\\#', '#', value)
    value = re.sub(r'\\\$', '$', value)
    value = re.sub(r'\\_', '_', value)
    value = re.sub(r'\\~', '~', value)
    value = re.sub(r'\\{', '{', value)
    value = re.sub(r'\\}', '}', value)
    
    # Remove any remaining standalone braces (but preserve markdown formatting)
    # Only remove braces that don't contain markdown stars
    value = re.sub(r'\{([^*{}]+)\}', r'\1', value)
    
    return value

def extract_braced_content(text: str, start_pos: int) -> tuple[str, int]:
    """Extract content from braces, handling nested braces. Returns (content, end_pos)."""
    if start_pos >= len(text) or text[start_pos] != '{':
        return '', start_pos
    
    depth = 0
    start = start_pos + 1
    i = start_pos
    
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    
    # Unmatched brace
    return text[start:], len(text)

def parse_bibtex_entry(entry_text: str) -> Optional[Dict[str, str]]:
    """Parse a single BibTeX entry."""
    # Extract entry type and key
    type_match = re.match(r'@(\w+)\{([^,]+),', entry_text)
    if not type_match:
        return None
    
    entry_type = type_match.group(1)
    entry_key = type_match.group(2)
    
    # Extract fields - handle nested braces properly
    fields = {}
    pos = entry_text.find(',', entry_text.find('{'))
    
    while pos < len(entry_text):
        # Find next field name
        field_match = re.search(r'(\w+)\s*=\s*', entry_text[pos:])
        if not field_match:
            break
        
        field_name = field_match.group(1).lower()
        field_start = pos + field_match.end()
        
        # Skip whitespace
        while field_start < len(entry_text) and entry_text[field_start] in ' \t\n':
            field_start += 1
        
        if field_start >= len(entry_text):
            break
        
        # Extract braced content
        if entry_text[field_start] == '{':
            value, next_pos = extract_braced_content(entry_text, field_start)
            fields[field_name] = clean_latex(value)
            pos = next_pos
        else:
            # Handle quoted strings or other formats
            match = re.search(r'["\']([^"\']+)["\']', entry_text[field_start:])
            if match:
                value = match.group(1)
                fields[field_name] = clean_latex(value)
                pos = field_start + match.end()
            else:
                # Try to find next comma or closing brace
                next_comma = entry_text.find(',', field_start)
                next_brace = entry_text.find('}', field_start)
                if next_comma != -1 and (next_brace == -1 or next_comma < next_brace):
                    value = entry_text[field_start:next_comma].strip()
                    fields[field_name] = clean_latex(value)
                    pos = next_comma + 1
                else:
                    break
    
    return {
        'type': entry_type,
        'key': entry_key,
        'fields': fields
    }

def format_author(author_str: str, max_authors: int = 20) -> str:
    """Format author string, preserving bold formatting.
    If more than max_authors, show first author then 'et al.'"""
    # Split by ' and ' or ' and'
    authors = re.split(r'\s+and\s+', author_str)
    formatted = []
    for author in authors:
        author = author.strip()
        # Handle "Last, First" or "First Last" format
        if ',' in author:
            parts = [p.strip() for p in author.split(',', 1)]
            if len(parts) == 2:
                formatted.append(f"{parts[1]} {parts[0]}")
            else:
                formatted.append(author)
        else:
            formatted.append(author)
    
    # Limit to max_authors, add "et al." if more
    if len(formatted) > max_authors:
        return ', '.join(formatted[:1]) + ' et al.'
    else:
        return ', '.join(formatted)

def format_entry(entry: Dict[str, str]) -> str:
    """Format a BibTeX entry as Markdown."""
    fields = entry['fields']
    
    # Get title
    title = fields.get('title', 'Untitled')
    title = title.strip()
    if not title.startswith('**'):
        title = f"**{title}**"
    
    # Get authors
    authors = fields.get('author', '')
    if authors:
        authors = format_author(authors, max_authors=20)
    
    # Get journal/booktitle
    journal = fields.get('journal', '') or fields.get('booktitle', '')
    
    # Get year
    year = fields.get('year', '')
    
    # Get volume, number, pages
    volume = fields.get('volume', '')
    number = fields.get('number', '')
    pages = fields.get('pages', '')
    
    # Build citation
    parts = []
    
    if authors:
        parts.append(authors)
    
    parts.append(title)
    
    if journal:
        parts.append(f"*{journal}*")
    
    if year:
        parts.append(f"{year}")
    
    if volume:
        if number:
            parts.append(f"{volume}({number})")
        else:
            parts.append(f"{volume}")
    
    if pages:
        parts.append(f"pp. {pages}")
    
    # Add DOI/URL if available
    doi = fields.get('doi', '')
    url = fields.get('url', '')
    
    citation = '. '.join(parts)
    
    # Add DOI/URL link
    if doi:
        citation += f". doi: [{doi}](https://doi.org/{doi})"
    elif url:
        citation += f". [{url}]({url})"
    
    return citation

def parse_bibtex_file(bibtex_path: Path) -> List[Dict[str, str]]:
    """Parse a BibTeX file and return list of entries."""
    content = bibtex_path.read_text(encoding='utf-8')
    
    # Split into entries (entries start with @)
    entries = []
    current_entry = []
    in_entry = False
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('%'):
            continue
        
        if line.startswith('@'):
            if current_entry:
                entry = parse_bibtex_entry('\n'.join(current_entry))
                if entry:
                    entries.append(entry)
            current_entry = [line]
            in_entry = True
        elif in_entry:
            current_entry.append(line)
            if line.endswith('}') and '{' not in line[line.rfind('}'):]:
                # End of entry
                entry = parse_bibtex_entry('\n'.join(current_entry))
                if entry:
                    entries.append(entry)
                current_entry = []
                in_entry = False
    
    # Handle last entry
    if current_entry:
        entry = parse_bibtex_entry('\n'.join(current_entry))
        if entry:
            entries.append(entry)
    
    return entries

def generate_markdown(entries: List[Dict[str, str]], header: str = "[Google Scholar](https://scholar.google.com/citations?hl=en&user=rLX9LVYAAAAJ&view_op=list_works&sortby=pubdate)\n\n") -> str:
    """Generate Markdown from BibTeX entries."""
    # Month name to number mapping
    month_map = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    
    # Sort by year-month (newest first), then by title
    def sort_key(entry):
        year = entry['fields'].get('year', '0')
        month = entry['fields'].get('month', '')
        
        try:
            year_int = int(year)
        except:
            year_int = 0
        
        # Convert month to number
        month_int = 0
        if month:
            month_lower = month.lower().strip()
            # Remove braces if present
            month_lower = month_lower.strip('{}')
            # Try to parse as number first
            try:
                month_int = int(month_lower)
            except:
                # Try month name
                month_int = month_map.get(month_lower, 0)
        
        title = entry['fields'].get('title', '').lower()
        # Sort by -year, -month (newest first), then title
        return (-year_int, -month_int, title)
    
    entries.sort(key=sort_key)
    
    lines = [header]
    for entry in entries:
        formatted = format_entry(entry)
        lines.append(formatted)
        lines.append('')  # Blank line between entries
    
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: bibtex_to_markdown.py <input.bib> <output.md>")
        sys.exit(1)
    
    bibtex_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not bibtex_path.exists():
        print(f"Error: {bibtex_path} not found")
        sys.exit(1)
    
    entries = parse_bibtex_file(bibtex_path)
    markdown = generate_markdown(entries)
    
    output_path.write_text(markdown, encoding='utf-8')
    print(f"Generated {len(entries)} publications in {output_path}")

if __name__ == '__main__':
    main()

