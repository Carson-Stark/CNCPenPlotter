import math
import os
import re
import time
import tkinter as TK
import tkinter.ttk as TTK
from threading import Timer
from xml.etree import ElementTree as ET
import serial
import threading
import random


class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if other == None:
            return False
        return self.x == other.x and self.y == other.y


class Segment:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class Node:
    def __init__(self, value):
        self.value = value
        self.next = None
        self.prev = None


class cycle:
    def __init__(self, List=None):
        self.first = None
        if List != None:
            for item in List:
                self.addLast(Node(item))

    def get_node(self, index):
        current = self.first
        for i in range(index):
            current = current.next
            if current == self.first:
                return None
        return current

    def find(self, value):
        current = self.first
        for i in range(0, self.length()):
            if current.value == value:
                return current
            current = current.next
        return None

    def findLast(self, value):
        current = self.first
        match = None
        for i in range(0, self.length()):
            if current.value == value:
                match = current
            current = current.next
        return match

    def insertAfter(self, node, new_node):
        new_node.prev = node
        new_node.next = node.next
        new_node.next.prev = new_node
        node.next = new_node

    def insertBefore(self, node, new_node):
        self.insertAfter(node.prev, new_node)

    def addLast(self, new_node):
        if self.first == None:
            self.first = new_node
            new_node.next = new_node
            new_node.prev = new_node
        else:
            self.insertAfter(self.first.prev, new_node)

    def addFirst(self, new_node):
        self.addLast(new_node)
        self.first = new_node

    def remove(self, node):
        if self.first.next == self.first:
            self.first = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if self.first == node:
                self.first = node.next

    def length(self):
        count = 0
        current = self.first
        while current != self.first or count == 0:
            current = current.next
            count = count + 1
        return count

    def toList(self):
        List = list()
        current = self.first
        for i in range(0, self.length()):
            List.append(current.value)
            current = current.next
        return List

    def contains(self, value):
        return False if self.find(value) == None else True


machineDemensionsX = 19150
machineDemensionsY = 15364
minDistanceBtwPoints = 0
minDistanceBtwPaths = 0

Scalar = machineDemensionsX/547

Paths = list()
totalDistance = 0
totalTime = 0


def updateSmoothnessNum(new):
    if int(new) > 9:
        smoothnessText["text"] = "Smoothness: " + new
    else:
        smoothnessText["text"] = "Smoothness: " + new + "  "


def is_number(s):
    if s == ".":
        return True
    try:
        float(s)
        return True
    except ValueError:
        return False


root = TK.Tk()
displayPanel = TK.Frame(root)
displayPanel.pack()
canvasFrame = TK.Frame(displayPanel, bd=3, relief="groove")
canvasFrame.pack(side="left", padx=10, pady=10)
C = TK.Canvas(canvasFrame, height=440, width=548, highlightthickness=0)
C.pack()
optionPanel = TK.Frame(displayPanel)
optionPanel.pack(side="top", padx=(0, 10), pady=10)
fileFrame = TK.Frame(optionPanel)
fileFrame.pack(side="top", fill="x")
TK.Label(fileFrame, text="File:").pack(side="left")
fileEntry = TK.Entry(fileFrame)
fileEntry.pack(side="left", fill="x")
smoothnessFrame = TK.Frame(optionPanel)
smoothnessSlider = TK.Scale(smoothnessFrame, showvalue=False, from_=1,
                            to=20, orient="horizontal", command=updateSmoothnessNum, length=90)
smoothnessSlider.set(5)
TK.Button(fileFrame, text="Use", command=lambda: svgToPaths(os.path.join(os.path.dirname(os.path.realpath(
    __file__)), "draw examples", fileEntry.get()), smoothnessSlider.get(), fillVar.get())).pack(side="left")
smoothnessFrame.pack(side="top", fill="x")
smoothnessText = TK.Label(smoothnessFrame, text="Smoothness: 5")
smoothnessText.pack(side="left")
smoothnessSlider.pack(side="left", fill="x")

fillFrame = TK.Frame(optionPanel)
fillFrame.pack(side="top", fill="x")
TK.Label(fillFrame, text="Fill:").pack(side="left")
fillVar = TK.StringVar()
fillVar.set("None")
TK.OptionMenu(fillFrame, fillVar, "None", "Horizontal", "Vertical",
              "Positive Diagonal", "Negative Diagonal", "Center Line").pack(side="left")
penFrame = TK.Frame(optionPanel)
penFrame.pack(side="top", fill="x")

TK.Label(penFrame, text="Pen Diameter:").pack(side="left")
penDEntry = TK.Entry(penFrame, validate="key", validatecommand=(
    root.register(is_number), '%S'), width=6)
penDEntry.insert(0, "1")
penDEntry.pack(side="left", fill="x")
TK.Label(penFrame, text="mm").pack(side="left")

orderFrame = TK.Frame(optionPanel)
orderFrame.pack(side="top", fill="x")
TK.Label(orderFrame, text="Order Paths:").pack(side="left")
orderVar = TK.StringVar()
orderVar.set("Next Closest")
TK.OptionMenu(orderFrame, orderVar, "Next Closest", "Top to Bottom",
              "Bottom to Top", "Left to Right", "Right to Left", "Center").pack(side="left")

orderFillFrame = TK.Frame(optionPanel)
orderFillFrame.pack(side="top", fill="x")
TK.Label(orderFillFrame, text="Order Fill:").pack(side="left")
orderFillVar = TK.StringVar()
orderFillVar.set("Next Closest")
TK.OptionMenu(orderFillFrame, orderFillVar, "Next Closest", "Top to Bottom",
              "Bottom to Top", "Left to Right", "Right to Left").pack(side="left")

drawPanel = TK.Frame(root)
drawPanel.pack(fill="x", padx=10, pady=(0, 10))

# region svgToPaths


