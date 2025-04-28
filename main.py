from flask import Flask, redirect, render_template, request, jsonify
import folium
import requests

app = Flask(__name__)


def start_site():
    print("site")
    app.run(debug=True)



@app.route('/')
def index():
    world_map = folium.Map(location=[64.6863136, 97.7453061], zoom_start=4)
    coords = folium.map.FeatureGroup()
    for i in coord():
        coords.add_child(
            folium.features.Marker(i[0], color='red', popup=f"{i[1], i[2]}")
        )
    world_map.add_child(coords)
    world_map_html = world_map._repr_html_()
    return render_template("main.html", map_html=world_map_html)


def coord():
    all_coords = []
    with open("coordinates.txt") as file:
        for i in file.readlines():
            i = i.split()
            coord = [[i[1], i[0]], i[2], i[3]]
            all_coords.append(coord)
    return all_coords


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)