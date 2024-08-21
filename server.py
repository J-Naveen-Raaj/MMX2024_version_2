#!/usr/bin/python
import os

from simulation import app

port = int(os.getenv("PORT",8083))
# port = 8083
# main driver function
if __name__ == "__main__":
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host="0.0.0.0", port=port)
