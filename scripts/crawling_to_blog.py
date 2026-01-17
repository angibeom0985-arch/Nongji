import os
import requests
from bs4 import BeautifulSoup
import datetime
import re
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
BASE_URL = "https://www.fbo.or.kr"
LIST_URL = "https://www.fbo.or.kr/info/bbs/RepdList.do?menuId=080030&schNtceClsfCd=B01010200"
BLOG_DIR = "blog"
TEMPLATE_PATH = "blog_template.html"
CHROME_DATA_DIR = r"C:\selenium\chrome_data"
GEMINI_URL = "https://gemini.google.com/app"

def get_article_links():
    print(f"Scanning list: {LIST_URL}")
    all_links = []
    
    # 1. Get First Page to determine Total Pages
    try:
        first_page_url = f"{LIST_URL}&pageIndex=1"
        response = requests.get(first_page_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find Total Pages
        total_pages = 1
        total_span = soup.select_one("ul.m_pagination li.index span.total")
        if total_span:
            total_pages = int(total_span.get_text(strip=True))
            print(f"Total pages detected: {total_pages}")
        else:
            print("Could not detect total pages. Defaulting to 1.")
            
        # 2. Iterate all pages
        for page in range(1, total_pages + 1):
            print(f"Scanning Page {page}/{total_pages}...")
            page_url = f"{LIST_URL}&pageIndex={page}"
            
            # Avoid re-fetching page 1 if we just did it? 
            # It's fine to re-fetch or use logic. Simple re-fetch is robust.
            if page > 1:
                response = requests.get(page_url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

            items = soup.select("td.subject > a")
            page_links = []
            for item in items:
                href = item.get('href')
                if href and 'NoticeView.do' in href:
                    full_link = f"/info/bbs/{href}"
                    # Deduplicate if needed, but list usually unique
                    page_links.append(full_link)
            
            print(f"  Found {len(page_links)} articles on page {page}.")
            all_links.extend(page_links)
            
            # Nice delay to be polite
            time.sleep(0.5)
            
        print(f"Total articles found: {len(all_links)}")
        return all_links

    except Exception as e:
        print(f"Error scanning list: {e}")
        return []

def adapt_text(raw_text):
    # (Leaving adapt_text as is, but it might be unused if adapt_content_node is used?)
    # ... logic unchanged ...
    return raw_text 

# ... (Previous adapt_content_node and fetch_article functions remain) ...

def main():
    generated_list = []
    print("Starting crawler...")
    
    target_links = get_article_links()
    
    # Remove LIMIT: Process ALL links
    for i, link in enumerate(target_links): 
        print(f"Processing ({i+1}/{len(target_links)}): {link}")
        data = fetch_article(link)
        if data:
            fname = generate_html(data)
            display_title = data['title'].replace('[보도자료]', '').strip()
            preview = re.sub(r'<[^>]+>', '', data['content'])[:60] + "..."
            generated_list.append((fname, display_title, data['date'], preview))
        
        # Save index checkpoint every 20 articles? Or just at end?
        # For safety, let's just do it at the end for now, or maybe update in chunks?
        
    if generated_list:
        update_index(generated_list)
        print("Success! Generated blog posts.")

if __name__ == "__main__":
    main()

def sanitize_filename(title):
    # Remove special chars, replace spaces with hyphens
    clean = re.sub(r'[\\/*?:"<>|]', '', title)
    clean = clean.replace(' ', '-').replace('[', '').replace(']', '')
    return clean.strip()[:50] # Limit length



def adapt_content_node(content_node):
    """
    Parses the BeautifulSoup content node to extract structure:
    - Intro (First paragraph)
    - Subheadings (Bold text, or lines starting with □, ○, -, <)
    - Body (Regular text)
    Returns: HTML string with <div class="intro-box">, <h3>, <p>
    """
    if not content_node:
        return ""
        
    final_html = ""
    
    # Strategy: Iterate through significant child elements (p, div) or split by <br>
    # Since structure varies, we'll try to process 'blocks' of text.
    # We will look for structural markers in text AND HTML tags (strong/b).
    
    # 1. Get textual blocks (mixed with relevant tags)
    # We'll use a simplified approach: process text lines but check for 'strong' parents
    
    lines = []
    # Using 'decode_contents' to get inner HTML, then split by <br> or </p> is one way.
    # An easier way using BS4: iterate over strings and tags?
    # Let's clean it up:
    
    # Convert <br> to newlines to distinct blocks
    for br in content_node.find_all("br"):
        br.replace_with("\n")
        
    # Get text blocks (splitting by newlines we just made + natural block elements)
    text = content_node.get_text("\n")
    raw_blocks = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not raw_blocks:
        return ""

    # Phase 2: Classification
    # First block -> Intro (unless it's a date or meta info? Press releases usually start with title or intro)
    # But usually Title is separate. So first block is Intro.
    
    intro_done = False
    
    for i, block in enumerate(raw_blocks):
        # 1. Detect Intro (First valid block)
        if not intro_done:
            # Highlight key info in Intro
            block = re.sub(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2}|\d{4}년\s?\d{1,2}월\s?\d{1,2}일)', r'<span class="highlight-green">\1</span>', block)
            block = re.sub(r'(\d+(?:,\d{3})*원|\d+(?:\.\d+)?%)', r'<span class="highlight-green">\1</span>', block)
            
            final_html += f'<div class="intro-box"><span class="intro-label">요약</span>{block}</div>\n'
            intro_done = True
            continue

        # 2. Detect Header vs Body
        is_header = False
        
        # Heuristic 1: Special Bullets (Very common in Korean Gov docs)
        if block.startswith(('□', '○', 'ㅇ', 'o', '-', '1.', '[', '<')):
            is_header = True
            # Clean bullet for display
            clean_text = re.sub(r'^[\□\○\ㅇ\-\1\.\s]+', '', block).strip()
        else:
            clean_text = block

        # Heuristic 2: Short length + Ends without punctuation (often a title)
        if len(block) < 40 and not block.endswith(('.', ',')):
             is_header = True

        # Render
        if is_header:
            final_html += f"<h3>{clean_text}</h3>\n"
        else:
            # Body Formatting: Highlight logic + Sentence Break
            body_text = block
            body_text = re.sub(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2}|\d{4}년\s?\d{1,2}월\s?\d{1,2}일)', r'<span class="highlight-green">\1</span>', body_text)
            body_text = re.sub(r'(\d+(?:,\d{3})*원|\d+(?:\.\d+)?%)', r'<span class="highlight-green">\1</span>', body_text)
            
            # Sentence splitting for readability
            # Strict Sentence splitting: Break on every period followed by space
            body_text = body_text.replace('. ', '.<br>')
            
            final_html += f"<p>{body_text}</p>\n"
            
    return final_html

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
            return None
            
        # Extract Date
        date_text = datetime.date.today().strftime("%Y.%m.%d") # Default
        view_tit_ul = soup.select_one("div.viewTit ul")
        if view_tit_ul:
            text_content = view_tit_ul.get_text()
            match = re.search(r'(\d{4}-\d{2}-\d{2})', text_content)
            if match:
                date_text = match.group(1).replace('-', '.')
        
        content_node = soup.select_one("div.viewContent")
        if content_node:
            # NEW: Pass the Node itself to easier extraction logic (or just text extraction with BR handling)
            # The new adapt_content_node handles <br> to \n conversion internally
            adapted_html = adapt_content_node(content_node)
        else:
            adapted_html = "<p>내용을 가져올 수 없습니다.</p>"
            
        # File Attachment scraping
        files = []
        file_node = soup.select_one("div.viewFile")
        if file_node:
            links = file_node.select("dd.fileName a")
            if not links: links = file_node.select("a")
            for link in links:
                file_href = link.get('href')
                file_name = link.get_text(strip=True)
                if file_href and "NoticeDownload" in file_href:
                    full_file_url = f"https://www.fbo.or.kr/info/bbs/{file_href}"
                    files.append({"name": file_name, "url": full_file_url})

        return {
            "title": title_text,
            "content": adapted_html,
            "date": date_text,
            "url": full_url,
            "files": files
        }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def generate_html(article):
    display_title = article['title'].replace('[보도자료]', '').strip()
    safe_filename = sanitize_filename(display_title) + ".html"
    filepath = os.path.join(BLOG_DIR, safe_filename)
    
    # File Block HTML
    file_html = ""
    if article['files']:
        file_html += '<div class="file-download-box"><h4>첨부파일</h4><ul>'
        for f in article['files']:
             file_html += f'<li><a href="{f["url"]}" target="_blank">📄 {f["name"]}</a></li>'
        file_html += '</ul></div>'

    ad_block = """
<div class="ad-wrapper">
<center>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-2686975437928535"
     data-ad-slot="6069624797"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
</center></div>
    """
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} | 농지연금 블로그</title>
    
    <link rel="icon" type="image/png" href="../favicon.png">
    <link rel="apple-touch-icon" href="../favicon.png">

    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2686975437928535"
     crossorigin="anonymous"></script>

    <link rel="stylesheet" href="../style.css">
    <style>
        .article-container {{ max-width: 680px; margin: 0 auto; padding: 40px 24px; }}
        
        /* Header Styling */
        .article-header {{ border-bottom: 1px solid var(--color-border); padding-bottom: 30px; margin-bottom: 30px; }}
        .article-title {{ font-size: 2rem; font-weight: 800; line-height: 1.4; margin-top: 10px; word-break: keep-all; letter-spacing: -0.02em; color: var(--color-text-main); }}
        .article-meta {{ color: var(--color-text-sub); margin-top: 16px; font-size: 0.95rem; }}
        
        /* Navigation Button */
        .btn-list {{ display: inline-flex; align-items: center; padding: 10px 16px; background-color: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; color: var(--color-text-sub); text-decoration: none; font-weight: 600; transition: all 0.2s; font-size: 0.9rem; }}
        .btn-list:hover {{ background-color: var(--color-bg); color: var(--color-text-main); border-color: var(--color-text-sub); }}
        
        /* Body Typography */
        .article-body {{ font-size: 1.15rem; line-height: 1.8; color: var(--color-text-main); word-break: keep-all; }}
        .highlight-green {{ color: var(--color-primary); font-weight: 700; background-color: rgba(0, 135, 68, 0.08); padding: 0 4px; border-radius: 4px; }}
        
        /* Intro Box & Ads */
        .intro-box {{ background: var(--color-surface); padding: 24px; border-radius: 16px; margin-bottom: 50px; border: 1px solid var(--color-primary); position: relative; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }}
        .intro-label {{ background: var(--color-primary); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; position: absolute; top: -14px; left: 24px; }}
        .ad-wrapper {{ margin: 15px 0; padding: 10px 0; background: var(--color-bg); border-radius: 8px; }}

        /* Headers & Spacing */
        .article-body h3 {{ font-size: 1.5rem; margin: 60px 0 24px; border-left: 5px solid var(--color-primary); padding-left: 18px; color: var(--color-text-main); font-weight: 800; line-height: 1.3; }}
        .article-body p {{ margin-bottom: 28px; }}
        
        .file-download-box {{ background: var(--color-surface-lighter); padding: 24px; border-radius: 12px; margin-top: 40px; border: 1px solid var(--color-border); }}
        .file-download-box h4 {{ font-size: 1.1rem; margin-bottom: 16px; color: var(--color-text-sub); font-weight: 700; }}
        .file-download-box ul {{ list-style: none; padding: 0; }}
        .file-download-box li {{ margin-bottom: 12px; }}
        .file-download-box a {{ color: var(--color-primary); text-decoration: none; font-weight: 600; display: flex; align-items: center; gap: 10px; padding: 8px 0; }}
        .file-download-box a:hover {{ text-decoration: underline; }}
        
        .original-link {{ display: block; margin-top: 60px; padding: 18px; background: var(--color-surface); border-radius: 12px; color: var(--color-text-main); text-decoration: none; font-weight: 600; text-align: center; border: 1px solid var(--color-border); transition: background 0.2s; font-size: 1.1rem; }}
        .original-link:hover {{ background: var(--color-bg); }}
    </style>
