import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

class TelegramBot:
    """Telegram Bot消息推送模块"""
    
    def __init__(self, config):
        self.config = config
        self.bot = None
        self.chat_id = None
        self._init_bot()
        self.loop = asyncio.get_event_loop()  # 获取当前事件循环
    
    def _init_bot(self):
        """初始化Telegram Bot"""
        if 'telegram' in self.config and self.config['telegram'].get('bot_token'):
            try:
                self.bot = Bot(self.config['telegram']['bot_token'])
                self.chat_id = self.config['telegram'].get('chat_id')
                logging.debug("Telegram Bot初始化成功")
            except Exception as e:
                logging.error(f"Telegram Bot初始化失败: {str(e)}")
                self.bot = None
                self.chat_id = None
        else:
            logging.warning("未配置Telegram Bot Token，消息推送功能将不可用")
            self.bot = None
            self.chat_id = None
    
    def send_message(self, message):
        """发送Telegram消息"""
        if not self.bot or not self.chat_id:
            logging.warning("无法发送Telegram消息：Bot未正确初始化或缺少chat_id")
            return False
            
        try:
            # 使用现有事件循环运行异步方法
            self.loop.run_until_complete(self._async_send_message(message))
            logging.info("Telegram消息发送成功")
            return True
        except Exception as e:
            logging.error(f"Telegram消息发送失败: {str(e)}")
            return False
    
    async def _async_send_message(self, message):
        """异步发送Telegram消息"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
            
    def check_connection(self):
        """检查Telegram Bot连接状态"""
        if not self.bot:
            return False
        try:
            # 检查Bot基本信息
            self.loop.run_until_complete(self._check_bot_info())
            return True
        except Exception as e:
            logging.error(f"Telegram Bot连接检查失败: {str(e)}")
            return False
    
    async def _check_bot_info(self):
        """异步检查Bot基本信息"""
        await self.bot.get_me()
