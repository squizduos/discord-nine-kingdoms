import environ

@environ.config
class AppConfig:
    token = environ.var(help="Discord app token.")
    debug = environ.bool_var(help="Enable debug mode", default=False)
    words = environ.var(help="Words for filtering", default="Локация,Тема,Ситуация,Существо,Настроение,Персонаж")
    files_dir = environ.var(help="Music files directory", default="files/")
    ffmpeg_executable = environ.var(help="ffmpeg location", default="ffmpeg")
