import requests
import logging
import os
from bs4 import BeautifulSoup
import toml

# 读取配置文件
with open('config.toml', 'r', encoding='utf-8') as f:
    config = toml.load(f)

# 从配置文件获取参数
MOBILE_USER_AGENT = config['spider']['mobile_user_agent']
TARGET_URL = config['spider']['target_url']
REQUIRED_COOKIE = {
    "name": config['spider']['cookie_name'],
    "value": config['spider']['cookie_value']
}
SCREENSHOT_PATH = "debug_screenshots"

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 基础配置常量

def parse_product_content(content):
    """解析商品页面内容，提取商品信息."""
    soup = BeautifulSoup(content, 'lxml')

    # 查找所有商品容器（根据实际HTML结构调整）
    goods_groups = soup.select('div.fui-goods-group.block.three')
    product_items = []
    for group in goods_groups[1:]:  # 跳过第一个爆款促销分组
        items = group.select('.fui-goods-item')
        product_items.extend(items)
    logging.debug(f'通过requests找到 {len(product_items)} 个非爆款商品')

    products = []
    for item in product_items:
        try:
            # 提取商品信息（根据实际HTML结构调整）
            name_elem = item.select_one('.name')
            price_elem = item.select_one('.minprice')
            stock_elem = item.select_one('.productprice span[style*="background-color:#0086EE"]')

            # 增加空值检查
            if not all([name_elem, price_elem, stock_elem]):
                raise ValueError("缺少必要字段")

            # 解析库存数量
            stock_text = stock_elem.text.strip()
            stock_num = int(stock_text.replace('库存:', '').replace(' ', ''))

            product = {
                'name': name_elem.text.strip(),
                'stock': stock_num
            }
            products.append(product)
        except Exception as e:
            logging.warning(f'解析单个商品失败: {str(e)}')
            continue

    return products


def fetch_product_info():
    """使用requests实现商品爬取."""
    # 设置请求头模拟移动端浏览器
    headers = {
        'User-Agent': MOBILE_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': TARGET_URL,
    }
    
    # 设置Cookie
    cookies = {
        config['spider']['cookie_name']: config['spider']['cookie_value']
    }
    
    try:
        # 创建会话对象
        with requests.Session() as session:
            # 第一次尝试 - 带Cookie的直接访问
            response = session.get(TARGET_URL,
                                 headers=headers, 
                                 cookies=cookies,
                                 timeout=30)
            
            # 检查响应状态码
            if response.status_code != 200:
                raise ValueError(f"HTTP错误代码: {response.status_code}")
            
            # 解析商品信息
            products = parse_product_content(response.text)
            
            # 保存页面源码用于调试（使用utf-8-sig避免BOM问题）
            with open(os.path.join(SCREENSHOT_PATH, "page_source.html"), "w", encoding="utf-8-sig") as f:
                f.write(response.text)
            
            logging.debug(f'成功解析 {len(products)} 个商品数据')
            return products if products else None
            
    except Exception as e:
        logging.error(f'requests执行失败: {str(e)}')
        return None