</head>
<body>
    <div class="article-container">
        <a href="./" class="btn-list">← 목록으로</a>
        <header class="article-header">

            <h1 class="article-title">{display_title}</h1>
            <div class="article-meta">{article['date']} · 보도자료 요약</div>
        </header>
        
        {ad_block}
        
        <div class="article-body">
            {article['content']}
        </div>
        
        {file_html}
        
        {ad_block}

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
    
    print(f"Generated: {safe_filename}")
    return safe_filename

def update_index(html_files_map):
    # html_files_map is list of (filename, title, date, content_preview)
    index_path = os.path.join(BLOG_DIR, "index.html")
    
    new_items = ""
    for item in html_files_map:
        filename, title, date, preview = item
        new_items += f"""
        <a href="{filename}" class="article-card">
            <h2 class="article-title">{title}</h2>
            <div class="article-meta">{date} · 보도자료</div>
            <p class="article-excerpt">{preview}</p>
        </a>
        """

    header = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
        content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="description" content="농지연금 가입 전 꼭 알아야 할 필수 정보와 꿀팁을 확인하세요.">
    <title>농지연금 가이드 | 블로그</title>
    
    <link rel="icon" type="image/png" href="../favicon.png">
    <link rel="apple-touch-icon" href="../favicon.png">

    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2686975437928535"
     crossorigin="anonymous"></script>

    <link rel="stylesheet" href="../style.css">
    <style>
        .blog-header { text-align: center; padding: 40px 20px; background: var(--color-surface); border-bottom: 1px solid var(--color-border); }
        .blog-container { max-width: 720px; margin: 0 auto; padding: 24px 20px; }
        .article-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 16px; padding: 24px; margin-bottom: 24px; transition: transform 0.2s; cursor: pointer; text-decoration: none; display: block; color: inherit; }
        .article-card:hover { transform: translateY(-4px); border-color: var(--color-primary); }
        .article-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 12px; color: var(--color-text-main); }
        .article-meta { font-size: 0.9rem; color: var(--color-text-sub); margin-bottom: 16px; }
        .article-excerpt { font-size: 1rem; line-height: 1.6; color: var(--color-text-main); }
        .back-nav { padding: 20px; max-width: 720px; margin: 0 auto; }
        .btn-back { background: none; border: none; color: var(--color-primary); font-weight: 600; cursor: pointer; font-size: 1rem; display: flex; align-items: center; gap: 8px; }
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

