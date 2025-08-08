class SummaryService:
    """Generates summaries from processed transcripts."""

    def generate(self, lines: list[str]) -> dict:
        """Return a naive summary consisting of line count and first line."""
        return {
            'line_count': len(lines),
            'first_line': lines[0] if lines else ''
        }
