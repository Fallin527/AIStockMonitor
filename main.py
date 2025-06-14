import sys  # 添加sys模块用于日志输出
import json
import toml
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# 项目内模块
from src.monitor import StockMonitor
from src.scheduler import MonitorScheduler



# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # 确保输出到控制台
)

# 读取配置文件
try:
    with open('config.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
except Exception as e:
    logging.critical(f"配置文件加载失败: {str(e)}")
    raise


def load_products():
    """加载预设商品信息."""
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
            
        # 验证数据格式
        if not isinstance(products, list):
            logging.critical("products.json内容不是列表格式")
            raise SystemExit(1)
            
        return products
    except FileNotFoundError:
        logging.critical("预设商品文件未找到")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        logging.critical(f"JSON解码错误: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        logging.critical(f"加载预设商品时发生错误: {str(e)}")
        raise SystemExit(1)


def main():
    """
    主函数：启动库存监控系统
    """

    logging.debug("初始化配置")
    logging.debug(f"检测间隔: {config['monitor']['interval']}分钟")
    logging.debug(f"Telegram Bot Token: {config['telegram']['bot_token']}")

    # 加载预设商品信息
    pre_configured_products = load_products()


    # 创建库存监控器
    monitor = StockMonitor(config, pre_configured_products)
    # 创建调度器
    scheduler = MonitorScheduler(config, monitor)
    # 启动系统
    logging.info("启动库存监控系统...")
    scheduler.start()

    # 添加监控任务
    scheduler.add_job(monitor.check_stock, 'interval', minutes=config['monitor']['interval'])

if __name__ == "__main__":
    main()