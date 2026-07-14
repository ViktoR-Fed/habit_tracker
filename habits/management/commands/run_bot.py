from django.core.management.base import BaseCommand

from telegram_bot.bot import bot_instance


class Command(BaseCommand):
    help = "Запуск Telegram бота"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Telegram bot..."))
        bot_instance.setup()
        bot_instance.run()