def svgToPaths(filePath, smoothness, fill):
    global Paths
    global totalDistance
    global totalTime
    Paths = list()
    totalDistance = 0
    totalTime = 0

    tree = ET.parse(filePath)
    root = tree.getroot()
    svgNamespace = root.tag[:-3]

    bounds = root.get("viewBox")
    if bounds != None:
        bounds = bounds.split(" ")
        vectorX = float(bounds[2])
        vectorY = float(bounds[3])
    else:
        vectorX = float(root.get("width"))
        vectorY = float(root.get("height"))
    print(vectorX)
    print(vectorY)

    C.delete("all")

    if (vectorX > vectorY and (vectorX < machineDemensionsX or vectorY < machineDemensionsY)) or (machineDemensionsX > machineDemensionsY and (vectorX > machineDemensionsX and vectorY > machineDemensionsY)):
        Sclr = machineDemensionsX/vectorX
        Xshift = 0
        Yshift = machineDemensionsY/2-(vectorY/2*Sclr)
        C.create_line(machineDemensionsX/Scalar, Yshift/Scalar,
                      0, Yshift/Scalar, fill="red", dash=(1, 2))
        C.create_line(machineDemensionsX/Scalar, (vectorY*Sclr+Yshift) /
                      Scalar, 0, (vectorY*Sclr+Yshift)/Scalar, fill="red", dash=(1, 2))
    else:
        Sclr = machineDemensionsY/vectorY
        Xshift = machineDemensionsX/2-(vectorX/2*Sclr)
        Yshift = 0
        C.create_line(Xshift/Scalar, machineDemensionsY/Scalar,
                      Xshift/Scalar, 0, fill="red", dash=(1, 2))
        C.create_line((vectorX*Sclr+Xshift)/Scalar, machineDemensionsY /
                      Scalar, (vectorX*Sclr+Xshift)/Scalar, 0, fill="red", dash=(1, 2))

    fileEntry.delete(0, "end")
    fileEntry.insert(0, "uploading...")
    C.update_idletasks()

    groups = root.findall(".//" + svgNamespace + "g")
    vectorGroups = list()
    for group in groups:
        style = group.get("style")
        if style == None:
            filled = 0
        elif style.find("fill:none") > -1:
            filled = 0
        else:
            filled = 1
        translateX = 0
        translateY = 0
        transform = group.get("transform")
        if transform != None:
            translateX = float(
                transform[transform.index("(")+1:-1].split(",")[0])
            translateY = float(
                transform[transform.index("(")+1:-1].split(",")[1])
        vectorGroups.append([filled, Coordinate(translateX, translateY), group.findall(
            svgNamespace + "path"), group.findall(svgNamespace + "ellipse")])
    vectorGroups.append([False, Coordinate(0, 0), root.findall(
        svgNamespace + "path"), root.findall(svgNamespace + "ellipse")])

    borderPaths = list()
    filledPaths = list()
    nonzeroFilledPaths = list()
    evenoddFilledPaths = list()
    newVPath = False
    for vectorGroup in vectorGroups:
        pathGroup = list()
        for vectorPath in vectorGroup[2]:
            newVPath = True
            path = list()
            evenoddPath = list()
            nonzeroPath = list()
            d = vectorPath.get("d").replace("\n", " ").replace("\r", "")
            if not vectorGroup[0]:
                style = vectorPath.get("style")
                rule = vectorPath.get("fill-rule")
                if style != None:
                    filled = 0 if style.find("fill:none") > -1 else 1
                elif rule != None:
                    filled = 2 if rule.find("nonzero") > -1 else 3
                else:
                    filled = 0
            else:
                filled = 1
            commands = re.findall(
                "[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*", d)
            lastCurveC2 = None
            for command in commands:
                lastPoint = lastCoordInPath(path)
                if bool(re.search("[MmLl]", command)):  # move/line
                    if (command[0] == "M" or command[0] == "m") and len(path) > 0:
                        if len(path) > 0:
                            pathGroup.append(path)
                            borderPaths.append(path)
                            if filled == 1:
                                filledPaths.append(path)
                            elif filled == 2:
                                nonzeroPath.append(path)
                            elif filled == 3:
                                evenoddPath.append(path)
                            path = list()
                        lastPoint = None
                    if lastPoint == None:
                        if len(borderPaths) == 0 or newVPath:
                            lastPoint = Coordinate(0, 0)
                        else:
                            lastPath = borderPaths[len(borderPaths)-1]
                            lastPoint = lastPath[len(lastPath)-1]
                    path.extend(findPointsInCommand(
                        command, command[0] == "m" or command[0] == "l", lastPoint, 1))
                elif str.lower(command[0]) == "h":  # horizontal line
                    for parameter in re.findall(r"[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?", command):
                        if float(parameter) != 0:
                            path.append(Coordinate(float(
                                parameter) + lastPoint.x if command[0] == "h" else float(parameter), lastPoint.y))
                elif str.lower(command[0]) == "v":  # vertical line
                    for parameter in re.findall(r"[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?", command):
                        if float(parameter) != 0:
                            path.append(Coordinate(lastPoint.x, float(
                                parameter) + lastPoint.y if command[0] == "v" else float(parameter)))
                elif bool(re.search("[CcQqSsTt]", command)):  # beizer curve
                    degree = 3 if bool(re.search("[Cc]", command)) else (
                        2 if bool(re.search("[QqSs]", command)) else 1)
                    points = findPointsInCommand(command, bool(
                        re.search("[cqst]", command)), lastPoint, degree)
                    results = findPointsOnCurve(degree, points, lastPoint, bool(re.search(
                        "[CcSsQqTt]", commands[commands.index(command)-1])), bool(re.search("[SsTt]", command)), lastCurveC2, smoothness)
                    path.extend(results[0])
                    lastCurveC2 = results[1]
                elif str.lower(command[0]) == "a":  # elliptical arc
                    parameters = list(map(float, re.findall(
                        r"[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?", command)))
                    for i in range(0, int(len(parameters) / 7)):
                        x = parameters[i*7 +
                                       5] if command[0] == "A" else parameters[i*7+5] + lastPoint.x
                        y = parameters[i*7 +
                                       6] if command[0] == "A" else parameters[i*7+6] + lastPoint.y
                        para = [lastPoint, Coordinate(
                            x, y), parameters[i*7], parameters[i*7+1], parameters[i*7+2], parameters[i*7+3], parameters[i*7+4]]
                        centerParams = findCenterParam(
                            para[0], para[1], para[2], para[3], para[4], para[5], para[6], Sclr, Xshift, Yshift)
                        interval = centerParams[3]/smoothness
                        t = centerParams[2]
                        for j in range(0, smoothness+1):
                            path.append(ellipseArc(
                                t, para[2], para[3], para[4], centerParams[0], centerParams[1]))
                            t += interval
                        lastPoint = path[len(path)-1]
                elif command[0] == "Z" or command[0] == "z":  # closePath
                    if len(path) > 0:
                        if path[0] != lastPoint:
                            path.append(Coordinate(path[0].x, path[0].y))
                newVPath = False
            if len(path) > 0:
                pathGroup.append(path)
                borderPaths.append(path)
                if filled == 1:
                    filledPaths.append(path)
                elif filled == 2:
                    nonzeroPath.append(path)
                    nonzeroFilledPaths.append(nonzeroPath)
                elif filled == 3:
                    evenoddPath.append(path)
                    evenoddFilledPaths.append(evenoddPath)
        for e in vectorGroup[3]:
            path = list()
            interval = 2*math.pi/smoothness
            t = 0
            for i in range(0, smoothness + 1):
                path.append(ellipse(t, float(e.get("cx")), float(
                    e.get("cy")), float(e.get("rx")), float(e.get("ry"))))
                t += interval
            pathGroup.append(path)
        for p in pathGroup:
            for coord in p:
                coord.x += vectorGroup[1].x
                coord.y += vectorGroup[1].y

    for Path in borderPaths:
        for point in Path:
            point.x = round(point.x * Sclr + Xshift)
            point.y = round(point.y * Sclr + Yshift)

    removeDuplicates(borderPaths, minDistanceBtwPoints)
    mergePaths(borderPaths, minDistanceBtwPaths)

    fillGroups = list()
    if fillVar.get() != "None":
        if filled == 1:
            copyOfPaths = list(filledPaths)
            copyOfPaths.sort(key=areaOfPath, reverse=True)
            count = 0
            count1 = 0
            for p1 in copyOfPaths:
                count += 1
                count1 = 0
                if p1 not in filledPaths:
                    fileEntry.delete(0, "end")
                    fileEntry.insert(0, "filling(" + str(count) + "/" + str(len(copyOfPaths)) +
                                     ")(1/3)..." + str(round(100*(count1/(len(copyOfPaths))))) + "%")
                    C.update_idletasks()
                    continue
                holes = list()
                for p2 in copyOfPaths:
                    count1 += 1
                    fileEntry.delete(0, "end")
                    fileEntry.insert(0, "filling(" + str(count) + "/" + str(len(copyOfPaths)) +
                                     ")(1/3)..." + str(round(100*(count1/(len(copyOfPaths))))) + "%")
                    C.update_idletasks()

                    if p2 not in filledPaths or p1 == p2:
                        continue
                    if pathContainedInPath(p1, p2):
                        invalid = False
                        for hole in holes:
                            if pathContainedInPath(hole, p2):
                                invalid = True
                                break
                        if not invalid:
                            filledPaths.remove(p2)
                            holes.append(p2)
                fpaths = fillPath(float(penDEntry.get()) *
                                  100, p1, holes, copyOfPaths)
                if len(fpaths) > 0:
                    fillGroups.append(fpaths)
        elif filled == 2:
            for paths in nonzeroFilledPaths:
                paths.sort(key=areaOfPath, reverse=True)
                print("sorted")
                for path in paths:
                    print(str(paths.index(path))+"/"+str(len(paths)))
                    holes = list()
                    for p in paths:
                        if p == path:
                            continue
                        if pathContainedInPath(path, p):
                            holes.append(p)
                    print("done")
                    point = getPointInsidePath(path, holes)
                    print("done2")
                    intersections = 0
                    for _path in paths:
                        lp = None
                        for p in _path:
                            if lp != None:
                                if doIntersect(point, Coordinate(point.x + machineDemensionsX, point.y), p, lp):
                                    if not onSegment(lp, point, Coordinate(point.x + machineDemensionsX, point.y), 0) or not doIntersect(path[path.index(lp)-1], p, point, Coordinate(point.x + machineDemensionsX, point.y)):
                                        if orientation(cycle(list([p, point, lp]))) == 1:
                                            intersections += 1
                                        else:
                                            intersections -= 1
                            lp = p
                    print("I:" + str(intersections))
                    if intersections != 0:
                        fillGroups.append(
                            fillPath(float(penDEntry.get())*100, path, holes, paths))
        elif filled == 3:
            # fill even odd paths
            for paths in evenoddFilledPaths:
                paths.sort(key=areaOfPath, reverse=True)
                print("sorted")
                for path in paths:
                    print(str(paths.index(path))+"/"+str(len(paths)))
                    holes = list()
                    for p in paths:
                        if p == path:
                            continue
                        if pathContainedInPath(path, p):
                            holes.append(p)
                    print("done")
                    point = getPointInsidePath(path, holes)
                    print("done2")
                    intersections = 0
                    for _path in paths:
                        lp = None
                        for p in _path:
                            if lp != None:
                                if doIntersect(point, Coordinate(point.x + machineDemensionsX, point.y), p, lp):
                                    if not onSegment(lp, point, Coordinate(point.x + machineDemensionsX, point.y), 0) or not doIntersect(path[path.index(lp)-1], p, point, Coordinate(point.x + machineDemensionsX, point.y)):
                                        intersections += 1
                            lp = p
                    print(intersections)
                    if intersections % 2 > 0:
                        fillGroups.append(
                            fillPath(float(penDEntry.get())*100, path, holes, paths))

    fileEntry.delete(0, "end")
    fileEntry.insert(0, filePath.split('\\')[-1])
    C.update_idletasks()

    # order paths
    orderedPaths = list()
    lastPoint = Coordinate(machineDemensionsX, machineDemensionsY)
    nextPath = borderPaths[0]
    shortestDist = math.inf
    paths = list(borderPaths)
    for i in range(0, len(borderPaths)):
        for Path in paths:
            if orderVar.get() == "Next Closest":
                dist1 = Distance(lastPoint, Path[0])
                dist2 = Distance(lastPoint, Path[len(Path)-1])
            elif orderVar.get() == "Top to Bottom":
                dist1 = Path[0].y
                dist2 = Path[len(Path)-1].y
            elif orderVar.get() == "Bottom to Top":
                dist1 = machineDemensionsY-Path[0].y
                dist2 = machineDemensionsY-Path[len(Path)-1].y
            elif orderVar.get() == "Left to Right":
                dist1 = Path[0].x
                dist2 = Path[len(Path)-1].x
            elif orderVar.get() == "Right to Left":
                dist1 = machineDemensionsX-Path[0].x
                dist2 = machineDemensionsX-Path[len(Path)-1].x
            else:
                dist1 = Distance(Coordinate(
                    machineDemensionsX/2, machineDemensionsY/2), Path[0])
                dist2 = Distance(Coordinate(
                    machineDemensionsX/2, machineDemensionsY/2), Path[len(Path)-1])

            if dist1 < shortestDist:
                nextPath = Path
                shortestDist = dist1
            elif dist2 < shortestDist:
                Path.reverse()
                nextPath = Path
                shortestDist = dist2
        orderedPaths.append(nextPath)
        lastPoint = nextPath[len(nextPath)-1]
        shortestDist = math.inf
        paths.remove(nextPath)

    # order fill groups
    if len(fillGroups) > 0:
        lastPoint = orderedPaths[len(
            orderedPaths)-1][len(orderedPaths[len(orderedPaths)-1])-1]
        nextGroup = fillGroups[0]
        shortestDist = math.inf
        groups = list(fillGroups)
        for i in range(0, len(fillGroups)):
            for group in groups:
                dist = Distance(lastPoint, group[0][0])
                if dist < shortestDist:
                    nextGroup = group
                    shortestDist = dist
            orderedPaths.extend(nextGroup)
            lastPoint = nextGroup[len(nextGroup) -
                                  1][len(nextGroup[len(nextGroup)-1])-1]
            shortestDist = math.inf
            groups.remove(nextGroup)

    for group in fillGroups:
        for Path in group:
            last = None
            for coord in Path:
                if last != None:
                    C.create_line(coord.x/Scalar, coord.y/Scalar,
                                  last.x/Scalar, last.y/Scalar, fill="gray")
                last = coord
    for Path in borderPaths:
        last = None
        for coord in Path:
            if last != None:
                C.create_line(coord.x/Scalar, coord.y/Scalar,
                              last.x/Scalar, last.y/Scalar)
            last = coord

    Paths = list(orderedPaths)
    stepsInAcceleration = (1000/((200+800)/2)) * 500
    lastPoint = Coordinate(0, 0)
    for path in Paths:
        totalTime += 0.75
        for point in path:
            dist = Distance(lastPoint, point)
            if dist != 0:
                totalDistance += dist
                if dist >= stepsInAcceleration*2:
                    totalTime += 0.5*2 + (dist-(stepsInAcceleration*2))*0.0002
                else:
                    ratio = dist/stepsInAcceleration
                    totalTime += 0.5 * ratio
            lastPoint = point
    distance["text"] = "Distance: 0/" + str(round(totalDistance/100)) + "mm"
    _time["text"] = "Time: 0:0/" + \
        str(int(totalTime/60)) + ":" + str(round(totalTime) % 60)


