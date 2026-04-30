import urllib.request
import urllib.error
import json
import os
import sys

def get_top_posts(limit=5):
    # Fetching from the frontpage (r/all)
    url = f"https://www.reddit.com/r/all/top.json?limit={limit}"
    
    # Custom user agent to avoid 429 Too Many Requests or 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            posts = []
            print(f"Top {limit} Posts from Reddit Frontpage (/r/all):\n" + "="*45)
            
            children = data.get('data', {}).get('children', [])
            for i, child in enumerate(children):
                post = child.get('data', {})
                title = post.get('title', 'No Title')
                score = post.get('score', 0)
                permalink = post.get('permalink', '')
                full_url = f"https://www.reddit.com{permalink}"
                
                safe_title = title.encode("ascii", "ignore").decode()
                print(f"{i+1}. {safe_title} (Score: {score})")
                print(f"   URL: {full_url}\n")
                
                posts.append({
                    'title': title,
                    'score': score,
                    'url': full_url
                })
                
            # Architecture Rule: Save intermediate files to .tmp/
            # Architecture Rule: Do not save to local folders unless it's .tmp/
            tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_file = os.path.join(tmp_dir, 'top_reddit_posts.json')
            
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=4, ensure_ascii=False)
                
            print(f"[Success] Data successfully saved to intermediate file: {tmp_file}")
            
    except urllib.error.HTTPError as e:
        print(f"[Error] HTTP Error: {e.code} - {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[Error] URL Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Failed to fetch or parse data: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    limit = 5
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
            
    get_top_posts(limit=limit)
