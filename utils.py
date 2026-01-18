import requests
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path


def download_image(url: str, save_path: str) -> bool:
    """
    使用 requests 下载图片

    Args:
        url (str): 图片 URL
        save_path (str): 保存路径

    Returns:
        bool: 下载是否成功
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 确保目录存在
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except requests.RequestException as e:
        print(f"下载图片失败: {e}")
        return False


def batch_download_images(image_urls: list, save_dir: str, max_workers: int = 5) -> list:
    """
    批量下载图片

    Args:
        image_urls (list): 图片 URL 列表
        save_dir (str): 保存目录
        max_workers (int): 最大并发数

    Returns:
        list: 下载结果列表
    """
    def download_single_image(url_and_filename):
        url, filename = url_and_filename
        save_path = os.path.join(save_dir, filename)
        return download_image(url, save_path), url

    # 为每个 URL 生成文件名
    url_filename_pairs = [(url, f"image_{i}.jpg") for i, url in enumerate(image_urls)]

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(download_single_image, url_filename_pairs))

    return results


def is_binary_file(file_path, sample_size=1024):
    """
    检测文件是否为二进制文件（音频文件）
    :param file_path: 文件路径
    :param sample_size: 检测样本大小
    :return: True如果是二进制文件，False如果是文本文件
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            if not chunk:
                return False  # 空文件

            # 检查是否包含null字节或其他二进制特征
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            return bool(chunk.translate(None, text_chars))
    except:
        return False

if __name__ == '__main__':
    download_image("http://p2.music.126.net/34YW1QtKxJ_3YnX9ZzKhzw==/2946691234868155.jpg?param=300x300", "./image/2946691234868155.jpg")