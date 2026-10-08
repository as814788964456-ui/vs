import os
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin

def fetch_page(url):
    """
    發送 HTTP 請求取得網頁內容
    """
    # 設定常見的 User-Agent，避免被網站當成機器人阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"正在爬取: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        # 檢查 HTTP 狀態碼是否為 200 (成功)
        response.raise_for_status() 
        
        # 如果網頁編碼不正確，可以手動設定，例如：
        # response.encoding = 'utf-8' 
        
        return response.text
        
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP 錯誤: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"連線錯誤: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"超時錯誤: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"其他錯誤: {err}")
        
    return None

def download_image(img_url, save_dir):
    """
    下載單張圖片並存檔
    """
    try:
        # 發送 GET 請求取得圖片二進位資料
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(img_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()

        # 從網址中提取檔名
        file_name = img_url.split('/')[-1]
        # 去除 url 參數 (例如 ?url=...)
        file_name = file_name.split('?')[0]
        
        # 如果檔名沒有副檔名或是空的，給個預設名稱
        if not file_name or '.' not in file_name:
            file_name = f"image_{int(time.time())}.jpg"
            
        file_path = os.path.join(save_dir, file_name)
        
        # 寫入檔案
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
                
        print(f"✅ 成功下載: {file_name}")
    except Exception as e:
        print(f"❌ 下載失敗 {img_url}: {e}")

def parse_data(html_content, base_url):
    """
    解析 HTML 結構並提取圖片網址進行下載
    """
    if not html_content:
        return
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = soup.title.string if soup.title else "無標題"
    print(f"\n網頁標題: {title}")
    print("-" * 50)
    
    # 建立用來存放圖片的資料夾
    save_dir = "downloaded_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"建立儲存資料夾: {save_dir}")

    # 找出所有 <img> 標籤
    img_tags = soup.find_all('img')
    print(f"共找到 {len(img_tags)} 個 img 標籤")
    
    download_count = 0
    for img in img_tags:
        # 很多網站會把真正的圖片網址放在 src, data-src 或是其他屬性
        img_url = img.get('src') or img.get('data-src')
        
        if not img_url:
            continue
            
        # 忽略 base64 的縮圖與無效字串
        if img_url.startswith('data:image'):
            continue
            
        # 轉換成絕對網址 (處理相對路徑像是 /images/pic.jpg)
        img_url = urljoin(base_url, img_url)
        
        download_image(img_url, save_dir)
        download_count += 1
        
        time.sleep(0.5) # 下載每張圖片間隔 0.5 秒，減輕伺服器負擔
        
    print(f"\n🎉 圖片下載完成！共嘗試下載 {download_count} 張圖片。")

def main():
    target_url = "https://www.cvwizard.com/app/resumes/cefcdde1-4a57-4e3e-bb8a-b64b4620102a/edit?ra=2xSjaRvoryBmojNC5mhXp0&fullscreenPreview=1"
    
    html = fetch_page(target_url)
    
    if html:
        # 將 target_url 傳入作為 base_url 以處理相對路徑的圖片網址
        parse_data(html, target_url)

if __name__ == "__main__":
    main()