def removeDuplicates(paths, minimumDist):  # remove duplicates from path
    for Path in paths:
        lp = Path[len(Path)-1]
        count = 0
        copyOfPath = list(Path)
        for point in copyOfPath:
            if count != 0 and Distance(point, lp) <= minimumDist:
                Path.reverse()
                Path.remove(point)
                Path.reverse()
                if len(Path) <= 0:
                    paths.remove(Path)
            else:
                lp = Coordinate(point.x, point.y)
            count += 1


def mergePaths(paths, minDist):  # merge paths with the same endpoint
    for P1 in paths:
        p1 = P1[len(P1)-1]
        pointRemoved = True
        while pointRemoved:
            pointRemoved = False
            for P2 in paths:
                p2 = P2[0]
                if P1 != P2 and Distance(p1, p2) <= minDist:
                    P2.remove(p2)
                    P1.extend(P2)
                    paths.remove(P2)
                    pointRemoved = True
                    break


def reflectPoint(p1, p2):
    return Coordinate(-(p1.x-p2.x)+p2.x, -(p1.y-p2.y)+p2.y)


def lastCoordInPath(path):
    if len(path) == 0:
        return None
    else:
        return path[len(path)-1]


def addCoords(c1, c2):
    return Coordinate(c1.x + c2.x, c1.y + c2.y)


def subCoords(c1, c2):
    return Coordinate(c1.x - c2.x, c1.y - c2.y)


def findPointsInCommand(command, relative, lastPoint, pointsInCommand):
    lp = lastPoint
    points = list()
    x = None
    i = 0
    for parameter in re.findall(r"[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?", command):
        if x == None:
            x = float(parameter) if not relative else float(parameter) + lp.x
        else:
            points.append(Coordinate(x, float(parameter)
                                     if not relative else float(parameter) + lp.y))
            x = None
            i = i+1
            if i == pointsInCommand:
                lp = lastCoordInPath(points)
                i = 0
    return points


def findPointsOnCurve(degree, points, lastPoint, lastCommandCurve, smooth, lastCurve, smoothness):
    path = list()
    lastCurveC2 = lastCurve
    lp = lastPoint
    for i in range(0, int(len(points) / degree)):
        controlPoints = [lp, reflectPoint(
            lastCurveC2, lp) if lastCommandCurve else lp] if smooth else [lp]
        for j in range(0, degree):
            controlPoints.append(points[i*degree+j])
        lastCurveC2 = controlPoints[len(controlPoints)-2]
        lp = controlPoints[len(controlPoints)-1]
        interval = 1/smoothness
        t = interval
        for j in range(0, smoothness):
            path.append(beizerCurve(t, controlPoints))
            t += interval
    return [path, lastCurveC2]


def beizerCurve(t, controlPoints):
    n = len(controlPoints)-1
    x = 0
    y = 0
    for i in range(0, n+1):
        x += nCr(n, i)*math.pow(1-t, n-i)*math.pow(t, i)*controlPoints[i].x
        y += nCr(n, i)*math.pow(1-t, n-i)*math.pow(t, i)*controlPoints[i].y
    return (Coordinate(x, y))


def nCr(n, r):
    f = math.factorial
    return f(n) / f(r) / f(n-r)


def ellipse(t, cx, cy, rx, ry):
    x = rx*math.cos(t)+cx
    y = ry*math.sin(t)+cy
    return Coordinate(x, y)


