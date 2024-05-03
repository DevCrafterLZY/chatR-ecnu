import configparser


class Config:
    def __init__(self, file_path):
        self.config = configparser.ConfigParser()
        self.config.read(file_path)

        # Tokens
        self.openai_api_key = self.config.get("tokens", "OPENAI_API_KEY")
        self.secret_key = self.config.get("tokens", "SECRET_KEY")
        self.baidu_app_id = self.config.get("tokens", "BAIDU_APP_ID")
        self.baidu_api_key = self.config.get("tokens", "BAIDU_API_KEY")

        # Parameters
        self.model_name = self.config.get("parameters", "MODEL_NAME")
        self.first_retrieval_k = self.config.getint("parameters", "FIRST_RETRIEVAL_K")
        self.second_retrieval_k = self.config.getint("parameters", "SECOND_RETRIEVAL_K")

        # Mysql
        self.max_connections = self.config.getint("mysql", "MAX_CONNECTIONS")
        self.host = self.config.get("mysql", "HOST")
        self.port = self.config.getint("mysql", "PORT")
        self.user = self.config.get("mysql", "USER")
        self.password = self.config.get("mysql", "PASSWORD")
        self.database = self.config.get("mysql", "DATABASE")
        self.charset = self.config.get("mysql", "CHARSET")
        self.min_cached = self.config.getint("mysql", "MIN_CACHED")


config = Config('configparser.ini')
