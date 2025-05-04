import time
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

class Triangulator:
    def __init__(self, dcel, plt, ax, slow_mode):
        self.dcel = dcel
        self.plt = plt
        self.ax = ax
        self.edges_to_add_for_monotonicity = []
        self.active_edges = []
        self.slow_mode = slow_mode
        self.current_pt = None
        self.delay = 1
    def add_to_dcel(self, verts, color="r-"):
        v_1 = verts[0]
        v_2 = verts[1]
        # first draw new edge in red on plot
        self.ax.plot([v_1["coords"]["x"], v_2["coords"]["x"]], [v_1["coords"]["y"], v_2["coords"]["y"]], color)
        self.ax.figure.canvas.draw()
        self.dcel.enqueue_new_edge(v_1, v_2)

    def get_e_i_from_vertex(self, vertex):
        # e_i is an edge incident to the vertex whose origin is the vertex and whose face is inner
        # incident edge is one of four edges
        # if incident edge is in outer face, get the twin

        edge = vertex["incident_edge"]

        if edge["face"]["key"] == "outer":

            edge = edge["twin"]

        if edge["origin"]["key"] == vertex["key"]:
            return edge
        else:
            return edge["next"]
    def get_e_i_minus_one_from_vertex(self, vertex):
        edge = vertex["incident_edge"]
        if edge["face"]["key"] == "outer":
            edge = edge["twin"]
        if edge["origin"]["key"] == vertex["key"]:
            edge = edge["prev"]

        return edge
    def find_edge_directly_to_left(self, vertex):
        # ! BAD, need to implement balanced bst instead
        # search active edges to find the edge directly to the left of the vertex
        self.active_edges.sort(key=lambda e: e["origin"]["coords"]["x"])
        for edge in self.active_edges[::-1]:
            # find first edge to the left of the vertex
            if edge["origin"]["coords"]["x"] < vertex["coords"]["x"] or (edge["twin"]["origin"]["coords"]["x"] < vertex["coords"]["x"]):                 
                return edge
        return None
    def vertex_type(self, vertex):
        # "start", "end", "split", "merge", "regular"
        e_i = self.get_e_i_from_vertex(vertex)
        e_i_minus_one = self.get_e_i_minus_one_from_vertex(vertex)
        
        v_1 = e_i_minus_one["origin"]
        v_2 = e_i["twin"]["origin"]

        if v_1["coords"]["y"] < vertex["coords"]["y"] and v_2["coords"]["y"] < vertex["coords"]["y"]:
            # is either start or split
            # if polygon is to left of v_2, it is start.  since the two verts could have same y coord, 
            # also check if polygon is to right of v_1
            if self.is_left_turn(v_1, vertex, v_2):
                return "start"
            else:
                return "split"

        elif v_1["coords"]["y"] > vertex["coords"]["y"] and v_2["coords"]["y"] > vertex["coords"]["y"]:
            # is either end or merge
            if self.is_left_turn(v_1, vertex, v_2):
                return "end"
            else:
                return "merge"
        else:
            # is regular
            return "regular"

    def is_left_turn(self, v_1, vertex, v_2):
        dx1 = vertex["coords"]["x"] - v_1["coords"]["x"]
        dy1 = vertex["coords"]["y"] - v_1["coords"]["y"]
        dx2 = v_2["coords"]["x"] - vertex["coords"]["x"]
        dy2 = v_2["coords"]["y"] - vertex["coords"]["y"]
        cross_product = dx1 * dy2 - dy1 * dx2
        return cross_product > 0
    def is_right_turn(self, v_1, vertex, v_2):
        dx1 = vertex["coords"]["x"] - v_1["coords"]["x"]
        dy1 = vertex["coords"]["y"] - v_1["coords"]["y"]
        dx2 = v_2["coords"]["x"] - vertex["coords"]["x"]
        dy2 = v_2["coords"]["y"] - vertex["coords"]["y"]
        cross_product = dx1 * dy2 - dy1 * dx2
        return cross_product < 0
    def polygon_is_to_left(self, vertex):
        # neighboring vertices are above and below the vertex
        # check the indices of the vertices
        # sort neighbors and vert by y coord, then if the indices are increasing, the polygon is to the left
        # otherwise it is to the right
        # ! way too complicated, only used for regular verts 
        vertex["tmp_index"] = 1
        local_verts = [vertex]
        incident_edge = vertex["incident_edge"]
        if incident_edge["face"]["key"] == "outer":
            incident_edge = incident_edge["twin"]

        
        if incident_edge["origin"]["key"] == vertex["key"]:
            local_verts.append(incident_edge["prev"]["origin"])
            incident_edge["prev"]["origin"]["tmp_index"] = 0
            local_verts.append(incident_edge["twin"]["origin"])
            incident_edge["twin"]["origin"]["tmp_index"] = 2
        else:
            local_verts.append(incident_edge["origin"])
            incident_edge["origin"]["tmp_index"] = 0
            local_verts.append(incident_edge["next"]["twin"]["origin"])
            incident_edge["next"]["twin"]["origin"]["tmp_index"] = 2
        local_verts.sort(key=lambda v: v["coords"]["y"])
        index_0 = local_verts[0]["tmp_index"]
        index_2 = local_verts[2]["tmp_index"]
        # if difference between vertex and neighbors is > 1, then there is a wrap-around
        return index_0 < index_2
        # ! Unnecessary, this method is only ever called on regulatr vertices
        # if local_verts[2]["coords"] == vertex["coords"]:
        #     # start or split 
        #     vertex_1 = local_verts[0]
        #     vertex_2 = local_verts[1]
        #     left = None
        #     right = None
        #     if self.is_left_turn(vertex_1, vertex, vertex_2):
        #         left = vertex_1
        #         right = vertex_2
        #     else:
        #         left = vertex_2
        #         right = vertex_1
            
        #     return right["tmp_index"] < left["tmp_index"]
        # elif local_verts[0]["coords"] == vertex["coords"]:
        #     # end or merge
        #     left = None
        #     right = None
        #     vertex_1 = local_verts[1]
        #     vertex_2 = local_verts[2]
        #     left = None
        #     right = None
        #     if self.is_left_turn(vertex_1, vertex, vertex_2):
        #         left = vertex_1
        #         right = vertex_2
        #     else:
        #         left = vertex_2
        #         right = vertex_1
        #     #  if right is more counterclockwise, return true i.e. if right["index"] > left["index"]. 
        #     # but must also check wrap-around case
        #     # then right["index"] > left["index"] iff right["index"] > left["index"]
        #     # or left["index"] != right["index"] - 2
        #     return left["tmp_index"] < right["tmp_index"]
        # else:

        #     index_0 = local_verts[0]["tmp_index"]
        #     index_2 = local_verts[2]["tmp_index"]
        #     # if difference between vertex and neighbors is > 1, then there is a wrap-around
        #     return index_0 < index_2

    def handle_start_vertex(self, vertex):

        vertex["type"] = "start"
        e_i = self.get_e_i_from_vertex(vertex)
        self.active_edges.append(e_i)
        e_i["helper"] = vertex

    def handle_end_vertex(self, vertex):

        vertex["type"] = "end"

        e_i_minus_one = self.get_e_i_minus_one_from_vertex(vertex)
        if "helper" in e_i_minus_one and e_i_minus_one["helper"]["type"] =="merge":
            self.add_to_dcel([vertex, e_i_minus_one["helper"]])
        for i, edge in enumerate(self.active_edges):
            if edge["key"] == e_i_minus_one["key"]:
                self.active_edges.pop(i)
                break
        
    def handle_split_vertex(self, vertex):

        vertex["type"] = "split"
        e_j = self.find_edge_directly_to_left(vertex)

        
        self.add_to_dcel([vertex, e_j["helper"]])
        e_j["helper"] = vertex
        e_i = self.get_e_i_from_vertex(vertex)
        self.active_edges.append(e_i)
        e_i["helper"] = vertex

    def handle_merge_vertex(self, vertex):

        vertex["type"] = "merge"
        e_i_minus_one = self.get_e_i_minus_one_from_vertex(vertex)
        if "helper" in e_i_minus_one and e_i_minus_one["helper"]["type"] =="merge":
            self.add_to_dcel([vertex, e_i_minus_one["helper"]])
        # self.active_edges.remove(e_i_minus_one)
        for i, edge in enumerate(self.active_edges):
            if edge["key"] == e_i_minus_one["key"]:
                self.active_edges.pop(i)
                break
        e_j = self.find_edge_directly_to_left(vertex)
        if "helper" in e_j and e_j["helper"]["type"] =="merge":
            self.add_to_dcel([vertex, e_j["helper"]])
        e_j["helper"] = vertex
    
    def handle_regular_vertex(self, vertex):

        vertex["type"] = "regular"
        # compute if interior of p is to the left or right of e_i
        if not self.polygon_is_to_left(vertex):
            e_i_minus_one = self.get_e_i_minus_one_from_vertex(vertex)
            if "helper" in e_i_minus_one and e_i_minus_one["helper"]["type"] =="merge":
                self.add_to_dcel([vertex, e_i_minus_one["helper"]])
            # self.active_edges.remove(e_i_minus_one)
            for i, edge in enumerate(self.active_edges):
                if edge["key"] == e_i_minus_one["key"]:
                    self.active_edges.pop(i)
                    break
            e_i = self.get_e_i_from_vertex(vertex)
            self.active_edges.append(e_i)
            e_i["helper"] = vertex
        else:
            e_j = self.find_edge_directly_to_left(vertex)
            if "helper" in e_j and e_j["helper"]["type"] =="merge":
                self.add_to_dcel([vertex, e_j["helper"]])
            e_j["helper"] = vertex
        

    
    def y_monotonic_partition(self):
        vertex_colors = {
            "start": "green",
            "end": "red",
            "split": "blue",
            "merge": "purple",
            "regular": "orange"
        }
        # vertices pq
        indicident_points = sorted(self.dcel.vertices, key=lambda v: v["coords"]["y"])
        # for each vertex
        self.ax.autoscale(False)
        while len(indicident_points) > 0:

            vertex = indicident_points.pop()

            vertex_type = self.vertex_type(vertex)

            color = vertex_colors.get(vertex_type, "black")

            self.ax.scatter(vertex["coords"]["x"], vertex["coords"]["y"], c=color, s=100, zorder=10)

            self.ax.annotate(vertex["index"], (vertex["coords"]["x"], vertex["coords"]["y"]),
                textcoords="offset points",
                xytext=(5, 5),
                color=color,
                fontsize=10,
                zorder=11)

            self.ax.figure.canvas.draw()
            if vertex_type == "start":
                self.handle_start_vertex(vertex)
            elif vertex_type == "end":
                self.handle_end_vertex(vertex)
            elif vertex_type == "split":
                self.handle_split_vertex(vertex)
            elif vertex_type == "merge":
                self.handle_merge_vertex(vertex)
            elif vertex_type == "regular":
                self.handle_regular_vertex(vertex)
            else:
                print("unknown vert type")
            # match vertex_type:
            #     case "start":
            #         self.handle_start_vertex(vertex)
            #     case "end":

            #         self.handle_end_vertex(vertex)

            #     case "split":

            #         self.handle_split_vertex(vertex)
            #     case "merge":

            #         self.handle_merge_vertex(vertex)
            #     case "regular":

            #         self.handle_regular_vertex(vertex)
            #     case _:
            #         print("unknown vert type")
            self.ax.figure.canvas.draw()
            if self.slow_mode:
                plt.pause(self.delay)
        self.ax.figure.canvas.draw()

        self.dcel.add_queued_edges()

    def sidedness_test(self, a, b, c):

        cross_product = (b["x"] - a["x"]) * (c["y"] - a["y"]) - (b["y"] - a["y"]) * (c["x"] - a["x"])


        if cross_product > 0:
            return "left"
        elif cross_product < 0:
            return "right"
        else:
            return "on the line"
    def diagonal_lies_within_P(self, u_j, u_k, prev, left_chain):
        if u_j["vert"]["key"] in left_chain:
            return self.is_right_turn(u_j["vert"], prev["vert"], u_k["vert"])
        else:
            return self.is_left_turn(u_j["vert"], prev["vert"], u_k["vert"])

    def diagonal_lies_within_P_old(self, u_j, vert, left_chain, top_vert):
        u = u_j["vert"]
        v = vert["vert"]
        
        if u["key"] in left_chain:
            temp_edge = u_j["edge"]["prev"]
            temp_vert = temp_edge["origin"]
            if temp_vert["key"] == v["key"]:
                return False
            ret_val = True

            # ! can check that temp_vert[y] < v[y]
            while temp_vert["coords"]["y"] <= v["coords"]["y"] and temp_vert["key"] != v["key"] and temp_vert["key"] != top_vert["key"]:

                sidedness_output = self.sidedness_test(u_j["vert"]["coords"], v["coords"], temp_vert["coords"]) == "left"

                ret_val = ret_val and sidedness_output
                temp_edge = temp_edge["prev"]
                temp_vert = temp_edge["origin"]

            return ret_val
            
        else:
            temp_edge = u_j["edge"]["next"]
            temp_vert = temp_edge["origin"]
            if temp_vert["key"] == v["key"]:
                return False
            ret_val = True
            while temp_vert["coords"]["y"] <= v["coords"]["y"] and temp_vert["key"] != v["key"] and temp_vert["key"] != top_vert["key"]:
                ret_val = ret_val and self.sidedness_test(u_j["vert"]["coords"], v["coords"], temp_vert["coords"]) == "right"
                temp_edge = temp_edge["next"]
                temp_vert = temp_edge["origin"]
            return ret_val
        
    def get_chains(self, entry_edge, verts):
        # ! CONSTRUCT CHAINS
        highest = verts[0]
        lowest = verts[len(verts)-1]
        left_chain = set()
        right_chain = set()

        left_chain_indices = []
        right_chain_indices = []

        previous_vert = highest["vert"]
        right_chain.add(previous_vert["key"])
        right_chain_indices.append(previous_vert["index"])
        curr = highest["edge"]["prev"]
        
        while(curr["origin"]["coords"]["y"] < previous_vert["coords"]["y"]):
            right_chain.add(curr["origin"]["key"])
            right_chain_indices.append(curr["origin"]["index"])
            previous_vert = curr["origin"]
            curr = curr["prev"]

        previous_vert = highest["vert"]
        left_chain.add(previous_vert["key"])
        left_chain_indices.append(previous_vert["index"])
        curr = highest["edge"]["next"]

        while(curr["origin"]["coords"]["y"] < previous_vert["coords"]["y"]):
            left_chain.add(curr["origin"]["key"])
            left_chain_indices.append(curr["origin"]["index"])
            previous_vert = curr["origin"]
            curr = curr["next"]

        return left_chain, right_chain

    def triangulate(self, entry_edge):


        curr = entry_edge["next"]
        verts = [
            {"vert": entry_edge["origin"], "edge" : entry_edge}
        ]

        while(curr["origin"]["key"]!=entry_edge["origin"]["key"]):
            verts.append({"vert": curr["origin"], "edge": curr})
            curr = curr["next"]

        verts.sort(key=lambda v: v["vert"]["coords"]["y"], reverse=True)

        S = []
        
        S.append(verts[0])
        S.append(verts[1])

        left_chain, right_chain = self.get_chains(entry_edge, verts)


        # ! MAIN LOOP
        for j in range(2, len(verts) - 1):
            if self.current_pt is not None:
                self.current_pt.remove()
                self.current_pt = None
                self.ax.figure.canvas.draw()
            
            u_j = verts[j]
            

            x, y = u_j["vert"]["coords"]["x"], u_j["vert"]["coords"]["y"]
            radius = 2
            self.current_pt = Circle((x, y), radius, edgecolor='purple', facecolor='none', linewidth=2, zorder=12)
            self.ax.add_patch(self.current_pt)
            self.ax.figure.canvas.draw()

            if self.slow_mode:
                plt.pause(self.delay)
            top_vert = S[len(S)-1]
            # if u_j and top_vert are on different chains
            # if both on left chain, top_vert["twin"]["origin"]==u_j
            # if both on right chain u_j["twin"]["origin"]==top_vert
            u_j_in_left_chain = u_j["vert"]["key"] in left_chain
            u_j_in_right_chain = u_j["vert"]["key"] in right_chain

            top_vert_in_left_chain = top_vert["vert"]["key"] in left_chain
            top_vert_in_right_chain  = top_vert["vert"]["key"] in right_chain

            on_different_chains = (u_j_in_left_chain and top_vert_in_right_chain) or (u_j_in_right_chain and top_vert_in_left_chain)
            if on_different_chains:

                while(len(S) > 0):
                    vertex_on_top = S.pop()
                    if(len(S) > 0):
                        self.add_to_dcel([u_j["vert"], vertex_on_top["vert"]], "y-")

                S.append(verts[j-1])
                S.append(verts[j])
            else:

                # http://homepages.math.uic.edu/~jan/mcs481/triangulating.pdf
                # same chain

                u = S.pop()
                
                # while S and self.diagonal_lies_within_P(u_j, S[-1], left_chain, verts[0]["vert"]):
                while S and self.diagonal_lies_within_P(u_j, S[-1], u, left_chain):
                    u = S.pop()
                    self.add_to_dcel([u_j["vert"], u["vert"]], "b-")

                    
                # if last_valid_vert != None:
                #     S.append(last_valid_vert)
                S.append(u)
                S.append(u_j)

        u_n = verts[len(verts)-1]["vert"]
        for i in range(1, len(S)-1):
            next_vert = S[i]["vert"]
            self.add_to_dcel([u_n, next_vert], "m-")
        
    def generate_triangles(self):
        pass