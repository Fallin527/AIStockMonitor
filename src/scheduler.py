from apscheduler.schedulers.blocking import BlockingScheduler
import time
import logging
import json


class MonitorScheduler(BlockingScheduler):
    """库存监控调度器，管理定时任务"""

    def __init__(self, config, monitor):
        super().__init__()  # 调用父类初始化方法
        self.config = config
        self.monitor = monitor

    def _run_check(self):
        """执行库存检查任务"""
        logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 开始库存检查")

        # 获取实时商品信息
        from src.spider import fetch_product_info
        real_time_products = fetch_product_info()
        # 把爬到的商品信息保存到本地文件data里面文件名是 goods.json
        with open('data/goods.json', 'w', encoding='utf-8') as f:
            json.dump(real_time_products, f, ensure_ascii=False, indent=4)
            logging.info('商品信息保存成功')

        # 检查库存阈值
        alerts = self.monitor.check_stock_threshold(real_time_products)

        if alerts:
            for alert in alerts:
                # 暂时代替消息推送的警告信息
                warning_msg = (
                    f"⚠️ 库存预警: {alert['product_name']} "
                    f"当前库存: {alert['current_stock']} "
                    f"阈值: {alert['threshold']}"
                )
                logging.warning(warning_msg)
        else:
            logging.info("未发现库存异常")

    def start(self):
        """启动定时任务"""
        interval = self.config['monitor']['interval']
        # 使用父类的add_job方法
        self.add_job(
            self._run_check,
            'interval',
            minutes=interval
        )
        logging.info(f"开始监控，检测间隔：{interval}分钟")
        try:
            # 使用父类的start方法
            super().start()
        except KeyboardInterrupt:
            logging.info("接收到退出信号，正在关闭...")
            # 使用父类的shutdown方法
            super().shutdown()