def findCenterParam(start, end, rx, ry, angle, large, sweep, Sclr, Xshift, Yshift):
    x1p = math.cos(angle) * (start.x - end.x) / 2 + \
        math.sin(angle) * (start.y - end.y) / 2
    y1p = -math.sin(angle) * (start.x - end.x) / 2 + \
        math.cos(angle) * (start.y - end.y) / 2

    L = math.pow(x1p, 2) / math.pow(rx, 2) + math.pow(y1p, 2) / math.pow(ry, 2)
    if L > 1:
        rx = math.sqrt(L) * abs(rx)
        ry = math.sqrt(L) * abs(ry)
    else:
        rx = abs(rx)
        ry = abs(ry)

    n = math.sqrt((math.pow(rx, 2)*math.pow(ry, 2)-math.pow(rx, 2)*math.pow(y1p, 2)-math.pow(ry, 2)
                   * math.pow(x1p, 2))/(math.pow(rx, 2)*math.pow(y1p, 2)+math.pow(ry, 2)*math.pow(x1p, 2)))
    cxp = (n if large != sweep else -n)*(rx*y1p)/ry
    cyp = (n if large != sweep else -n)*(-ry*x1p)/rx
    cx = math.cos(angle)*cxp-math.sin(angle)*cyp+(start.x+end.x)/2
    cy = math.sin(angle)*cxp+math.cos(angle)*cyp+(start.y+end.y)/2
    o1 = vectorAngle(Coordinate(1, 0), Coordinate(
        (x1p - cxp) / rx, (y1p - cyp) / ry))
    do = math.degrees(vectorAngle(Coordinate((x1p - cxp) / rx, (y1p - cyp) / ry),
                                  Coordinate((-x1p - cxp) / rx, (-y1p - cyp) / ry))) % 360
    if sweep == 0 and do > 0:
        do -= 360
    if sweep == 1 and do < 0:
        do += 360
    return [cx, cy, o1, math.radians(do)]


def ellipseArc(t, rx, ry, angle, cx, cy):
    x = rx*math.cos(t)*math.cos(angle) - ry*math.sin(t)*math.sin(angle) + cx
    y = rx*math.cos(t)*math.sin(angle) + ry*math.sin(t)*math.cos(angle) + cy
    return Coordinate(x, y)


def vectorAngle(a, b):
    sign = -1 if a.x * b.y - a.y * b.x < 0 else 1
    aA = math.sqrt(a.x * a.x + a.y * a.y)
    bA = math.sqrt(b.x * b.x + b.y * b.y)
    dot = a.x * b.x + a.y * b.y
    n = dot / (aA * bA)
    if n > 1:
        n = 1
    elif n < -1:
        n = -1
    return sign * math.acos(n)


def findIntersection(p1, q1, p2, q2):
    if not doIntersect(p1, q1, p2, q2):
        return None
    else:
        intersection = Coordinate(0, 0)

    if q1.x - p1.x == 0:
        intersection.x = q1.x
        intersection.y = (q2.y - p2.y) / (q2.x - p2.x) * \
            q1.x + p2.y - ((q2.y - p2.y) / (q2.x - p2.x) * p2.x)
        return intersection
    elif q2.x - p2.x == 0:
        intersection.x = q2.x
        intersection.y = (q1.y - p1.y) / (q1.x - p1.x) * \
            q2.x + p1.y - ((q1.y - p1.y) / (q1.x - p1.x) * p1.x)
        return intersection

    # find the equations of the lines
    m1 = (q1.y - p1.y) / (q1.x - p1.x)
    m2 = (q2.y - p2.y) / (q2.x - p2.x)
    b1 = p1.y - (m1 * p1.x)
    b2 = p2.y - (m2 * p2.x)

    # find intersection by setting both sides equal
    intersection.x = (b1 - b2) / (m2 - m1)
    intersection.y = m1 * intersection.x + b1
    return intersection


