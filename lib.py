# coding: utf-8
import re
from collections import deque
import datetime, time
import math
from xml.dom import minidom


def getPointsFromFile(traceFile):
    """ Prend le chemin d'un fichier  kml de Mercury 100 ou gpx et retourne un tableau de points 
    (un point est un dictionnaire de 'lat' 'lon' 'ele' et 'time').
    """
    g = minidom.parse(traceFile)
    if g.getElementsByTagName('gpx'):
        return getPointsFromGpx(g)
    elif g.getElementsByTagName('kml'):
        return getPointsFromMercuryFile(traceFile)
    else:
        return []  #echec -no points


def getPointsFromGpx(g):
    """ g est une instance de minidom.parse, renvoi un tableau de points """
    #test des trkpt ou des wpt
    t = g.getElementsByTagName('trkpt')
    if not t: t = g.getElementsByTagName('wpt')
    if not t: t = g.getElementsByTagName('rtept')
    ptime = datetime.datetime.now()
    points = []
    segment = 1 # todo gérer les segments
    order_num = 0
    current_lat, current_lon =0,0
    for tp in t:
        lat = float(str.replace(str(tp.getAttribute('lat')), ',', '.'))
        lon = float(str.replace(str(tp.getAttribute('lon')), ',', '.'))
        elNode = tp.getElementsByTagName('ele')
        if elNode:
            ele = float(str.replace(str(elNode[0].firstChild.data), ',', '.'))
        else:
            ele = 0
        timenode = tp.getElementsByTagName('time')
        if timenode:
            try:
                time_format = '%Y-%m-%dT%H:%M:%SZ'
                ptime = datetime.datetime.fromtimestamp(
                    time.mktime(time.strptime(tp.getElementsByTagName('time')[0].firstChild.data, time_format)))
            except:
                try:
                    time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
                    ptime = datetime.datetime.fromtimestamp(
                        time.mktime(time.strptime(tp.getElementsByTagName('time')[0].firstChild.data, time_format)))
                except:
                    time_format = '%Y-%m-%d %H:%M:%SZ'
                    ptime = datetime.datetime.fromtimestamp(
                        time.mktime(time.strptime(tp.getElementsByTagName('time')[0].firstChild.data, time_format)))
        #deal with extension extensions node
        hrNode = tp.getElementsByTagName('gpxtpx:hr')
        hr = int(hrNode[0].firstChild.data) if hrNode else 0

        if not(lat==current_lat and lon== current_lon):
            order_num += 1
            points.append({"segment": segment, "order_num": order_num, "lon": lon, "lat": lat, "elevation": ele, "time": ptime, "heartrate":hr})
            current_lat, current_lon = lat, lon
    points = setDistancesSpeedsAndHeadings(points)
    #check points


    return points


def setDistancesSpeedsAndHeadings(points):
    #TODO headings
    #distances ..
    dist, current_lat, current_lon = 0,points[0]['lat'],points[0]['lon']
    for p in points:
        x = getDistance(current_lat, current_lon, float(p['lat']), float(p['lon']))
        current_lat, current_lon = float(p['lat']), float(p['lon'])
        dist = dist + x
        p['distance'] = dist

    # pour chaque p on calcule la vitesse (d/t entre p+1 et p-1)
    segment = 1
    length = len(points)
    newseg = True
    for i in range(0, length):
        if newseg and i < length-1:
            #premier point d'un segment
            td = points[i+1]['time']-points[i]['time']
            x = points[i+1]['distance']-points[i]['distance']
            points[i]['speed'] = 3600 * x / (td.seconds) if td.seconds > 0 else 0
            newseg = False
        elif (i >= length-1):
            #dernier point
            points[i]['speed'] = points[i-1]['speed']
        else:
            #tous les autres points (si td > 30 secondes on démarre un nouveau segment
            td = points[i+1]['time'] - points[i-1]['time']
            if td.seconds < 60:
                x = points[i+1]['distance'] - points[i-1]['distance']
                points[i]['speed'] = 3600 * x / (td.seconds) if td.seconds > 0 else 0
                #track for valeur aberrante
                if points[i]['speed'] > 50 * points[i-1]['speed'] and points[i-1]['speed'] > 0: points[i]['speed'] = points[i-1]['speed']
            else:
                newseg = True
                segment = segment + 1
                points[i]['speed']= points[i-1]['speed'] #en bout de segment on affecte la valeur du point précédent (à discuter plutôt que 0)
        points[i]['segment']= segment
    return points


def getDistanceAB(A, B):
    """ A et B sont des tuplés lat,lon
    """
    return getDistance(A[0], A[1], B[0], B[1])


