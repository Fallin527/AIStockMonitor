import time
import logging
import json
from datetime import datetime
import asyncio
from src.telegram_bot import TelegramBot  # 导入Telegram Bot模块
from telegram.error import NetworkError, RetryAfter  # 导入Telegram网络异常类


class StockMonitor:
    """库存监控器，负责管理商品列表和预警状态"""

    def __init__(self, config, pre_configured_products):
        self.config = config
        self.last_alert_time = {}
        # 使用预设商品信息作为基准
        self.products = {p['name']: p for p in pre_configured_products}
        
        # 初始化Telegram Bot模块
        self.telegram_bot = TelegramBot(config)
            
        logging.debug(f"初始化了 {len(self.products)} 个商品的监控")

            
    def check_stock_threshold(self, real_time_products=None):
        """检查所有商品库存阈值并触发预警"""
        current_time = time.time()
        alerts = []

        # 创建实时库存索引
        real_time_index = {p['name']: p for p in real_time_products}
        
        # 检查每个预设商品的库存
        for product_name, info in self.products.items():
            # 获取实时库存
            real_info = real_time_index.get(product_name)
            
            if not real_info:
                logging.warning(f"未找到商品 '{product_name}' 的实时数据")
                continue
                
            try:
                # 获取商品当前库存（确保是整数）
                current_stock = int(real_info['stock'])
                
                # 获取商品自身阈值（优先），若未定义则默认0
                threshold = int(info.get('threshold', 0))
                
                # 阈值为-1时跳过库存检查
                if threshold == -1:
                    continue
                
            except (ValueError, TypeError) as e:
                logging.error(f"库存阈值解析错误 - 商品: {product_name}, 错误: {str(e)}")
                continue
                
            # 记录库存检查详情（DEBUG级别）
            logging.debug(f"库存检查 - 商品: {product_name}, 当前库存: {current_stock}, 阈值: {threshold}")
            
            # 检查库存是否低于阈值
            if current_stock < threshold:
                # 冷却时间检查
                last_alert = self.last_alert_time.get(product_name, 0)
                if current_time - last_alert > self.config['monitor']['cooldown']:
                    # 构造消息内容
                    warning_msg = (
                        f"⚠️ *库存预警*\n"
                        f"商品名称：{product_name}\n"
                        f"当前库存：{current_stock}\n"
                        f"阈值：{threshold}\n"
                        f"时间戳：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    # 控制台打印库存预警信息
                    print(warning_msg)
                    logging.warning(warning_msg)
                    
                    # 发送Telegram消息
                    try:
                        self.telegram_bot.send_message(warning_msg)
                    except Exception as e:
                        logging.error(f"发送Telegram消息异常: {str(e)}")
                    
                    # 添加到警报列表
                    alerts.append({
                        'product_name': product_name,
                        'current_stock': current_stock,
                        'threshold': threshold
                    })
                    self.last_alert_time[product_name] = current_time
                
        return alerts

    def check_stock(self, real_time_products=None):
        """执行库存检查流程"""
        logging.info("开始执行库存检查...")
        alerts = self.check_stock_threshold(real_time_products)
        if alerts:
            for alert in alerts:
                logging.warning(
                    f"⚠️ 库存预警: {alert['product_name']} "
                    f"当前库存: {alert['current_stock']} "
                    f"阈值: {alert['threshold']}"
                )
        else:
            logging.info("未发现库存异常")
        return alerts
