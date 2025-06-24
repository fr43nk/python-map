import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.transforms as transforms
from shapely.geometry import Point
import numpy as np
import pyproj

from svgpathtools import svg2paths
from svgpath2mpl import parse_path

mappin_path, attributes = svg2paths('map-pin.svg')
mappin_marker = parse_path(attributes[0]['d'])


def teardrop_marker(scale=1):
    # Definiert einen Tropfenpfad durch Kontrollpunkte (normalized)
    verts = [
        (0.0, 0.0),    # Spitze/unten
        (-40, 60),    # rechts oben
        (0.0, 70),    # obere Mitte (Kopf)
        (40, 60),   # links oben
        (0.0, 0.0)     # zurück zur Spitze
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.CURVE3,
        Path.CLOSEPOLY
    ]
    verts = [(x*scale, y*scale) for x, y in verts]
    return Path(verts, codes)

# https://petercbsmith.github.io/marker-tutorial.html
def teardrop_from_svg():
    marker_path, attributes = svg2paths("map-pin.svg")
    pin_marker_path = parse_path(attributes[0]['d'])
    pin_marker_path.vertices -= pin_marker_path.vertices.mean(axis=0)
    pin_marker_path = pin_marker_path.transformed(transforms.Affine2D().rotate_deg(180))
    pin_marker_path = pin_marker_path.transformed(transforms.Affine2D().translate(0, 22))
    return pin_marker_path

# Lade das Natural Earth Shapefile von deinem lokalen Speicherplatz
shapefile_path = './ne_110m_admin_0_countries.shp'
world = gpd.read_file(shapefile_path)

# Rest wie gehabt: 
europe = world[(world['CONTINENT'] == 'Europe') &
               (~world['NAME'].isin(['Russia', 'Greenland', 'French Guiana']))]

# Städte koordinaten (in WGS84)
cities = {
    "Dresden": (51.0504, 13.7373),
    "Ljubljana": (46.0569, 14.5058),
    "München": (48.1351, 11.5820),
    "Manchester": (53.4808, -2.2426),
    "Leuven": (50.8798, 4.7005),
    "Groningen": (53.2194, 6.5665),
    "Louvain-la-Neuve": (50.6683, 4.6114),
    "Bergen": (60.3913, 5.3221),
    "Turin": (45.0703, 7.6869),
    "Mailand": (45.4642, 9.1900),
    "Navarra": (42.8125, -1.6458),
    "Aarhus": (56.1629, 10.2039),
    "Stockholm": (59.3293, 18.0686),
    "Villigen": (47.533333,8.216667),
    "Bern": (46.948056,7.4475)
}

partners = {
"Boston": (42.35843, -71.05977),
"Delft": (52.00667, 4.35556),
"Wien": (48.20849, 16.37208),
"Ljubljana": (46.0569, 14.5058),
"Zürich": (47.36667, 8.55),
"Erlangen": (49.59099, 11.00783),
"Darmstadt": (49.87167, 8.65027),
"München": (48.1351, 11.5820),
"Stockholm": (59.3293, 18.0686),
"Pavia": (45.19205, 9.15917),
"Turin": (45.07049, 7.68682),
"Heidelberg": (49.40768, 8.69079),
"Bergen": (60.3913, 5.3221),
"Trondheim": (63.43049, 10.39506),
"Villigen": (47.533333, 8.216667),
"Brüssel": (50.85045, 4.34878)
}
city_points = [Point(lon, lat) for lat, lon in cities.values()]
city_gdf = gpd.GeoDataFrame({'city': list(cities.keys())}, geometry=city_points, crs='EPSG:4326')

partner_city_points = [Point(lon, lat) for lat, lon in partners.values()]
partner_city_gdf = gpd.GeoDataFrame({'city': list(partners.keys())}, geometry=partner_city_points, crs='EPSG:4326')



# Projektion: Web Mercator
europe = europe.to_crs(epsg=3857)
city_gdf = city_gdf.to_crs(epsg=3857)
partner_city_gdf = partner_city_gdf.to_crs(epsg=3857)

# Punktwolke in den Ländergrenzen
xmin, ymin, xmax, ymax = europe.total_bounds
n_points = 200000  # Anzahl Punkte, ggf. anpassen
x = np.random.uniform(xmin, xmax, n_points)
y = np.random.uniform(ymin, ymax, n_points)
points = gpd.GeoDataFrame(
    geometry=[Point(x_, y_) for x_, y_ in zip(x, y)],
    crs='EPSG:3857'
)

# points = gpd.sjoin(points, europe, how='inner', predicate='within')

# Deine gewünschten Grenzen in WGS84 (Länge/Breite in Grad)
lon_min, lon_max = -10, 36   # z.B. Westeuropa bis Osteuropa
lat_min, lat_max = 35, 71    # Südeuropa bis Nordeuropa

# Umrechnen in EPSG:3857
project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
x_min, y_min = project(lon_min, lat_min)
x_max, y_max = project(lon_max, lat_max)

# Plotten
fig, ax = plt.subplots(figsize=(12, 12))
# points.plot(ax=ax, color='grey', markersize=0.2, alpha=0.7)

ax.set_xlim([x_min, x_max])
ax.set_ylim([y_min, y_max])

# hintergrund und landesgrenzen
europe.plot(ax=ax, 
            color='white', 
            hatch="oooo",
            edgecolor='grey',
            alpha=0.6,
            linewidth=1)
europe.boundary.plot(ax=ax, color='white', linewidth=2)

marker1 = teardrop_marker(scale=10)
marker = teardrop_from_svg()

# Rote Teardrop Marker für Städte
for idx, row in city_gdf.iterrows():
    plt.scatter(row.geometry.x, row.geometry.y, marker=marker, s=3000, zorder=10, color="red", edgecolors="white", linewidths=1)

ax.set_axis_off()
plt.tight_layout()
# plt.show()
plt.savefig("europe_map.png", dpi=300, format="png")


fig, ax = plt.subplots(figsize=(12, 12))
# points.plot(ax=ax, color='grey', markersize=0.2, alpha=0.7)

ax.set_xlim([x_min, x_max])
ax.set_ylim([y_min, y_max])

# hintergrund und landesgrenzen
europe.plot(ax=ax, 
            color='white', 
            hatch="oooo",
            edgecolor='grey',
            alpha=0.6,
            linewidth=1)
europe.boundary.plot(ax=ax, color='white', linewidth=2)

marker1 = teardrop_marker(scale=10)
marker = teardrop_from_svg()

# Rote Teardrop Marker für Städte
for idx, row in partner_city_gdf.iterrows():
    plt.scatter(row.geometry.x, row.geometry.y, marker=marker, s=3000, zorder=10, color="steelblue", edgecolors="white", linewidths=1)


ax.set_axis_off()
plt.tight_layout()
# plt.show()
plt.savefig("europe_map_partners.png", dpi=300, format="png")




fig, ax = plt.subplots(figsize=(12, 12))
# points.plot(ax=ax, color='grey', markersize=0.2, alpha=0.7)
ax.set_axis_off()

ax.set_xlim([x_min, x_max])
ax.set_ylim([y_min, y_max])


ax.set_axis_off()
plt.tight_layout()
# plt.show()
plt.savefig("europe_map_pins.png", dpi=300, format="png")

