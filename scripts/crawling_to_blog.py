
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# Configuration
BASE_URL = "https://www.fbo.or.kr"
LIST_URL = "https://www.fbo.or.kr/info/bbs/RepdList.do?menuId=080030&schNtceClsfCd=B01010200"
BLOG_DIR = "blog"
TEMPLATE_PATH = "blog_template.html"

def get_article_links():
    print(f"Scanning list: {LIST_URL}")
    links = []
    try:
        response = requests.get(LIST_URL)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.select("td.subject > a")
        for item in items:
            href = item.get('href')
            if href and 'NoticeView.do' in href:
                full_link = f"/info/bbs/{href}"
                links.append(full_link)
                
        print(f"Found {len(links)} articles.")
        return links
    except Exception as e:
        print(f"Error scanning list: {e}")
        return []

def adapt_text(raw_text):
    """
    Advanced heuristic adaptation to structure text into Blog format:
    [Intro Box] -> [Subheadings/Body]
    """
    # 1. Basic Cleanup
    text = raw_text.replace('\r', '').strip()
    
    # 2. Highlight key info (Regex) - Apply BEFORE structure splitting to ensure it persists
    # Dates
    text = re.sub(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2}|\d{4}년\s?\d{1,2}월\s?\d{1,2}일|\d{4}년\s?\d{1,2}월)', r'<strong>\1</strong>', text)
    # Money/Percentages
    text = re.sub(r'(\d+(?:,\d{3})*원|\d+(?:\.\d+)?%)', r'<strong>\1</strong>', text)
    
    # 3. Split into blocks
    blocks = text.split('\n\n')
    blocks = [b.strip() for b in blocks if b.strip()]
    
    adapted_html = ""
    
    # --- Logic: Intro Section ---
    # Assume the first block is the "Lead" (Summary)
    if blocks:
        intro_text = blocks[0]
        # Apply sentence splitting for Intro too
        intro_text = intro_text.replace('. ', '.<br>')
        adapted_html += f'<div class="intro-box"><span class="intro-label">요약</span>{intro_text}</div>\n'
        
        # Remove first block from processing
        blocks = blocks[1:]

    # --- Logic: Body Sections ---
    for block in blocks:
        # Heuristic: Is this a Title/Subheading?
        # Check patterns: starts with special char or short length (<40 chars)
        is_header = False
        strip_block = re.sub(r'<[^>]+>', '', block).strip() # clean tags for check
        
        if len(strip_block) < 40 and not strip_block.endswith('.'):
            is_header = True
        elif strip_block.startswith(('□', 'ㅇ', '-', '1.', '[', '(', '<')):
             is_header = True

        if is_header:
            # Clean header chars
            clean_header = re.sub(r'^[\□\ㅇ\-\1\.\s]+', '', strip_block)
            adapted_html += f"<h3>{clean_header}</h3>\n"
        else:
            # Regular Body Text
            # Apply strict sentence breaking
            # Replace ". " with ".<br><br>" for distinct separation or ".<br>" for soft break
            # User asked for "Sentence end -> line break".
            body_text = block.replace('. ', '.<br><br>')
            adapted_html += f"<p>{body_text}</p>\n"
            
    return adapted_html

def fetch_article(url):
    full_url = BASE_URL + url
    print(f"Fetching: {full_url}")
    try:
        response = requests.get(full_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_node = soup.select_one("div.viewTit > h4")
        title_text = title_node.get_text(strip=True) if title_node else "제목 없음"
        
        if title_text == "제목 없음":
            print(f"Skipping untitled article: {url}")
            return None
        
        content_node = soup.select_one("div.viewContent")
        if content_node:
            adapted_html = adapt_text(content_node.get_text())
        else:
            adapted_html = "<p>내용을 가져올 수 없습니다.</p>"
        
        return {
            "title": title_text,
            "content": adapted_html,
            "date": datetime.date.today().strftime("%Y.%m.%d"),
            "url": full_url
        }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def generate_html(article, index):
    filename = f"article-press-{index}.html"
    filepath = os.path.join(BLOG_DIR, filename)
    
    display_title = article['title'].replace('[보도자료]', '').strip()
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} | 농지연금 블로그</title>
    
    <!-- AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2686975437928535"
     crossorigin="anonymous"></script>

    <link rel="stylesheet" href="../style.css">
    <style>
        .article-container {{ max-width: 680px; margin: 0 auto; padding: 40px 24px; }}
        .article-header {{ border-bottom: 1px solid var(--color-border); padding-bottom: 20px; margin-bottom: 30px; }}
        .article-title {{ font-size: 1.6rem; font-weight: 700; line-height: 1.4; }}
        .article-meta {{ color: var(--color-text-sub); margin-top: 10px; font-size: 0.9rem; }}
        
        /* Body Typography */
        .article-body {{ font-size: 1.1rem; line-height: 1.8; color: var(--color-text-main); word-break: keep-all; }}
        .article-body strong {{ background: linear-gradient(120deg, var(--color-primary-light) 0%, var(--color-primary-light) 100%); padding: 0 4px; border-radius: 4px; color: inherit; font-weight: 700; }}
        
        /* Intro Box */
        .intro-box {{ background: var(--color-surface); padding: 20px; border-radius: 12px; margin-bottom: 40px; border: 1px solid var(--color-primary); position: relative; }}
        .intro-label {{ background: var(--color-primary); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; position: absolute; top: -12px; left: 20px; }}
        
        /* Headers */
        .article-body h3 {{ font-size: 1.3rem; margin: 40px 0 16px; border-left: 4px solid var(--color-primary); padding-left: 12px; color: var(--color-text-main); font-weight: 700; }}
        .article-body p {{ margin-bottom: 24px; }}
        
        .original-link {{ display: block; margin-top: 40px; padding: 15px; background: var(--color-surface); border-radius: 8px; color: var(--color-text-main); text-decoration: none; font-weight: 600; text-align: center; border: 1px solid var(--color-border); transition: background 0.2s; }}
        .original-link:hover {{ background: var(--color-bg); }}
    </style>
