from chatR import create_app
from flask_cors import CORS

app = create_app()
CORS(app, resources=r'/*')

if __name__ == '__main__':
    app.run()
