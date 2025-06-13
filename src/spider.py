import requests  # 新增requests库
import asyncio
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import logging
import os

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_product_content(content):
    """解析商品页面内容，提取商品信息."""
    soup = BeautifulSoup(content, 'lxml')
    products = []

    # 查找所有商品容器（根据实际HTML结构调整）
    goods_groups = soup.select('div.fui-goods-group.block.three')
    product_items = []
    for group in goods_groups[1:]:  # 跳过第一个爆款促销分组
        items = group.select('.fui-goods-item')
        product_items.extend(items)
    logging.debug(f'找到 {len(product_items)} 个非爆款商品')

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


# 移动端浏览器配置
MOBILE_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"

SCREENSHOT_PATH = "debug_screenshots"


async def fetch_product_info():
    """优先使用requests实现商品爬取，失败时回退到Playwright."""
    try:
        # 尝试使用requests方法
        logging.debug("尝试使用requests方法爬取")
        products = fetch_with_requests()
        if products:
            logging.debug(f"通过requests成功获取{len(products)}个商品")
            return products

    except Exception as e:
        logging.warning(f"requests方法失败: {str(e)}，正在回退到Playwright")

    # 如果requests方法失败，使用Playwright
    logging.debug("使用Playwright进行备用爬取")
    return await fetch_with_playwright()


def fetch_with_requests():
    """使用requests实现商品爬取."""
    # 设置请求头模拟移动端浏览器
    headers = {
        'User-Agent': MOBILE_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://80lp.com/mobile'
    }

    # 设置Cookie
    cookies = {
        'BL_encrypt_c21f969b5f03d33d43e04f8f136e7682': 'c69012c4f51807cf3155bf9a5bed0356'
    }

    try:
        response = requests.get('https://80lp.com/mobile',
                                headers=headers,
                                cookies=cookies,
                                timeout=30)

        # 检查响应状态码
        if response.status_code != 200:
            raise ValueError(f"HTTP错误代码: {response.status_code}")

        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'lxml')

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

        # 保存页面源码用于调试
        with open(os.path.join(SCREENSHOT_PATH, "page_source.html"), "w", encoding="utf-8") as f:
            f.write(response.text)

        return products if products else None

    except Exception as e:
        logging.error(f'requests执行失败: {str(e)}')
        return None


async def fetch_with_playwright():
    """使用Playwright实现的手机浏览器商品爬虫."""
    try:
        async with async_playwright() as p:
            # 启动Chromium浏览器并设置移动端视口
            browser = await p.chromium.launch(
                headless=True,  # 生产环境应启用无头模式
                slow_mo=100  # 适当减少延迟
            )
            context = await browser.new_context(
                user_agent=MOBILE_USER_AGENT,
                viewport={"width": 375, "height": 667},  # 使用更常见的iPhone 8尺寸
                accept_downloads=True,
                ignore_https_errors=True  # 忽略HTTPS错误提高兼容性
            )
            page = await context.new_page()

            # 添加全局Cookie
            await context.add_cookies([
                {
                    "name": "BL_encrypt_c21f969b5f03d33d43e04f8f136e7682",
                    "value": "c69012c4f51807cf3155bf9a5bed0356",
                    "url": "https://80lp.com"
                }
            ])

            # 访问目标页面并等待加载完成
            await page.goto('https://80lp.com/mobile', wait_until="networkidle")  # 等待网络空闲

            # 等待并检测页面中的商品元素
            try:
                await page.wait_for_selector('.fui-goods-item', timeout=30000)  # 直接等待选择器
                logging.debug("检测到商品容器")
            except Exception as e:
                logging.warning(f'未检测到商品容器: {str(e)}')
                content = await page.content()
                with open(os.path.join(SCREENSHOT_PATH, "error_page_source.html"), "w", encoding="utf-8") as f:
                    f.write(content)
                raise

            # 获取最终页面内容
            content = await page.content()
            if not content or len(content) < 1000:  # 检测是否为有效页面内容
                raise ValueError("获取的页面内容过短，可能被重定向或出现错误")
            soup = BeautifulSoup(content, 'lxml')
            products = []

            # 查找所有商品容器（根据实际HTML结构调整）
            # 过滤掉第一个商品分组（爆款促销）
            goods_groups = soup.select('div.fui-goods-group.block.three')
            product_items = []
            for group in goods_groups[1:]:  # 跳过第一个爆款促销分组
                items = group.select('.fui-goods-item')
                product_items.extend(items)
            logging.debug(f'找到 {len(product_items)} 个非爆款商品')

            for item in product_items:

                try:
                    # 提取商品信息（根据实际HTML结构调整）
                    name_elem = item.select_one('.name')
                    price_elem = item.select_one('.minprice')
                    stock_elem = item.select_one('.productprice span[style*="background-color:#0086EE"]')
                    url_elem = item.get('href', '')

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

            # 保存页面源码用于调试
            with open(os.path.join(SCREENSHOT_PATH, "page_source.html"), "w", encoding="utf-8") as f:
                f.write(content)

            logging.debug(f'成功解析 {len(products)} 个商品数据')
            await browser.close()
            return products

    except Exception as e:
        logging.error(f'浏览器自动化执行失败: {str(e)}', exc_info=True)  # 记录完整异常信息
        return []