def fillPath(penDiameter, path, holes, pathList):
    lines = list()
    line = list()

    MinX = path[0].x
    MinY = path[0].y
    MaxX = path[0].x
    MaxY = path[0].y
    for p in path:
        MinX = min(MinX, p.x)
        MinY = min(MinY, p.y)
        MaxX = max(MaxX, p.x)
        MaxY = max(MaxY, p.y)

    count1 = 1
    step = penDiameter
    count = pathList.index(path)
    done = False
    while not done:
        count1 += 1
        fileEntry.delete(0, "end")
        fileEntry.insert(0, "filling(" + str(count) + "/" + str(len(pathList)) +
                         ")(2/3)..." + str(round(100*(count1/((MaxY-MinY)/penDiameter)))) + "%")
        C.update_idletasks()

        if fillVar.get() == "Horizontal":
            minCoord = Coordinate(MinX, MaxY-step)
            maxCoord = Coordinate(MaxX, MaxY-step)
            done = MaxY-step <= MinY + penDiameter
        elif fillVar.get() == "Vertical":
            minCoord = Coordinate(MinX+step, MinY)
            maxCoord = Coordinate(MinX+step, MaxY)
            done = MaxX-step <= MinX + penDiameter
        elif fillVar.get() == "Positive Diagonal":
            minCoord = Coordinate(MaxX-step, MaxY)
            maxCoord = Coordinate(MaxX, MaxY-step)
            done = (MaxX-MinX)+(MaxY-MinY)-step <= penDiameter
        else:
            minCoord = Coordinate(MinX+step, MaxY)
            maxCoord = Coordinate(MinX, MaxY-step)
            done = (MaxX-MinX)+(MaxY-MinY)-step <= penDiameter

        line = list()
        for h in holes:
            lp = h[len(h)-1]
            for p in h:
                inter = findIntersection(minCoord, maxCoord, p, lp)
                if inter != None and (not onSegment(lp, minCoord, maxCoord, 0) or not doIntersect(h[h.index(lp)-1], p, minCoord, maxCoord)):
                    line.append(inter)
                lp = p
        lp = path[len(path)-1]
        for p in path:
            inter = findIntersection(minCoord, maxCoord, p, lp)
            if inter != None and (not onSegment(lp, minCoord, maxCoord, 0) or not doIntersect(path[path.index(lp)-1], p, minCoord, maxCoord)):
                line.append(inter)
            lp = p
        if len(line) > 0:
            lines.append(line)
        step += penDiameter*math.sqrt(2) if fillVar.get(
        ) == "Positive Diagonal" or fillVar.get() == "Negative Diagonal" else penDiameter

    strokes = list()
    for l in lines:
        L = l[0]
        l.sort(key=lambda x: Distance(x, Coordinate(0, L.y)))
        stroke = list()
        for p in l:
            stroke.append(p)
            if len(stroke) == 2:
                strokes.append(stroke)
                stroke = list()

    if len(strokes) == 0:
        return strokes

    copyOfStrokes = list(strokes)
    orderedPaths = list()
    currentPath = strokes[0]
    nextPath = strokes[0]
    nextPathStart = strokes[0]
    shortestDist = math.inf
    shortestDistValid = math.inf
    reverseStartPath = False
    reverseNewPath = False
    orderedStrokes = list(strokes)
    lastIndex = 0
    direction = True
    previousStep = 0
    for i in range(0, len(strokes)):
        fileEntry.delete(0, "end")
        fileEntry.insert(0, "filling(" + str(count) + "/" + str(len(pathList)) +
                         ")(3/3)..." + str(round(100*(i/len(copyOfStrokes)))) + "%")
        C.update_idletasks()

        for Path in orderedStrokes:
            dist1 = Distance(currentPath[len(currentPath)-1], Path[0])
            dist2 = Distance(currentPath[len(currentPath)-1], Path[1])

            if orderFillVar.get() == "Next Closest":
                ndist1 = Distance(lastPoint, Path[0])
                ndist2 = Distance(lastPoint, Path[len(Path)-1])
            elif orderFillVar.get() == "Top to Bottom":
                ndist1 = Path[0].y
                ndist2 = Path[len(Path)-1].y
            elif orderFillVar.get() == "Bottom to Top":
                ndist1 = machineDemensionsY-Path[0].y
                ndist2 = machineDemensionsY-Path[len(Path)-1].y
            elif orderFillVar.get() == "Left to Right":
                ndist1 = Path[0].x
                ndist2 = Path[len(Path)-1].x
            else:
                ndist1 = machineDemensionsX-Path[0].x
                ndist2 = machineDemensionsX-Path[len(Path)-1].x

            if dist1 > shortestDist and dist2 > shortestDist:
                continue

            notValid1 = False
            notValid2 = False

            # connecting stroke cannot intersect any strokes / skip any strokes
            for p in copyOfStrokes:
                if not notValid1 and doIntersect(currentPath[len(currentPath)-1], Path[0], p[0], p[1]):
                    notValid1 = True
                if not notValid2 and doIntersect(currentPath[len(currentPath)-1], Path[1], p[0], p[1]):
                    notValid2 = True
                if notValid1 and notValid2:
                    break

            for hole in holes:
                if notValid1 and notValid2:
                    break

                # midpoint of connecting stroke cannot lie inside any holes
                if not notValid1 and pointInsidePath(hole, Coordinate((currentPath[len(currentPath)-1].x + Path[0].x)/2, (currentPath[len(currentPath)-1].y + Path[0].y)/2), penDiameter/50, True):
                    notValid1 = True
                if not notValid2 and pointInsidePath(hole, Coordinate((currentPath[len(currentPath)-1].x + Path[1].x)/2, (currentPath[len(currentPath)-1].y + Path[1].y)/2), penDiameter/50, True):
                    notValid2 = True

                if notValid1 and notValid2:
                    break

                # connecting stroke cannot intersect any holes
                intersecting1 = False
                intersecting2 = False
                sp1 = hole[0]
                sDist1 = math.inf
                sp2 = hole[0]
                sDist2 = math.inf
                ep1 = hole[0]
                eDist1 = math.inf
                ep2 = hole[0]
                eDist2 = math.inf
                lastP = hole[len(hole)-1]
                for p in hole:
                    if not intersecting1 and doIntersect(currentPath[len(currentPath)-1], Path[0], p, lastP) and not onSegment(Path[0], p, lastP, penDiameter/2) and not onSegment(currentPath[len(currentPath)-1], p, lastP, penDiameter/2):
                        intersecting1 = True
                        np = findIntersection(
                            currentPath[len(currentPath)-1], Path[0], p, lastP)
                        if Distance(np, currentPath[len(currentPath)-1]) < sDist1:
                            sp1 = np
                            sDist1 = Distance(
                                np, currentPath[len(currentPath)-1])
                        if Distance(np, Path[0]) < eDist1:
                            ep1 = np
                            eDist1 = Distance(np, Path[0])
                    if not intersecting2 and doIntersect(currentPath[len(currentPath)-1], Path[1], p, lastP) and not onSegment(Path[1], p, lastP, penDiameter/2) and not onSegment(currentPath[len(currentPath)-1], p, lastP, penDiameter/2):
                        intersecting2 = True
                        np = findIntersection(
                            currentPath[len(currentPath)-1], Path[1], p, lastP)
                        if Distance(np, currentPath[len(currentPath)-1]) < sDist2:
                            sp2 = np
                            sDist2 = Distance(
                                np, currentPath[len(currentPath)-1])
                        if Distance(np, Path[1]) < eDist2:
                            ep2 = np
                            eDist2 = Distance(np, Path[1])

                    if intersecting1 and intersecting2:
                        break
                    lastP = p

                if intersecting1 or intersecting2:
                    shortestDistToStartCW1 = math.inf
                    connectorStartCW1 = hole[0]
                    shortestDistToStartCC1 = math.inf
                    connectorStartCC1 = hole[0]
                    shortestDistToStartCW2 = math.inf
                    connectorStartCW2 = hole[0]
                    shortestDistToStartCC2 = math.inf
                    connectorStartCC2 = hole[0]
                    shortestDistToEndCW1 = math.inf
                    connectorEndCW1 = hole[0]
                    shortestDistToEndCW2 = math.inf
                    connectorEndCW2 = hole[0]
                    shortestDistToEndCC1 = math.inf
                    connectorEndCC1 = hole[0]
                    shortestDistToEndCC2 = math.inf
                    connectorEndCC2 = hole[0]
                    lastP = hole[len(hole)-1]
                    for p in hole:
                        if Distance(p, sp1) < shortestDistToStartCW1 and orientation(cycle(list([sp1, p, ep1]))) == 1:
                            shortestDistToStartCW1 = Distance(p, sp1)
                            connectorStartCW1 = p
                        if Distance(p, sp1) < shortestDistToStartCC1 and orientation(cycle(list([sp1, p, ep1]))) == 2:
                            shortestDistToStartCC1 = Distance(p, sp1)
                            connectorStartCC1 = p
                        if Distance(p, sp2) < shortestDistToStartCW2 and orientation(cycle(list([sp2, p, ep2]))) == 1:
                            shortestDistToStartCW2 = Distance(p, sp2)
                            connectorStartCW2 = p
                        if Distance(p, sp2) < shortestDistToStartCC2 and orientation(cycle(list([sp2, p, ep2]))) == 2:
                            shortestDistToStartCC2 = Distance(p, sp2)
                            connectorStartCC2 = p
                        if Distance(p, ep1) < shortestDistToEndCW1 and orientation(cycle(list([ep1, p, sp1]))) == 1:
                            shortestDistToEndCW1 = Distance(p, ep1)
                            connectorEndCW1 = p
                        if Distance(p, ep1) < shortestDistToEndCC1 and orientation(cycle(list([ep1, p, sp1]))) == 2:
                            shortestDistToEndCC1 = Distance(p, ep1)
                            connectorEndCC1 = p
                        if Distance(p, ep2) < shortestDistToEndCW2 and orientation(cycle(list([ep2, p, sp2]))) == 1:
                            shortestDistToEndCW2 = Distance(p, ep2)
                            connectorEndCW2 = p
                        if Distance(p, ep2) < shortestDistToEndCC2 and orientation(cycle(list([ep2, p, sp2]))) == 2:
                            shortestDistToEndCC2 = Distance(p, ep2)
                            connectorEndCC2 = p
                        lastP = p

                    if intersecting1 and not notValid1:
                        holeCycle = cycle(hole)
                        if orientation(holeCycle) == 2:
                            holeCycle = cycle(hole.__reversed__())

                        totalDist1 = Distance(connectorStartCW1, sp1)
                        totalSlope1 = 0
                        current = holeCycle.find(connectorStartCW1)
                        while current.value != connectorEndCC1:
                            totalDist1 += Distance(current.value,
                                                   current.next.value)
                            totalSlope1 += (current.value.y-current.prev.value.y) / \
                                (current.value.x-current.prev.value.x)
                            current = current.next
                        totalDist1 += Distance(connectorEndCC1, Path[0])

                        totalDist2 = Distance(connectorStartCC1, sp1)
                        totalSlope2 = 0
                        current = holeCycle.find(connectorStartCC1)
                        while current.value != connectorEndCW1:
                            totalDist2 += Distance(current.value,
                                                   current.prev.value)
                            totalSlope2 += (current.value.y-current.prev.value.y) / \
                                (current.value.x-current.prev.value.x)
                            current = current.prev
                        totalDist1 += Distance(connectorEndCW1, ep1)

                        #print (abs(min(totalDist1, totalDist2)-Distance(sp1, ep1)))
                        if abs(min(totalDist1, totalDist2)-Distance(sp1, ep1)) > penDiameter:
                            notValid1 = True

                    if intersecting2 and not notValid2:
                        holeCycle = cycle(hole)
                        if orientation(holeCycle) == 2:
                            holeCycle = cycle(hole.__reversed__())

                        totalDist1 = Distance(connectorStartCW2, sp2)
                        totalSlope1 = 0
                        current = holeCycle.find(connectorStartCW2)
                        while current.value != connectorEndCC2:
                            totalDist1 += Distance(current.value,
                                                   current.next.value)
                            totalSlope1 += (current.value.y-current.prev.value.y) / \
                                (current.value.x-current.prev.value.x)
                            current = current.next
                        totalDist1 += Distance(connectorEndCC2, Path[1])

                        totalDist2 = Distance(connectorStartCC2, sp2)
                        totalSlope2 = 0
                        current = holeCycle.find(connectorStartCC2)
                        while current.value != connectorEndCW2:
                            totalDist2 += Distance(current.value,
                                                   current.prev.value)
                            totalSlope2 += (current.value.y-current.prev.value.y) / \
                                (current.value.x-current.prev.value.x)
                            current = current.prev
                        totalDist1 += Distance(connectorEndCW2, ep2)

                        #print (abs(min(totalDist1, totalDist2)-Distance(sp2, ep2)))
                        if abs(min(totalDist1, totalDist2)-Distance(sp2, ep2)) > penDiameter:
                            notValid2 = True

            # midpoint of connecting stroke cannot lie outside border path
            if not notValid1 and not pointInsidePath(path, Coordinate((currentPath[len(currentPath)-1].x + Path[0].x)/2, (currentPath[len(currentPath)-1].y + Path[0].y)/2), penDiameter/50, False):
                notValid1 = True
            if not notValid2 and not pointInsidePath(path, Coordinate((currentPath[len(currentPath)-1].x + Path[1].x)/2, (currentPath[len(currentPath)-1].y + Path[1].y)/2), penDiameter/50, False):
                notValid2 = True

            """if notValid1:
                l1 = C.create_line (currentPath[len(currentPath)-1].x/Scalar, currentPath[len(currentPath)-1].y/Scalar, Path[0].x/Scalar, Path[0].y/Scalar, fill="red")
            else:
                l1 = C.create_line (currentPath[len(currentPath)-1].x/Scalar, currentPath[len(currentPath)-1].y/Scalar, Path[0].x/Scalar, Path[0].y/Scalar, fill="blue")

            if notValid2:
                l2 = C.create_line (currentPath[len(currentPath)-1].x/Scalar, currentPath[len(currentPath)-1].y/Scalar, Path[1].x/Scalar, Path[1].y/Scalar, fill="red")
            else:
                l2 = C.create_line (currentPath[len(currentPath)-1].x/Scalar, currentPath[len(currentPath)-1].y/Scalar, Path[1].x/Scalar, Path[1].y/Scalar, fill="blue")

            C.update_idletasks()
            C.delete (l1)
            C.delete (l2)"""

            if ndist1 < shortestDist:
                reverseStartPath = False
                nextPathStart = Path
                shortestDist = ndist1
            if ndist2 < shortestDist:
                reverseStartPath = True
                nextPathStart = Path
                shortestDist = ndist2

            if dist1 < shortestDistValid and not notValid1:
                reverseNewPath = False
                shortestDistValid = dist1
                nextPath = Path
            if dist2 < shortestDistValid and not notValid2:
                reverseNewPath = True
                nextPath = Path
                shortestDistValid = dist2
        if shortestDistValid > penDiameter * 4:
            if len(currentPath) > 0:
                orderedPaths.append(currentPath)
            C.create_line(nextPathStart[0].x/Scalar, nextPathStart[0].y /
                          Scalar, nextPathStart[1].x/Scalar, nextPathStart[1].y/Scalar)
            C.update_idletasks()
            currentPath = list(nextPathStart.__reversed__()
                               if reverseStartPath else nextPathStart)
            index = strokes.index(nextPathStart)
            strokes.remove(nextPathStart)
            orderedStrokes.remove(nextPathStart)
        else:
            C.create_line(nextPath[0].x/Scalar, nextPath[0].y /
                          Scalar, nextPath[1].x/Scalar, nextPath[1].y/Scalar)
            if reverseNewPath:
                C.create_line(currentPath[len(currentPath)-1].x/Scalar, currentPath[len(
                    currentPath)-1].y/Scalar, nextPath[1].x/Scalar, nextPath[1].y/Scalar)
            else:
                C.create_line(currentPath[len(currentPath)-1].x/Scalar, currentPath[len(
                    currentPath)-1].y/Scalar, nextPath[0].x/Scalar, nextPath[0].y/Scalar)
            C.update_idletasks()
            currentPath.extend(list(nextPath.__reversed__())
                               if reverseNewPath else nextPath)
            index = strokes.index(nextPath)
            strokes.remove(nextPath)
            orderedStrokes.remove(nextPath)
        previousStep = index-lastIndex
        if index-lastIndex != 0 and len(strokes) > 0:
            orderedStrokes = list()
            strokesCycle = cycle(strokes)
            if index + previousStep < 0:
                start = strokesCycle.first
                step = 1
            elif index+previousStep >= len(strokes):
                start = strokesCycle.first.prev
                step = -1
            else:
                start = strokesCycle.get_node(
                    index+previousStep-(0 if direction > 0 else -1))
            orderedStrokes.append(start.value)
            current = start.next if direction > 0 else start.prev
            while current != start:
                orderedStrokes.append(current.value)
                if direction > 0:
                    current = current.next
                else:
                    current = current.prev
        lastIndex = index

        shortestDist = math.inf
        shortestDistValid = math.inf
        reverseNewPath = False
        reverseStartPath = False
    if len(currentPath) > 0:
        orderedPaths.append(currentPath)
    return orderedPaths