</head>
<body>
    <div class="article-container">
        <a href="./" style="text-decoration: none; color: var(--color-text-sub);">← 목록으로</a>
        <header class="article-header">
            <h1 class="article-title">{display_title}</h1>
            <div class="article-meta">{article['date']} · 보도자료 요약</div>
        </header>
        <div class="article-body">
            {article['content']}
        </div>
        
        <div class="ad-container" style="margin: 40px 0;">
            <!-- AdSense Slot (Example) -->
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-2686975437928535"
                 data-ad-slot="6069624797"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({{}});
            </script>
        </div>

        <a href="{article['url']}" class="original-link">원문 보러가기 →</a>
    </div>
     <script>
        if(localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-mode');
        }}
    </script>
</body>
</html>"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated: {filename}")
    return filename

def update_index(articles):
    index_path = os.path.join(BLOG_DIR, "index.html")
    
    # Read existing index to get header
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will reconstruct the file to ensure cleanliness
    # Header part: Up to start of main container or similar
    # But simplifies: Let's use the template structure we know.
    
    new_items = ""
    for i, article in enumerate(articles):
        filename = f"article-press-{i+1}.html" 
        title = article['title'].replace('[보도자료]', '').strip()
        preview = re.sub(r'<[^>]+>', '', article['content'])[:60] + "..."
        
        new_items += f"""
        <a href="{filename}" class="article-card">
            <h2 class="article-title">{title}</h2>
            <div class="article-meta">{article['date']} · 보도자료</div>
            <p class="article-excerpt">{preview}</p>
        </a>
        """

    # Static parts
    header = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
        content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="description" content="농지연금 가입 전 꼭 알아야 할 필수 정보와 꿀팁을 확인하세요.">
    <title>농지연금 가이드 | 블로그</title>
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2686975437928535"
     crossorigin="anonymous"></script>

    <link rel="stylesheet" href="../style.css">
    <style>
        /* Blog Specific Styles */
        .blog-header {
            text-align: center;
            padding: 40px 20px;
            background: var(--color-surface);
            border-bottom: 1px solid var(--color-border);
        }

        .blog-container {
            max-width: 720px;
            margin: 0 auto;
            padding: 24px 20px;
        }

        .article-card {
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            transition: transform 0.2s;
            cursor: pointer;
            text-decoration: none;
            display: block;
            color: inherit;
        }

        .article-card:hover {
            transform: translateY(-4px);
            border-color: var(--color-primary);
        }

        .article-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 12px;
            color: var(--color-text-main);
        }

        .article-meta {
            font-size: 0.9rem;
            color: var(--color-text-sub);
            margin-bottom: 16px;
        }

        .article-excerpt {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--color-text-main);
        }

        .back-nav {
            padding: 20px;
            max-width: 720px;
            margin: 0 auto;
        }

        .btn-back {
            background: none;
            border: none;
            color: var(--color-primary);
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
    </style>
</head>

<body>
    <div class="background-globes">
        <div class="globe globe-1"></div>
        <div class="globe globe-2"></div>
    </div>

    <div class="back-nav">
        <a href="../" class="btn-back">← 계산기로 돌아가기</a>
    </div>

    <header class="blog-header">
        <h1 class="app-title" style="font-size: 2rem;">농지연금 인사이트</h1>
        <p class="section-desc" style="margin-bottom:0;">현명한 노후 설계를 위한 필수 가이드</p>
    </header>

    <main class="blog-container">
"""
    
    footer = """
        <!-- Article 1 -->
        <a href="article-1.html" class="article-card">
            <h2 class="article-title">농지연금, 실제 조회는 어떻게 하나요?</h2>
            <div class="article-meta">2026.01.17 · 가이드</div>
            <p class="article-excerpt">
                공시지가와 감정평가액 중 무엇이 유리할까요? 배우자 승계형 가입 시 주의할 점은 무엇일까요?
                농지은행 공식 기준을 바탕으로 핵심만 정리해 드립니다.
            </p>
        </a>
    </main>

    <script>
        // Theme Persistence Script (Minimal)
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-mode');
        }
    </script>
</body>
</html>
"""
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(header + new_items + footer)
    print("Updated index.html")

def main():
    articles = []
    print("Starting crawler...")
    
    target_links = get_article_links()
    
    # Process only top 10
    for i, link in enumerate(target_links[:10]): 
        data = fetch_article(link)
        if data:
            generate_html(data, i+1) 
            articles.append(data)
    
    if articles:
        update_index(articles)
        print("Success! Generated blog posts.")

if __name__ == "__main__":
    main()
