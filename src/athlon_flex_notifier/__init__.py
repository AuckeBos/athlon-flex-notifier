from athlon_flex_notifier.bootstrap import load_env, setup_dependency_injection, setup_mongo_engine


load_env()
setup_mongo_engine()
setup_dependency_injection()