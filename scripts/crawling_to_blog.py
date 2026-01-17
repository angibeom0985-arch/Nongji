
import os
import requests
from bs4 import BeautifulSoup
import datetime

# Configuration
BASE_URL = "https://www.fbo.or.kr"
LIST_URL = "https://www.fbo.or.kr/info/bbs/RepdList.do?menuId=080030&schNtceClsfCd=B01010200"
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
        
        # User defined selector: <td class="subject"> <a ...>
        items = soup.select("td.subject > a")
        for item in items:
            href = item.get('href')
            # The href might be relative or absolute. Usually it's "NoticeView.do?..."
            if href and 'NoticeView.do' in href:
                # Handle path joining carefully. The list is at /info/bbs/
                # Href is likely "NoticeView.do..."
                full_link = f"/info/bbs/{href}"
                links.append(full_link)
                
        print(f"Found {len(links)} articles.")
        return links
    except Exception as e:
        print(f"Error scanning list: {e}")
        return []

def fetch_article(url):
    full_url = BASE_URL + url
    print(f"Fetching: {full_url}")
    try:
        response = requests.get(full_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # User defined selector: <div class="viewTit"> <h4>Title</h4> ...
        title_node = soup.select_one("div.viewTit > h4")
        title_text = title_node.get_text(strip=True) if title_node else "제목 없음"
        
        # User defined selector: <div class="viewContent"> <pre ...>
        content_node = soup.select_one("div.viewContent")
        
        if content_node:
            # "Adaptation": Convert raw pre text to styled paragraphs
            # The user mentioned <pre class="txt">. We extract text and split by newlines.
            raw_text = content_node.get_text()
            # Simple heuristic: Split by double newlines for paragraphs
            paragraphs = raw_text.split('\n\n')
            
            adapted_html = ""
            for p in paragraphs:
                clean_p = p.strip()
                if clean_p:
                    adapted_html += f"<p>{clean_p}</p>\n"
            
            # If explicit images exist, keep them? For now, text adaptation is priority.
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
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']} | 농지연금 블로그</title>
    <link rel="stylesheet" href="../style.css">
    <style>
        .article-container {{ max-width: 680px; margin: 0 auto; padding: 40px 24px; }}
        .article-header {{ border-bottom: 1px solid var(--color-border); padding-bottom: 20px; margin-bottom: 30px; }}
        .article-title {{ font-size: 1.6rem; font-weight: 700; line-height: 1.4; }}
        .article-meta {{ color: var(--color-text-sub); margin-top: 10px; font-size: 0.9rem; }}
        .article-body {{ font-size: 1.05rem; line-height: 1.7; }}
        .article-body img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; }}
        .original-link {{ display: block; margin-top: 40px; padding: 15px; background: var(--color-surface); border-radius: 8px; color: var(--color-primary); text-decoration: none; font-weight: 600; text-align: center; }}
    </style>
</head>
<body>
    <div class="article-container">
        <a href="./" style="text-decoration: none; color: var(--color-text-sub);">← 목록으로</a>
        <header class="article-header">
            <h1 class="article-title">{article['title'].replace('[보도자료]', '').strip()}</h1>
            <div class="article-meta">{article['date']} · 보도자료 요약</div>
        </header>
        <div class="article-body">
            {article['content']}
        </div>
        <a href="{article['url']}" target="_blank" class="original-link">원문 보러가기 →</a>
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
    
    # Read existing index
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create list items
    new_items = ""
    for i, article in enumerate(articles):
        # We start index from 1 for file naming, but loop is 0-based
        filename = f"article-press-{i+1}.html" 
        title = article['title'].replace('[보도자료]', '').strip()
        desc = "농어촌공사 공식 보도자료입니다."
        
        new_items += f"""
        <a href="{filename}" class="article-card">
            <h2 class="article-title">{title}</h2>
            <div class="article-meta">{article['date']} · 보도자료</div>
            <p class="article-excerpt">{desc}</p>
        </a>
        """
        
    # Inject after the first article (marker) or append to container
    # Simple replace for demo: find the end of container and insert before it
    if "<!-- New Articles Inserted Here -->" not in content:
        # Add marker first if not exists (manual injection for now)
        target = '<main class="blog-container">'
        content = content.replace(target, target + "\n<!-- New Articles Inserted Here -->\n" + new_items)
    else:
        # Append to marker
        content = content.replace("<!-- New Articles Inserted Here -->", "<!-- New Articles Inserted Here -->\n" + new_items)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated index.html")

def main():
    articles = []
    print("Starting crawler...")
    
    # Get links dynamically
    target_links = get_article_links()
    
    # Process only top 10 for safety/demo (user can remove slice later)
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
