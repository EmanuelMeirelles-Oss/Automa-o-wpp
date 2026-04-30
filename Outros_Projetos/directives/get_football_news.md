# Directive: Football Weekly News Automation

**Goal**: Fetch the top 5 most important football news of the week across different categories (national, international, transfers) and publish them to a static site.

**Inputs**:
- RSS Feeds from major sports news outlets (e.g. ESPN, BBC, GE).
- Number of news limits (default: 5).

**Outputs**:
- `logs/automation.log`: detailed step-by-step logs of the automation execution.
- `.tmp/football_news.json`: Intermediate data extracted from the feeds.
- `site/data.json`: The historical record of all news, with the current week at the top.
- `site/index.html`, `site/app.css`, `site/app.js`: Static SPA to visualize the data.

**Execution Script**: `execution/football_news_bot.py`

**Edge Cases**:
- RSS Feed parsing errors should be logged correctly.
- If less than 5 news are found for the week, format what is available gracefully.
