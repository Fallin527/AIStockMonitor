import asyncio
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import logging
import os

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 移动端浏览器配置
MOBILE_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"

SCREENSHOT_PATH = "debug_screenshots"

async def fetch_product_info():
    """使用Playwright实现的手机浏览器商品爬虫."""
    try:
        async with async_playwright() as p:

            
            # 启动Chromium浏览器并设置移动端视口
            browser = await p.chromium.launch(
                headless=False,  # 启用有头模式
                slow_mo=500   # 减慢操作速度便于观察
            )
            context = await browser.new_context(
                user_agent=MOBILE_USER_AGENT,
                viewport={"width": 375, "height": 812},  # iPhone X尺寸
                accept_downloads=True
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
            
            # 访问目标页面
            await page.goto('https://80lp.com/mobile')
            
            # 等待并检测页面中的商品元素
            try:
                await page.wait_for_function("""
                    () => {
                        // 检查是否存在商品容器
                        const items = document.querySelectorAll('.fui-goods-item');
                        return items.length > 0;
                    }
                """, timeout=30000)
            except Exception as e:
                logging.warning(f'未检测到商品容器: {str(e)}')

            # 获取最终页面内容
            content = await page.content()
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
        logging.error(f'浏览器自动化执行失败: {str(e)}')
        return []