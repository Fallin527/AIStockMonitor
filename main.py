import toml
import asyncio
import logging
import json
import os

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取配置文件
with open('config.toml', 'r', encoding='utf-8') as f:
    config = toml.load(f)

if __name__ == "__main__":
    # 初始化配置
    logging.debug("初始化配置...")
    logging.debug(f"检测间隔: {config['monitor']['interval']}分钟")
    logging.debug(f"Telegram Bot Token: {config['telegram']['bot_token']}")

    # 获取商品信息
    logging.debug("开始爬取商品信息...")
    from src.spider import fetch_product_info
    products = asyncio.run(fetch_product_info())
    
    # 格式化输出JSON数据
    if products:
        json_data = json.dumps(products, indent=2, ensure_ascii=False)
        print(json_data)
        
        # 保存到本地文件
        output_path = "data/products.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        logging.debug(f'共获取到{len(products)}个商品信息，已保存至 {output_path}')
    else:
        logging.warning("未获取到任何商品信息")