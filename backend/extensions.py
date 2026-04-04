from flask_cors import CORS
from flask_jwt_extended import JWTManager
from mongoengine import connect, disconnect


jwt = JWTManager()
cors = CORS()


def init_db(app):
    try:
        disconnect(alias="default")
    except Exception:
        pass

    if app.config["USE_MOCK_DB"]:
        import mongomock

        connect(
            host=app.config["MONGODB_URI"],
            alias="default",
            mongo_client_class=mongomock.MongoClient,
        )
        return

    connect(host=app.config["MONGODB_URI"], alias="default")