class GeminiBot:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        """Sets up the Chrome WebDriver with persistent user profile."""
        if not os.path.exists(CHROME_DATA_DIR):
            os.makedirs(CHROME_DATA_DIR)
            print(f"Created chrome data directory at: {CHROME_DATA_DIR}")

        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={CHROME_DATA_DIR}")
        chrome_options.add_argument("profile-directory=Default")
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--log-level=3")

        print("Launching Chrome...")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.implicitly_wait(10)

    def login_check(self):
        self.driver.get(GEMINI_URL)
        print(f"Navigated to {GEMINI_URL}")
        while "accounts.google.com" in self.driver.current_url:
            print("\n[!] Please log in to Google in the opened browser window.")
            time.sleep(5)
        print("[+] Login detected! Accessing Gemini...")

    def send_prompt(self, prompt_text):
        try:
            print("Looking for input box...")
            input_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            input_box.click()
            input_box.clear()
            pyperclip.copy(prompt_text)
            input_box.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
            
            print("Speaking to Gemini...")
            time.sleep(3)
            time.sleep(10) # Simple wait
            
            response_elements = self.driver.find_elements(By.CSS_SELECTOR, ".model-response-text") 
            if not response_elements:
                response_elements = self.driver.find_elements(By.CSS_SELECTOR, "markdown-converter")

            if response_elements:
                return response_elements[-1].text
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    generated_list = []
    print("Starting crawler...")
    
    target_links = get_article_links()
    
    # Process ALL links
    for i, link in enumerate(target_links): # Removed [:12]
        print(f"Processing ({i+1}/{len(target_links)}): {link}")
        data = fetch_article(link)
        if data:
            fname = generate_html(data)
            display_title = data['title'].replace('[보도자료]', '').strip()
            preview = re.sub(r'<[^>]+>', '', data['content'])[:60] + "..."
            generated_list.append((fname, display_title, data['date'], preview))
    
    if generated_list:
        update_index(generated_list)
        print("Success! Generated blog posts.")

if __name__ == "__main__":
    main()
