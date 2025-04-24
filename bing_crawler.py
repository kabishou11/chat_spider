import os
import time
import csv
import re
import requests
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from threading import Thread, Lock
from queue import Queue
import json

# 全局控制变量
cancel_crawl = False
continue_crawl = False
BING_URL = "https://www.bing.com/search"
visited_lock = Lock()  # 添加锁以确保线程安全

def load_visited_urls(visited_file):
    if os.path.exists(visited_file):
        with open(visited_file, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_visited_urls(urls, visited_file):
    with open(visited_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(urls))

def load_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config, config_file):
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def download_pdf(url, output_dir):
    try:
        response = requests.get(url, timeout=10, verify=False)  # 禁用SSL验证以解决握手问题
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            pdf_name = os.path.basename(url.split('?')[0]) or f"pdf_{int(time.time())}.pdf"
            pdf_path = os.path.join(output_dir, pdf_name)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"PDF下载成功: {pdf_path}")
            return pdf_path
    except Exception as e:
        print(f"PDF下载失败: {str(e)}")
    return None

def search_bing(driver, query, regions, max_results, max_pages, since=None, until=None, progress_callback=None):
    global cancel_crawl
    search_results = set()
    
    for region in regions:
        for page in range(max_pages):
            if cancel_crawl or len(search_results) >= max_results:
                break
            
            q = query
            if since and until:
                q += f" daterange:{since}-{until}"
            params = {
                'q': q,
                'first': page * 10 + 1,
                'cc': region
            }
            
            try:
                url = f"{BING_URL}?{requests.compat.urlencode(params)}"
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ol#b_results'))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                results = soup.select('li.b_algo h2 a')
                
                for link in results:
                    url = link.get('href')
                    if url and url.startswith('http'):
                        search_results.add(url)
                        if progress_callback:
                            try:
                                progress_callback(f"搜索 {region} 第 {page+1} 页: {url}", len(search_results))
                            except:
                                print(f"进度回调失败于: {url}")
                        if len(search_results) >= max_results:
                            break
                
                next_page = soup.select_one('a.sb_pagN')
                if not next_page:
                    break
                    
            except Exception as e:
                print(f"搜索失败: {str(e)}")
                time.sleep(2)  # 在失败时添加延迟
                continue
    
    return list(search_results)

def clean_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    return text[:10000]

def crawl_page(driver, url, visited, csv_file_path, pdf_dir, depth=1, max_depth=2, progress_callback=None):
    global cancel_crawl
    with visited_lock:  # 线程安全检查和更新
        if cancel_crawl or url in visited or depth > max_depth:
            return
        visited.add(url)
    
    print(f"正在爬取 [第{depth}级]: {url}")
    
    try:
        if url.lower().endswith('.pdf'):
            pdf_path = download_pdf(url, pdf_dir)
            if pdf_path:
                with open(csv_file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["PDF文件", url, f"已下载至: {pdf_path}"])
            return
        
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        title = driver.title or "无标题"
        content = clean_content(driver.page_source)
        
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([title, url, content])
        
        if progress_callback:
            try:
                with visited_lock:
                    progress_callback(f"爬取: {url}", len(visited))
            except:
                print(f"进度回调失败于: {url}")
            
        if depth < max_depth:
            links = driver.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and href.startswith('http'):
                    absolute_url = urljoin(url, href)
                    with visited_lock:
                        if absolute_url not in visited:
                            crawl_page(driver, absolute_url, visited, csv_file_path, pdf_dir, depth + 1, max_depth, progress_callback)
                        
    except Exception as e:
        print(f"爬取失败: {str(e)}")

def run_crawler(query, regions, max_results, max_pages, since, until, output_dir, max_depth=2, progress_callback=None):
    global cancel_crawl, continue_crawl
    
    start_time = time.strftime("%Y%m%d_%H%M%S")
    base_name = f"{query}_{start_time}"
    csv_file_path = os.path.join(output_dir, f"{base_name}.csv")
    visited_file = os.path.join(output_dir, f"{base_name}_visited.txt")
    config_file = os.path.join(output_dir, f"{base_name}_config.json")
    pdf_dir = os.path.join(output_dir, f"{base_name}_pdfs")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    config = load_config(config_file)
    if continue_crawl and config:
        visited = load_visited_urls(visited_file)
        urls = config.get('remaining_urls', [])
        total_results = config.get('total_results', 0)
    else:
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['标题', 'URL', '内容'])
        visited = load_visited_urls(visited_file)
        urls = []
        total_results = 0
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--ignore-certificate-errors')  # 处理SSL错误
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        if not continue_crawl or not urls:
            urls = search_bing(driver, query, regions, max_results, max_pages, since, until, progress_callback)
            total_results = len(urls)
        
        url_queue = Queue()
        for url in urls:
            url_queue.put(url)
        
        def worker():
            # 每个线程拥有自己的驱动实例
            thread_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            try:
                while not url_queue.empty() and not cancel_crawl:
                    url = url_queue.get()
                    crawl_page(thread_driver, url, visited, csv_file_path, pdf_dir, max_depth=max_depth, progress_callback=progress_callback)
                    url_queue.task_done()
            finally:
                thread_driver.quit()
        
        threads = []
        num_threads = min(4, max(1, len(urls)))  # 确保至少有1个线程
        for _ in range(num_threads):
            t = Thread(target=worker)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        remaining_urls = list(url_queue.queue)
        config = {
            'query': query,
            'regions': regions,
            'max_results': max_results,
            'max_pages': max_pages,
            'since': since,
            'until': until,
            'total_results': total_results,
            'remaining_urls': remaining_urls,
            'output_dir': output_dir,
            'max_depth': max_depth
        }
        save_config(config, config_file)
        save_visited_urls(visited, visited_file)
    
    finally:
        driver.quit()
    
    print(f"\n完成! 共爬取 {len(visited)} 个结果")
    return csv_file_path, len(visited)

if __name__ == '__main__':
    run_crawler("TAICCA", ['TW', 'CN', 'US', 'JP'], 100, 10, None, None, r'D:\spider\chat_spider\bing')