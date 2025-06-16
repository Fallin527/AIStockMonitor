from apscheduler.schedulers.blocking import BlockingScheduler
import time
import logging
import json
import datetime  # 修正为完整datetime模块导入


class MonitorScheduler(BlockingScheduler):
    """库存监控调度器，管理定时任务"""

    def __init__(self, config, monitor):
        super().__init__()  # 调用父类初始化方法
        self.config = config
        self.monitor = monitor

    def _run_check(self):
        """执行库存检查任务"""
        logging.info("开始库存检查")
        
        # 新增时间判断逻辑
        try:
            snooze_start = int(self.config['monitor'].get('snooze_start', 0))
            snooze_end = int(self.config['monitor'].get('snooze_end', 6))
            current_hour = datetime.datetime.now().hour
            
            # 验证时间范围有效性
            if not (0 <= snooze_start < 24 and 0 < snooze_end <= 24):
                logging.warning("免打扰时间配置超出有效范围（0-24），使用默认值")
                snooze_start, snooze_end = 0, 6

            if snooze_start <= current_hour < snooze_end:
                logging.info(f"当前时间在{snooze_start}:00-{snooze_end}:00之间，跳过本次库存检查")
                return
        except ValueError:
            logging.error("免打扰时间配置必须为整数，跳过时间检查")

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
