# Directive: Update 01dosAnimes Data

**Goal**: Fetch the top posts from Reddit (r/dragonball, r/dbz, r/anime), NewsAPI.org, and AnimeNewsNetwork RSS, deduplicate them based on their URLs, and save them as intermediate data or push to Supabase for the 01dosAnimes web application.

**Inputs**:
- `.env` file credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, NEWS_API_KEY, SUPABASE keys)

**Outputs**:
- Fetches data and saves an intermediate file: `.tmp/01dosanimes_news.json`
- (Optional, if DB is ready) Pushes the final deduplicated news to `noticias` table in Supabase.

**Execution Script**: `execution/01dosanimes_bot.py`

**Edge Cases**:
- Reddit API limit rates.
- Empty or invalid articles from NewsAPI (ensure 'title' and 'url' exist and are valid strings).
- Duplicate articles from the same source.
