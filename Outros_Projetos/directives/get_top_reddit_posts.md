# Directive: Get Top Reddit Posts

**Goal**: Fetch the top posts from Reddit (default: /r/all) to see what's trending.

**Inputs**:
- Limit: Number of posts to fetch (default: 5)
- Subreddit: The subreddit to fetch from (default: 'all')

**Outputs**:
- A JSON file in `.tmp/top_reddit_posts.json` containing the post titles, scores, and URLs.
- Terminal output with a formatted list.

**Execution Script**: `execution/get_reddit_posts.py`

**Edge Cases**:
- Reddit blocks default HTTP client user-agents. Use a custom realistic User-Agent.
- Handle potential network errors gracefully.