def getDistance(latX, lonX, latY, lonY):
    if latX == 0.0:
        return 0.0
    lat1, lng1 = math.radians(latX), math.radians(lonX)
    lat2, lng2 = math.radians(latY), math.radians(lonY)

    sin_lat1, cos_lat1 = math.sin(lat1), math.cos(lat1)
    sin_lat2, cos_lat2 = math.sin(lat2), math.cos(lat2)

    delta_lng = lng2 - lng1
    cos_delta_lng, sin_delta_lng = math.cos(delta_lng), math.sin(delta_lng)

    central_angle = math.acos(min(1.0, sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lng))

    # From http://en.wikipedia.org/wiki/Great_circle_distance:
    #   Historically, the use of this formula was simplified by the
    #   availability of tables for the haversine function. Although this
    #   formula is accurate for most distances, it too suffers from
    #   rounding errors for the special (and somewhat unusual) case of
    #   antipodal points (on opposite ends of the sphere). A more
    #   complicated formula that is accurate for all distances is: (below)

    d = math.atan2(math.sqrt((cos_lat2 * sin_delta_lng) ** 2 +
                             (cos_lat1 * sin_lat2 -
                              sin_lat1 * cos_lat2 * cos_delta_lng) ** 2),
                   sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lng)

    return 6371 * d

def getQuickDistance(latX, lonX, latY, lonY):
    R = 6371  #radius of the earth in km
    x = (lonY - lonX)*math.pi/180 * math.cos( 0.5*(latY+latX)*math.pi/180)
    y = (latY - latX)*math.pi/180
    return R * math.sqrt( x*x + y*y )


def getLatLonBounds(points):
    """ prend un tableau de points en parametre et renvoie un dictionnaire avec les bounds """
    pstart = points[0]
    t = {'maxlat': pstart['lat'], 'maxlon': pstart['lon'], 'minlat': pstart['lat'], 'minlon': pstart['lon']}
    for p in points:
        if p['lat'] > t['maxlat']:
            t['maxlat'] = p['lat']
        if p['lon'] > t['maxlon']:
            t['maxlon'] = p['lon']
        if p['lat'] < t['minlat']:
            t['minlat'] = p['lat']
        if p['lon'] < t['minlon']:
            t['minlon'] = p['lon']
    return t

#TODO include real segment feature
def createGpxXml(points, name):
    "Prend un tableau de point et un nom de trace et renvoie un fichier gpx"
    from xml.dom.minidom import Document

    doc = Document()
    maincard = doc.createElement("gpx")
    maincard.setAttribute("version", "1.0")
    maincard.setAttribute("creator", "Python GPX lib B.Damay V0.1 beta")
    maincard.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    maincard.setAttribute("xmlns", "http://www.topografix.com/GPX/1/0")
    maincard.setAttribute("xsi:schemaLocation",
                          "http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd")
    doc.appendChild(maincard)

    p1 = doc.createElement("time")
    maincard.appendChild(p1)
    ptext1 = doc.createTextNode((points[0]['time']))
    p1.appendChild(ptext1)

    b = getLatLonBounds(points)
    bounds = doc.createElement("bounds")
    bounds.setAttribute('minlat', b['minlat'])
    bounds.setAttribute('minlon', b['minlon'])
    bounds.setAttribute('maxlat', b['maxlat'])
    bounds.setAttribute('maxlon', b['maxlon'])
    maincard.appendChild(bounds)

    trkNode = doc.createElement("trk")
    maincard.appendChild(trkNode)
    nameNode = doc.createElement("name")
    nameNode.appendChild(doc.createTextNode(name))
    trkNode.appendChild(nameNode)
    trkSegNode = doc.createElement("trkseg")
    trkNode.appendChild(trkSegNode)

    for pt in points:
        trkPointNode = doc.createElement("trkpt")
        trkPointNode.setAttribute('lat', (pt['lat']))
        trkPointNode.setAttribute('lon', (pt['lon']))
        trkSegNode.appendChild(trkPointNode)
        eleNode = doc.createElement('ele')
        eleNode.appendChild(doc.createTextNode((pt['ele'])))
        trkPointNode.appendChild(eleNode)
        timeNode = doc.createElement('time')
        timeNode.appendChild(doc.createTextNode((pt['time'])))
        trkPointNode.appendChild(timeNode)
    return doc


def getPointsFromMercuryFile(traceFile):
    f = open(traceFile)
    points = []
    times = []
    tmp_points = []

    for line in f:
        if re.search('<coordinates>', line):
            tmp = re.split(' |,', line)
            for t in tmp:
                if re.search('\d+', t):
                    tmp_points.append(t)

        if re.search('<!-- MERCURY', line):
            tmp_times = re.split(' |,', line)
            for t in tmp_times:
                if re.search('\d\d/\d\d/\d\d\d\d', t):
                    dt = t
                    date = dt[6:] + '-' + dt[0:2] + '-' + dt[3:5]
                if re.search('\d\d:\d\d:\d\d', t):
                    times.append(date + 'T' + t + 'Z')

    for i in range(len(tmp_points) // 3):
        points.append({"lon": tmp_points.pop(0), "lat": tmp_points.pop(0), "ele": tmp_points.pop(0)})
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    for p in points:
        p['time'] = datetime.datetime.fromtimestamp(time.mktime(time.strptime(times.pop(0), time_format)))

    points = setDistancesSpeedsAndHeadings(points)
    f.close
    return points