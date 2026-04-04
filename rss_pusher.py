import re

URL_REGEX = re.compile(r'https?://[^\s"'<>]+')
HREF_REGEX = re.compile(r'href=["']([^"']+)')

class YourRSSClass:
    def extract_entry_link(self, entry):
        # Scan for links in description, summary, content, and title first
        potential_links = []
        # Assuming entry.description contains the HTML content
        content_match = HREF_REGEX.findall(entry.content)
        potential_links.extend(content_match)

        # Then check entry.links
        for link in entry.links:
            potential_links.append(link.href)

        # Then check id, guid, link
        fallback_links = [entry.id, entry.guid, entry.link]
        potential_links.extend(fallback_links)

        # Scoring logic here, avoiding timeline item links
        best_link = None
        best_score = -float('inf')
        for link in potential_links:
            score = self.score_link(link)
            # Extra penalty for timeline item links
            if '/user/[^/]+/timeline/\d+' in link:
                score -= 10  # Example penalty
            if score > best_score:
                best_score = score
                best_link = link

        return best_link

    def score_link(self, link):
        # Your scoring logic
        return 0  # Dummy logic