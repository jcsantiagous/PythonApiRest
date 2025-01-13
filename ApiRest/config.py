from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "90de4293c01e469715d923460159ddb92c2f17730a4e373104566b3aab828e235c713fd6f0a9e2c6205c85f782c70e288d5443d6209170be87d4886ae6f9b4cb33cac5cd9186860c9cf1353a77d8131676c5877f0ee6d8c363774f985cc8823f3c193d769682e6e04e1a92c168d33c6bd82c037e9f246e1a6fa413d7abc2f04d57dff20b347891badb37b28f9ea4a8a10d1bebc43cd05e0fea689264681adfba960f22d88d03e25f639d66ffdaa9de7dd76fef07639dde8dc52fffb7043241ccb8ccf42911f52e76dfbcdd04b41042f04f5fbefdd4eea107bd72b09d5b44ce175b79ff9b7639fb058d95fd9e59d188d0e2c3065d487632d6bfe1fa3248519e34"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./database/sql_app.db"

    class Config:
        env_file = ".env"


settings = Settings()