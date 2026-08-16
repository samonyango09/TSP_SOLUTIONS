from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    workspace_root: Path = Path("./workspace")
    data_raw_root: Path = Path("../data/raw")
    customers_csv_path: Path = Path("../Customer Sales Analysis-Misoclear and Mariprist Only.csv")

    # Unset locally -> SQLite at workspace/app.db. Set in production (e.g. a
    # Neon/Supabase Postgres URL) - Render/Fly's free-tier filesystem is
    # ephemeral, so SQLite's single file wouldn't survive a redeploy there.
    # Accepts a standard postgres:// URL; SQLAlchemy's driver prefix is
    # normalized in `database_url` below.
    database_url: str = ""

    app_password: str = ""
    session_secret: str = "dev-only-change-me"

    # Fuzzy-match thresholds (rapidfuzz token_set_ratio, 0-100). Below reject_below
    # a candidate isn't stored at all - too noisy to be useful.
    match_auto_confirm_threshold: float = 90.0
    match_suggest_threshold: float = 70.0

    # Churn classification: ratio of days-since-last-order to the customer's own
    # average purchase interval. >= churned_ratio -> churned, >= at_risk_ratio -> at_risk.
    churn_at_risk_ratio: float = 1.5
    churn_churned_ratio: float = 3.0

    route_buffer_km_default: float = 15.0
    osrm_base_url: str = "https://router.project-osrm.org"

    @property
    def db_path(self) -> Path:
        return self.workspace_root / "app.db"

    @property
    def sqlalchemy_url(self) -> str:
        if not self.database_url:
            return f"sqlite:///{self.db_path}"
        # Render/Neon/Supabase commonly hand out "postgres://" or
        # "postgresql://" - SQLAlchemy with the psycopg3 driver needs the
        # "postgresql+psycopg://" form explicitly.
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def pharma_outlets_csv(self) -> Path:
        return self.data_raw_root / "geocoded_pharmaceutical_outlets.csv"

    @property
    def hospitals_csv(self) -> Path:
        return self.data_raw_root / "registered_hospitals.csv"

    @property
    def customers_csv(self) -> Path:
        return self.customers_csv_path


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.workspace_root.mkdir(parents=True, exist_ok=True)
    return settings
