from flask_restful import Resource

class MetricsHandler(Resource):
    def get(self):
        return {'hello': 'world'}