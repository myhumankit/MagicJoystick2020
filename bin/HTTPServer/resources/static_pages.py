import os
from flask import Flask, send_from_directory, request, render_template, make_response
from flask_restful import Resource

class StaticPages(Resource):
    def get(self, folder = "", filename = "index.html"):
        """
        Return the static page requested from folder and filename
        If folder is null, return the file from the views folder
        """
        print(folder, filename)

        if folder == "":
            if filename in os.listdir("templates"):
                return make_response(render_template(filename))
            
            print("%s: file not found" % filename)
            return "", 404

        folders = ["css", "js", "img", "fonts", "fonts", "svg_icon"]

        if folder in folders and filename in os.listdir(folder):
            return send_from_directory(folder,filename)

        print("%s: file not found" % filename)
        return "", 404