def midpoint(p1, p2):
    return Coordinate((p1.x+p2.x)/2, (p1.y+p2.y)/2)


def findCenterLines(paths):
    centerLines = list()
    paths.sort(key=areaOfPath, reverse=True)
    copyOfPaths = list(paths)
    for p1 in copyOfPaths:
        if p1 not in paths:
            continue
        holes = list()
        for p2 in copyOfPaths:
            if p2 not in paths or p1 == p2:
                continue
            if pathContainedInPath(p1, p2):
                invalid = False
                for hole in holes:
                    if pathContainedInPath(hole.toList(), p2):
                        invalid = True
                        break
                if not invalid:
                    paths.remove(p2)
                    holes.append(cycle(p2))
        p = cycle(p1)
        triangulation = triangulate(p, holes, 30)
        centerLine = list()
        trianglesUsed = list()
        branches = list()
        sharedEdge = list()
        nextTri = triangulation[0]
        while nextTri != None or len(branches) > 0:
            if nextTri == None:
                tri = branches[0]
                branches.remove(tri)
                centerLines.append(centerLine)
                centerLine = list()
            else:
                tri = nextTri
            borderEdges = list()
            virtualEdges = list()
            current1 = tri.first
            for i in range(0, 3):
                mp = midpoint(current1.value, current1.prev.value)
                current2 = p.first
                onBorder = False
                for j in range(0, p.length()-1):
                    if onSegment(mp, current2.value, current2.prev.value, 0):
                        onBorder = True
                        break
                    current2 = current2.next
                if onBorder:
                    borderEdges.append([current1.value, current1.prev.value])
                else:
                    virtualEdges.append([current1.value, current1.prev.value])
                current1 = current1.next
            trianglesUsed.append(tri)
            nextTri = None
            neighborCount = 0
            for t in triangulation:  # find neighbors
                sharedPoints = [
                    element for element in t.toList() if element in tri.toList()]
                if len(sharedPoints) == 2:
                    neighborCount += 1
                    if t not in trianglesUsed and t != tri:
                        nextTri = t
                        sharedEdge = list(sharedPoints)
            if neighborCount == 3 and nextTri != None:
                centerLine.append(Coordinate((tri.first.value.x+tri.first.prev.value.x+tri.first.next.value.x) /
                                             3, (tri.first.value.y+tri.first.prev.value.y+tri.first.next.value.y)/3))
                branches.append(tri)
            if neighborCount > 0:
                centerLine.append(midpoint(sharedEdge[0], sharedEdge[1]))
        centerLines.append(centerLine)
    return centerLines


def getPointInsidePath(path, holes):
    MinX = path[0].x
    MinY = path[0].y
    MaxX = path[0].x
    MaxY = path[0].y
    for p in path:
        MinX = min(MinX, p.x)
        MinY = min(MinY, p.y)
        MaxX = max(MaxX, p.x)
        MaxY = max(MaxY, p.y)

    point = Coordinate(random.randint(MinX, MaxX), random.randint(MinY, MaxY))
    while not pointInsidePath(path, point, 0, False):
        point = Coordinate(random.randint(MinX, MaxX),
                           random.randint(MinY, MaxY))
    return point

# endregion

# region triangulation

# group the verticies of a polygon into triangules : Ear Clipping


