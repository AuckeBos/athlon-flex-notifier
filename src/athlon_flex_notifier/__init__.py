from athlon_flex_notifier.bootstrap import bootstrap_di, load_env, setup_mongo_engine

load_env()
setup_mongo_engine()
bootstrap_di()
