import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
import math
# vertex = {
#     "key":0, 
#     "coords":{"x":0,"y":0}, 
#     "incident_edge":None,
#     "half_edge_list":[],
#     }
# face = {
#     "key":0,
#     "outer_component":None,
#     "inner_components":None
#     }
# edge = {
#     "key":0,
#     "origin":None,
#     "twin":None,
#     "next":None,
#     "prev":None,
#     "face":None
#     }
class DCEL:
    def __init__(self, ax, plt):
        self.vertices = []
        self.faces = []
        self.edges = []
        self.edge_queue = []
        self.added_edges = []
        self.ax = ax
        self.plt = plt

    def set_angle(self, edge, vertex):
        dest = None
        # print(v2)
        if vertex is None:
            dest = edge["twin"]["origin"]["coords"]
        else:
            dest=vertex["coords"]
        origin = edge["origin"]["coords"]
        dx = dest["x"] - origin["x"]
        dy = dest["y"] - origin["y"]
        l = math.sqrt(dx*dx + dy*dy)
        def to_deg(rad):
            return 180 * rad/math.pi
        if dy > 0:
            edge["angle"] = to_deg(math.acos(dx/l))
        else:
            edge["angle"] = to_deg(2 * math.pi - math.acos(dx/l))

    def is_counterclockwise(self, vertices):
        # https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
        signed_area = 0
        for i in range(len(vertices)):
            j = (i + 1) % len(vertices)
            signed_area += vertices[i][0] * vertices[j][1]
            signed_area -= vertices[j][0] * vertices[i][1]
        return signed_area > 0

    def init_from_vertex_list(self, vertices):
        if not self.is_counterclockwise(vertices):
            vertices = vertices[::-1]
        inner_face = {
            "key": "inner",
            "outer_component": None,
            "inner_components": []
        }
        outer_face = {
            "key": "outer",
            "outer_component": None,
            "inner_components": []
        }
        self.add_face(inner_face)
        self.add_face(outer_face)
        edges = []
        edges.append([vertices[len(vertices) - 1], vertices[0]])
        self.add_vertex({
            "key": str(vertices[0]),
            "index": 0,
            "coords": {"x": vertices[0][0], "y": vertices[0][1]},
            "y_comparator":(vertices[0][1],vertices[0][0]),
            "x_comparator":(vertices[0][0],vertices[0][1]),
            "incident_edge": None,
            "outgoing_half_edge_list":[],
        })
        vertex_map = {}
        vertex_map[str(vertices[0])] = self.vertices[0]
        
        for i in range(1, len(vertices)):
            key = str(vertices[i])
            vertex = {
                "key": key,
                "index": i,
                "coords": {"x": vertices[i][0], "y": vertices[i][1]},
                "y_comparator":(vertices[i][1],vertices[i][0]),
                "x_comparator":(vertices[i][0],vertices[i][1]),
                "incident_edge": None,
                "outgoing_half_edge_list":[]
            }
            self.add_vertex(vertex)
            vertex_map[key] = vertex
            edges.append([vertices[i - 1], vertices[i]]) 

        for edge in edges:
            half_edge_1 = {
                "key": vertex_map[str(edge[0])]["key"]+vertex_map[str(edge[1])]["key"],
                "origin": vertex_map[str(edge[0])],
                "twin": None,
                "next": None,
                "prev": None,
                "face": inner_face
            }
            half_edge_2 = {
                "key": vertex_map[str(edge[1])]["key"]+vertex_map[str(edge[0])]["key"],
                "origin": vertex_map[str(edge[1])],
                "twin": half_edge_1,
                "next": None,
                "prev": None,
                "face": outer_face
            }
            if inner_face["outer_component"] is None:
                inner_face["outer_component"] = half_edge_1
                outer_face["inner_components"] = [half_edge_2]
            vertex_map[str(edge[1])]["outgoing_half_edge_list"].append(half_edge_2)
            vertex_map[str(edge[0])]["outgoing_half_edge_list"].append(half_edge_1)
            vertex_map[str(edge[0])]["incident_edge"] = half_edge_1
            vertex_map[str(edge[1])]["incident_edge"] = half_edge_2
            
            half_edge_1["twin"] = half_edge_2

            half_edge_1["prev"] = self.edges[-2] if self.edges else None
            half_edge_2["next"] = self.edges[-1] if self.edges else None
            self.set_angle(half_edge_1, None)
            self.set_angle(half_edge_2, None)
            self.add_edge(half_edge_1)
            self.add_edge(half_edge_2)
        
        self.edges[0]["prev"] = self.edges[-2]
        self.edges[1]["next"] = self.edges[-1]
        self.inner_face = inner_face
        for i in self.edges:
            if i["prev"] is not None:
                i["prev"]["next"] = i
            if i["next"] is not None:
                i["next"]["prev"] = i
        
    def add_vertex(self, vertex):
        self.vertices.append(vertex)
    def add_edge(self, edge):
        self.edges.append(edge)

    def add_face(self, face):

        self.faces.append(face)

    def enqueue_new_edge(self, v1, v2):
        self.edge_queue.append([v1, v2])
    # https://stackoverflow.com/questions/56980195/adding-edges-dynamically-in-a-dcel-half-edge-based-graph
    # ! should not use notion of e_i
    def add_queued_edges(self):
        if(len(self.edge_queue) == 0):
            return
        # print("add_queued edges called")
        added_edges = []
        for [A, B] in self.edge_queue:
            AB = {
                "key": A["key"]+B["key"],
                "origin": A,
                "twin": None,
                "next": None,
                "prev": None,
                "face": None
            }
            self.set_angle(AB, B)
            BA = {
                "key": B["key"]+A["key"],
                "origin": B,
                "twin": AB,
                "next": None,
                "prev": None,
                "face": None
            }
            AB["twin"]=BA
            self.set_angle(BA, A)
            A["outgoing_half_edge_list"].append(AB)
            B["outgoing_half_edge_list"].append(BA)
            A["outgoing_half_edge_list"].sort(key=lambda e: e["angle"])
            B["outgoing_half_edge_list"].sort(key=lambda e: e["angle"])

            index_ab = None
            for i in range(len(A["outgoing_half_edge_list"])):
                if A["outgoing_half_edge_list"][i]["key"] == AB["key"]:
                    index_ab = i
                    break
            ba_next_twin = index_ab - 1
            if ba_next_twin == -1:
                ba_next_twin = len(A["outgoing_half_edge_list"]) - 1
            BA["next"] = A["outgoing_half_edge_list"][ba_next_twin]
            A["outgoing_half_edge_list"][ba_next_twin]["prev"] = BA

            # now must find BA["prev"]

            index_ba = None 
            for i in range(len(B["outgoing_half_edge_list"])):
                if B["outgoing_half_edge_list"][i]["key"] == BA["key"]:
                    index_ba = i
                    break
            ba_prev_twin = index_ba + 1
            if ba_prev_twin >= len(B["outgoing_half_edge_list"]):
                ba_prev_twin = 0
            BA["prev"] = B["outgoing_half_edge_list"][ba_prev_twin]["twin"]
            B["outgoing_half_edge_list"][ba_prev_twin]["twin"]["next"] = BA

            
            
            index_ba = None
            for i in range(len(B["outgoing_half_edge_list"])):
                if B["outgoing_half_edge_list"][i]["key"] == BA["key"]:
                    index_ba = i
                    break
            ab_next_twin = index_ba - 1
            if ab_next_twin == -1:
                ab_next_twin = len(B["outgoing_half_edge_list"]) - 1
            AB["next"] = B["outgoing_half_edge_list"][ab_next_twin]
            B["outgoing_half_edge_list"][ab_next_twin]["prev"] = AB

            # now must find BA["prev"]

            index_ab = None 
            for i in range(len(A["outgoing_half_edge_list"])):
                if A["outgoing_half_edge_list"][i]["key"] == AB["key"]:
                    index_ab = i
                    break
            ab_prev_twin = index_ab + 1
            if ab_prev_twin >= len(A["outgoing_half_edge_list"]):
                ab_prev_twin = 0
            AB["prev"] = A["outgoing_half_edge_list"][ab_prev_twin]["twin"]
            A["outgoing_half_edge_list"][ab_prev_twin]["twin"]["next"] = AB

            added_edges.append(AB)
            added_edges.append(BA)
            self.edges.append(AB)
            self.edges.append(BA)

            
        
        self.added_edges = added_edges

        updated_edges = set()

        new_face_id_counter = 0
        face_map = {}
        for edge in self.edges:
            if edge["key"] in updated_edges or (edge["face"] is not None and edge["face"]["key"]=="outer"):
                continue
            if new_face_id_counter not in face_map:
                face_map[new_face_id_counter] = {
                "key": new_face_id_counter,
                "outer_component": edge,
                "inner_components": []
                }
                self.add_face(face_map[new_face_id_counter])
            face = face_map[new_face_id_counter]
            edge["face"] = face
            updated_edges.add(edge["key"])
            curr = edge["next"]
            visited_edges = set()
            # print("\n\nSTART KEY: "+edge["key"])

            iters = 0
            while curr["key"] != edge["key"]:
                # print("curr key: "+curr["key"])
                iters+=1
                curr["face"] = face
                updated_edges.add(curr["key"])
                visited_edges.add(curr["key"])
                curr = curr["next"]
                # if(iters > 10):
                #     return
            # print("DONE\n\n")
            new_face_id_counter+=1
        # remove inner face
        self.faces.pop(0)
            
        self.edge_queue = []
   