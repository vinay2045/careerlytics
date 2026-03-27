class MockTestRouter:
    """
    A router to control all database operations on models in the
    mock_test_db application.
    """
    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'mocktestxp':
            return 'mock_test_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'mocktestxp':
            return 'mock_test_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations involving MockTestXP
        if obj1._meta.model_name == 'mocktestxp' or obj2._meta.model_name == 'mocktestxp':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'mocktestxp':
            return db == 'mock_test_db'
        if db == 'mock_test_db':
            return False
        return None
