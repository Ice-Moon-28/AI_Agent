"""reworkd_platform models."""
import pkgutil
from pathlib import Path

from loguru import logger


def load_all_models() -> None:
    """Load all models from this folder."""
    # 修正路径拼接方式
    package_dir = (Path(__file__).resolve().parent.parent / 'orm').resolve()

    # 动态加载模块
    modules = pkgutil.walk_packages(
        path=[str(package_dir)],  # 指定搜索路径
        prefix="blog_backend_gpt.db.orm.",  # 指定模块路径前缀，需以 '.' 结尾
    )

    logger.info(f"Loading {list(modules)} models from {package_dir}")

    # 导入模块
    for module in modules:
        __import__(module.name)  # noqa: WPS421