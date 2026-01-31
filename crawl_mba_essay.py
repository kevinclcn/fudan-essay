import os, sys
import logging
from fpdf import FPDF
from PIL import Image
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
import requests


def remove_watermark_from_url(url: str) -> str:
    """
    从URL中移除watermark参数
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        # 移除watermark参数
        if 'watermark' in query_params:
            del query_params['watermark']
        # 重新构建URL
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception as e:
        logging.exception(f"Error removing watermark from URL: {e}")
        return url


def get_and_save_to_img(url: str, filename: str, cookies: dict = None):
    """
    使用 requests 下载图片
    cookies: 字典格式，例如 {"JSESSIONID": "xxx"}
    """
    try:
        # 使用 requests.get，cookies 参数可以直接接受字典
        response = requests.get(url, cookies=cookies, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)
        else:
            logging.error(f"get image failed: {response.status_code}")
    except Exception as e:
        logging.exception(f"get image exception: {e}")


def get_pages(url: str, cookies: dict = None):
    """
    使用 requests 获取页面数据
    cookies: 字典格式，例如 {"JSESSIONID": "xxx"}
    """
    try:
        # 使用 requests.get，cookies 参数可以直接接受字典
        response = requests.get(url, cookies=cookies, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"get page failed: {response.status_code}")
            return None
    except Exception as e:
        logging.exception(f"get page exception for {url}: {e}")
        return None

def images_in_dir_to_pdf(image_dir, output_pdf_path):
    # 创建一个 PDF 对象
    pdf = FPDF()
    # 支持的图片文件扩展名
    supported_extensions = ('.png', '.jpg', '.jpeg')
    # 获取目录下所有图片文件，并按文件名排序
    image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir)
                   if f.lower().endswith(supported_extensions)]
    image_files.sort()

    for image_path in image_files:
        try:
            # 打开图片
            img = Image.open(image_path)
            width, height = img.size
            # 将图片尺寸转换为 PDF 单位（毫米）
            width_mm = width * 25.4 / 72
            height_mm = height * 25.4 / 72

            # 添加一个新页面
            pdf.add_page()

            # 计算图片在 PDF 页面上的位置和缩放比例，以适应页面
            if width_mm > pdf.w - 20:
                height_mm = height_mm * (pdf.w - 20) / width_mm
                width_mm = pdf.w - 20
            if height_mm > pdf.h - 20:
                width_mm = width_mm * (pdf.h - 20) / height_mm
                height_mm = pdf.h - 20

            # 将图片添加到 PDF 页面上
            pdf.image(image_path, x=(pdf.w - width_mm) / 2, y=(pdf.h - height_mm) / 2, w=width_mm, h=height_mm, type=img.format)
        except Exception as e:
            # print(f"Error processing {image_path}: {e}")
            logging.exception(e)

    # 保存 PDF 文件
    pdf.output(output_pdf_path)

def crawl_mba_essay(fid: str, filename: str, cookies: dict = None):
    """
    爬取 MBA 论文
    fid: 文件ID
    filename: 保存的文件名（也是目录名）
    cookies: 字典格式的 cookies，例如 {"JSESSIONID": "xxx"}
    """
    if not os.path.exists(filename):
        os.makedirs(filename, exist_ok=True)

    url_template = "https://drm.fudan.edu.cn/read/jumpServlet?page={page_id}&fid={fid}"

    page_id = 0
    processed_pages = set()
    while True: 
        url = url_template.format(page_id=page_id, fid=fid)
        pages = get_pages(url, cookies=cookies)
        
        # 检查返回数据是否有效
        if not pages or "list" not in pages:
            logging.info(f"No pages data received for page_id={page_id}, stopping")
            break
        
        # 检查列表是否为空
        if not pages["list"] or len(pages["list"]) == 0:
            logging.info(f"Empty list returned for page_id={page_id}, stopping")
            break
            
        # 遍历列表，下载图片并找到最大的id
        next_id = page_id
        for page in pages["list"]:
            id = int(page["id"])
            if id > next_id:
                next_id = id
            if id in processed_pages:
                continue
            print(f"downloading page {id}")
            processed_pages.add(id)
            # 移除URL中的watermark参数
            image_url = remove_watermark_from_url(page["src"])
            get_and_save_to_img(image_url, f"{filename}/page_{int(page['id']):0{3}d}.jpeg", cookies)

        # 如果返回的列表中最大的id不大于当前查询的page_id，说明没有更多页面了
        if int(next_id) <= page_id:
            logging.info(f"Max id {next_id} <= current page_id {page_id}, stopping")
            break
        page_id = int(next_id)




if __name__ == "__main__":
    arg_count = len(sys.argv) - 1
    if arg_count < 2:
        print("Usage: crawl_mba_essay.py <JSessionID> <fid> [filename]")
        print("Example: crawl_mba_essay.py ABC123XYZ 12345")
        sys.exit(1)
    
    JSessionID = sys.argv[1]
    fid = sys.argv[2]
    # 如果提供了第三个参数作为文件名，使用它；否则使用 fid 作为文件名
    # 如果第三个参数是空字符串，也使用 fid
    filename = sys.argv[3] if arg_count >= 3 and sys.argv[3].strip() else fid
    
    cookies = {
        "JSESSIONID": JSessionID
    }

    # 使用 requests 爬取
    crawl_mba_essay(fid, filename, cookies)
    
    # 生成 PDF
    images_in_dir_to_pdf(filename, f"{filename}.pdf")