def triangulate(path, holes, SAThreshold):
    path.remove(path.first.prev)
    if orientation(path) != 1:
        path = cycle(path.toList().__reversed__())

    triangles = list()
    polygonVerts = path
    polyVerts = cycle()
    convexVerts = list()
    reflexVerts = list()
    earTips = list()

    # add hole verts to polygon verts
    for hole in holes:
        hole.remove(hole.first.prev)
        if orientation(hole) != 2:
            hole = cycle(hole.toList().__reversed__())

        # find possible bridges
        bridges = list()
        current1 = polygonVerts.first
        for i in range(0, polygonVerts.length()):
            current2 = hole.first
            for j in range(0, hole.length()):
                bridges.append(Segment(current1.value, current2.value))
                current2 = current2.next
            current1 = current1.next

        # choose best bridge
        bridges.sort(key=lambda b: Distance(b.a, b.b))
        bridge = bridges[0]
        while (not bridgeIsValid(bridge, polygonVerts, holes) and len(bridges) > 1):
            bridges.remove(bridge)
            bridge = bridges[0]

        #C.create_line (bridge.a.x/Scalar, bridge.a.y/Scalar, bridge.b.x/Scalar, bridge.b.y/Scalar, fill="green")

        # Insert hole verts
        bridgeA = polygonVerts.find(bridge.a)
        bridgeB = hole.find(bridge.b)
        last = bridgeA
        current = bridgeB
        while current != bridgeB or last == bridgeA:
            polygonVerts.insertAfter(last, Node(current.value))
            last = polygonVerts.find(current.value)
            current = current.next

        polygonVerts.insertAfter(last, Node(bridge.b))
        polygonVerts.insertAfter(
            polygonVerts.findLast(bridge.b), Node(bridge.a))

    # find convex / reflex verts
    current = polygonVerts.first
    for i in range(0, polygonVerts.length()):
        #C.create_text (current.value.x/Scalar+5, current.value.y/Scalar+5, text=i)
        polyVerts.addLast(Node(i))
        triangle = cycle(
            [current.prev.value, current.value, current.next.value])
        if isConvex(triangle):
            convexVerts.append(i)
            #C.create_oval (current.value.x/Scalar+2, current.value.y/Scalar+2, current.value.x/Scalar-2, current.value.y/Scalar-2, fill="blue")
        else:
            reflexVerts.append(i)
            #C.create_oval (current.value.x/Scalar+2, current.value.y/Scalar+2, current.value.x/Scalar-2, current.value.y/Scalar-2, fill="red")
        current = current.next

    # find ears
    for vert in convexVerts:
        vertNode = polyVerts.find(vert)
        triangle = cycle([polygonVerts.get_node(vertNode.prev.value).value, polygonVerts.get_node(
            vertNode.value).value, polygonVerts.get_node(vertNode.next.value).value])
        if isEar(reflexVerts, polygonVerts, triangle, C):
            earTips.append(vert)
            #C.create_oval (polygonVerts.get_node(vert).value.x/Scalar+2, polygonVerts.get_node (vert).value.y/Scalar+2, polygonVerts.get_node (vert).value.x/Scalar-2, polygonVerts.get_node (vert).value.y/Scalar-2, fill="purple")

    while polyVerts.length() > 2:
        # something went wrong!
        if len(earTips) < 1:
            print("No more ear tips!")
            return triangles

        earTip = polyVerts.find(earTips[0])

        # find ear with smallest angle
        smallestAngle = math.inf
        for ear in earTips:
            earNode = polyVerts.find(ear)
            a = angle(polygonVerts.get_node(earNode.prev.value).value, polygonVerts.get_node(
                ear).value, polygonVerts.get_node(earNode.next.value).value)
            if a < smallestAngle:
                earTip = earNode
                smallestAngle = a

        previous = earTip.prev
        nxt = earTip.next

        # store trplet
        a = polygonVerts.get_node(previous.value).value
        b = polygonVerts.get_node(earTip.value).value
        c = polygonVerts.get_node(nxt.value).value
        tri = cycle([a, b, c])

        # swap diagonal with adjacent triangle to improve triangle quality
        originalSM = smallestAngle
        if originalSM < SAThreshold:
            for triangle in triangles:
                # find longest edge
                ab = Distance(a, b)
                bc = Distance(b, c)
                ca = Distance(c, a)

                if ab > bc and ab > ca:
                    longestEdge = [a, b]
                elif bc > ab and bc > ca:
                    longestEdge = [b, c]
                else:
                    longestEdge = [c, a]

                if triangle.find(longestEdge[0]) != None and triangle.find(longestEdge[1]) != None:
                    # find the verticies not part of the pair
                    triList = tri.toList()
                    triList.remove(longestEdge[0])
                    triList.remove(longestEdge[1])
                    d = triList[0]
                    triangleList = triangle.toList()
                    triangleList.remove(longestEdge[0])
                    triangleList.remove(longestEdge[1])
                    e = triangleList[0]

                    # generate new triangles
                    t1 = cycle([longestEdge[0], e, d])
                    t2 = cycle([longestEdge[1], d, e])

                    if getTriAngle(longestEdge[0], e, d) > originalSM and getTriAngle(longestEdge[1], d, e) > originalSM:
                        # ensure orientation of old triangle is still CC
                        triVerts1 = t2.toList()
                        if orientation(cycle([triVerts1[0], triVerts1[1], triVerts1[2]])) != 2:
                            t2.first.value = triVerts1[2]
                            t2.first.prev.value = triVerts1[0]

                        # update triangles
                        triangles.remove(triangle)
                        triangles.append(t2)
                        tri = t1

        # enusre the triangle is orientated CC
        if orientation(tri) != 2:
            tri = cycle(tri.toList().__reversed__())

        triangles.append(tri)

        #triangle = [tri.first.value, tri.first.next.value, tri.first.prev.value]
        #C.create_line (triangle[0].x/Scalar, triangle[0].y/Scalar, triangle[1].x/Scalar, triangle[1].y/Scalar)
        #C.create_line (triangle[1].x/Scalar, triangle[1].y/Scalar, triangle[2].x/Scalar, triangle[2].y/Scalar)
        #C.create_line (triangle[2].x/Scalar, triangle[2].y/Scalar, triangle[0].x/Scalar, triangle[0].y/Scalar)

        # remove ear tip from lists
        earTips.remove(earTip.value)
        convexVerts.remove(earTip.value)
        polyVerts.remove(earTip)

        # update the statis of the adjacient verticies
        updateVertStat(previous, polygonVerts, earTips,
                       convexVerts, reflexVerts)
        updateVertStat(nxt, polygonVerts, earTips, convexVerts, reflexVerts)

    return triangles


def bridgeIsValid(bridge, verts, holes):
    # test the bridge for intersection with the polygon bounds
    current = verts.first
    for i in range(0, verts.length()):
        if doIntersect(current.value, current.prev.value, bridge.a, bridge.b):
            return False
        current = current.next

    # test the bridge for intersection with the polygon bounds
    for h in holes:
        current = h.first
        for i in range(0, h.length()):
            if doIntersect(current.value, current.prev.value, bridge.a, bridge.b):
                return False
            current = current.next

    return True

# determine if the verticie is still convex / reflex / ear


def updateVertStat(vert, verts, e, c, r):
    triangle = cycle([verts.get_node(vert.prev.value).value, verts.get_node(
        vert.value).value, verts.get_node(vert.next.value).value])

    convex = isConvex(triangle)

    if convex and not vert.value in c:
        c.append(vert.value)
        r.remove(vert.value)
        #C.create_oval (verts.get_node (vert.value).value.x/Scalar+2, verts.get_node (vert.value).value.y/Scalar+2, verts.get_node (vert.value).value.x/Scalar-2, verts.get_node (vert.value).value.y/Scalar-2, fill="blue")

    ear = isEar(r, verts, triangle, C) if convex else False

    if ear and not vert.value in e:
        e.append(vert.value)
        #C.create_oval (verts.get_node (vert.value).value.x/Scalar+2, verts.get_node (vert.value).value.y/Scalar+2, verts.get_node (vert.value).value.x/Scalar-2, verts.get_node (vert.value).value.y/Scalar-2, fill="purple")
    elif not ear and vert.value in e:
        e.remove(vert.value)
        #C.create_oval (verts.get_node (vert.value).value.x/Scalar+2, verts.get_node (vert.value).value.y/Scalar+2, verts.get_node (vert.value).value.x/Scalar-2, verts.get_node (vert.value).value.y/Scalar-2, fill="blue")

# find the triangles minimum angle


def getTriAngle(a, b, c):
    return min([angle(a, b, c), angle(a, b, c), angle(a, b, c)])

# test wether any reflex verticies lie in the triangle


