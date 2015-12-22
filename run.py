from discordant import Discordant, configure_logging


if __name__ == '__main__':
    configure_logging()

    bot = Discordant('config.ini')
    bot.run()