def isEar(reflexVerts, verts, triangle, C):
    for r in reflexVerts:
        if triangle.contains(verts.get_node(r).value):
            continue

        if pointInsidePath(triangle.toList(), verts.get_node(r).value, 0, True):
            return False

    return True

# test wether the orientation of the triplet is the same as the polygon (counter clockwise)


def isConvex(triangle):
    if orientation(triangle) == 2:
        return False
    return True


def angle(a, b, c):
    acc = abs(math.degrees(math.atan2(c.y-b.y, c.x-b.x) -
                           math.atan2(a.y-b.y, a.x-b.x)))
    #print (math.degrees(math.atan2(c.y-b.y, c.x-b.x) - math.atan2(a.y-b.y, a.x-b.x)))
    #print (abs(math.degrees(math.atan2(c.y-b.y, c.x-b.x) - math.atan2(a.y-b.y, a.x-b.x))))
    acw = abs(math.degrees(math.atan2(a.y-b.y, a.x-b.x) -
                           math.atan2(c.y-b.y, c.x-b.x)))
    return min(acc, acw)

# endregion


def Distance(p1, p2):
    return math.sqrt(math.pow(p2.x-p1.x, 2) + math.pow(p2.y-p1.y, 2))


def areaOfPath(path):
    if len(path) == 0:
        return 0
    area = 0
    lastPoint = path[len(path)-1]
    for point in path:
        area += (lastPoint.x+point.x) * (lastPoint.y-point.y)
        lastPoint = point
    return abs(area/2)


def pathContainedInPath(path1, path2):
    for p in path2:
        if not pointInsidePath(path1, p, 0, False):
            return False
    return True

# determines if a point lies inside a polygon : horizontal line test

def pointInsidePath(path, point, margin, defaultOutside):
    MinX = path[0].x
    MinY = path[0].y
    MaxX = path[0].x
    MaxY = path[0].y
    for p in path:
        MinX = min(MinX, p.x)
        MinY = min(MinY, p.y)
        MaxX = max(MaxX, p.x)
        MaxY = max(MaxY, p.y)

    # test if the point is inside the polygon bounding box
    if point.x < MinX or point.y < MinY or point.x > MaxX or point.y > MaxY:
        return False

    lp = path[len(path)-1]
    intersections = 0
    for p in path:
        if onSegment(point, p, lp, margin):
            return not defaultOutside
        if doIntersect(point, Coordinate(point.x + machineDemensionsX, point.y), p, lp):
            if not onSegment(lp, point, Coordinate(point.x + machineDemensionsX, point.y), 0) or not doIntersect(path[path.index(lp)-1], p, point, Coordinate(point.x + machineDemensionsX, point.y)):
                intersections += 1
                """l2=C.create_line (p.x/Scalar, p.y/Scalar, lp.x/Scalar, lp.y/Scalar, fill="blue")
                l=C.create_line (point.x/Scalar, point.y/Scalar, point.x+machineDemensionsX/Scalar, point.y/Scalar, fill="red")
                C.update_idletasks()
                time.sleep (1)
                C.delete (l)
                C.delete (l2)"""
        lp = p

    # if intersections is even, we are outside the polygon
    return False if intersections % 2 == 0 else True


def doIntersect(p1, q1, p2, q2):
    # Find the four orientations needed
    o1 = orientation(cycle([p1, q1, p2]))
    o2 = orientation(cycle([p1, q1, q2]))
    o3 = orientation(cycle([p2, q2, p1]))
    o4 = orientation(cycle([p2, q2, q1]))

    if p1 == p2 or q1 == q2 or p1 == q2 or p2 == q1:
        return False

    # General case
    if o1 != o2 and o3 != o4:
        return True

    return False  # Doesn't fall in any of the above cases

# checks if a point lies on a segment


def onSegment(checkPoint, endpoint1, endpoint2, margin):
    ab = Distance(endpoint1, endpoint2)
    ap = Distance(endpoint1, checkPoint)
    bp = Distance(endpoint2, checkPoint)

    return ap + bp - ab <= margin

# To find orientation of ordered triplet (p, q, r).
# The function returns following values
# 0 --> p, q and r are colinear
# 1 --> Clockwise
# 2 --> Counterclockwise


def orientation(points):
    val = 0
    current = points.first
    for i in range(0, points.length()):
        val += (current.next.value.x - current.value.x) * \
            (current.next.value.y + current.value.y)
        current = current.next
    return 0 if val == 0 else (1 if val > 0 else 2)


currentPathInd = 0
currentPointInd = 0
paused = False
stopped = False
lastPoint = Coordinate(0, 0)
distanceCovered = 0


def sendCoords(ser):
    global currentPathInd
    global currentPointInd
    global paused
    global stopped
    global lastPoint
    global totalDistance
    global distanceCovered

    if stopped:
        stopped = False
        return

    line = ser.readline()
    if line == b"ready\r\n" and not paused:
        if currentPathInd >= len(Paths):
            stopDraw(ser)
            return
        else:
            if currentPointInd >= len(Paths[currentPathInd]):
                currentPointInd = 0
                currentPathInd += 1
                ser.write("<path>".encode())
            else:
                ser.write(("<" + str(Paths[currentPathInd][currentPointInd].x)+","+str(
                    Paths[currentPathInd][currentPointInd].y)+">").encode())
                distanceCovered += Distance(lastPoint,
                                            Paths[currentPathInd][currentPointInd])
                distance["text"] = "Distance: " + \
                    str(round(distanceCovered/100)) + "/" + \
                    str(round(totalDistance/100)) + "mm"
                percentage["text"] = str(
                    round(distanceCovered/totalDistance*100)) + "%"
                progress["value"] = distanceCovered/totalDistance*100
                lastPoint = Paths[currentPathInd][currentPointInd]
                currentPointInd += 1
    elif line == b"start\r\n" and not paused and not stopped:
        clock_seconds()

    threading.Timer(0.01, lambda: sendCoords(ser)).start()


seconds = 0


def clock_seconds():
    global seconds
    global totalTime
    if not stopped and not paused:
        seconds += 1
        _time["text"] = "Time: " + str(int(seconds/60)) + ":" + str(
            seconds % 60) + "/" + str(int(totalTime/60)) + ":" + str(round(totalTime) % 60)
        threading.Timer(1, clock_seconds).start()


def pauseDraw(ser):
    global paused
    paused = True
    ser.write("<pause>".encode())
    start["text"] = "Start"
    start["command"] = lambda: unpauseDraw(ser)


def unpauseDraw(ser):
    global paused
    paused = False
    ser.write("<unpause>".encode())
    start["text"] = "Pause"
    start["command"] = lambda: pauseDraw(ser)


def stopDraw(ser):
    global stopped
    global distanceCovered
    global totalDistance
    global currentPathInd
    global currentPointInd

    stopped = True
    currentPathInd = 0
    currentPointInd = 0
    ser.write("<stop>".encode())
    ser.close()
    start["text"] = "Start"
    stop["text"] = "Trace Border"
    start["command"] = startDraw
    stop["command"] = startDraw
    progress["value"] = 0
    distanceCovered = 0
    distance["text"] = "Distance: 0/" + str(round(totalDistance/100)) + "mm"
    percentage["text"] = "0%"
    _time["text"] = "0:0/" + str(int(totalTime/60)) + \
        ":" + str(round(totalTime) % 60)


def startDraw():
    global lastPoint

    if len(Paths) < 1:
        return

    ser = serial.Serial("com4", 9600)
    time.sleep(3)
    ser.write("><start>".encode())

    start["text"] = "Pause"
    stop["text"] = "Stop"
    start["command"] = lambda: pauseDraw(ser)
    stop["command"] = lambda: stopDraw(ser)
    lastPoint = Coordinate(0, 0)
    sendCoords(ser)


start = TK.Button(drawPanel, text="Start", command=startDraw)
start.pack(side="left")
stop = TK.Button(drawPanel, text="Trace Border", command=startDraw)
stop.pack(side="left")
percentage = TK.Label(drawPanel, text="0%")
percentage.pack(side="left", padx=(5, 0))
_time = TK.Label(drawPanel, text="Time: 0:0/0:0")
_time.pack(side="right")
distance = TK.Label(drawPanel, text="Distance: 0/0mm")
distance.pack(side="right")
progress = TTK.Progressbar(drawPanel, orient="horizontal")
progress.pack(fill="x", padx=5, pady=(2, 0))

root.mainloop()
