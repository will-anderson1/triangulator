import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector, Button, Slider
from DCEL import DCEL
from Triangulator import Triangulator
from collections import defaultdict

class Main:
    def __init__(self, vertices=[]):
        self.vertices = vertices
        self.triangles = []
        self.can_triangulate = False
        self.selector = None
        self.delay = 1
    def update_delay(self, val):
        if hasattr(self, 'triangulator') and self.triangulator is not None:
            self.triangulator.delay = val
    def shift_duplicate_verts(self):
        changes = 1
        e = 1e-3
        while(changes > 0):
            x_map = {}
            y_map = {}
            changes = 0
            for i in range(len(self.vertices)):
                (x, y) = self.vertices[i]
                if x in x_map:
                    tmp = x + (e * x_map[x])
                    x_map[x]+=1
                    x = tmp
                    changes+=1
                else:
                    x_map[x] = 1
                if y in y_map:
                    tmp = y + (e * y_map[y])
                    y_map[y]+=1
                    y = tmp
                    changes+=1
                else:
                    y_map[y] = 1
                self.vertices[i]=(x, y)
        return self.vertices

    def handle_start_triangulation_slow(self, event=None):
        self.handle_start_triangulation(slow_mode=True)
    def handle_start_triangulation(self, event=None, slow_mode=False):
        if(not self.can_triangulate):
            print("Cannot triangulate yet!")
            return
        self.DCEL = DCEL(self.ax, self.plt)


        self.shift_duplicate_verts()
        self.DCEL.init_from_vertex_list(self.vertices)
        
        # self.DCEL.draw_inner_face()
        # print("slow mode: ")
        # print(slow_mode)
        self.triangulator = Triangulator(self.DCEL, self.plt, self.ax, slow_mode)
        if slow_mode:
            self.triangulator.delay = self.delay_slider.val
        self.triangulator.y_monotonic_partition()
        # self.DCEL.draw_faces()
        
        if len(self.DCEL.added_edges) == 0:
            self.triangulator.triangulate(self.DCEL.inner_face["outer_component"])
        else:
            for i in self.DCEL.faces:
                if i["key"] == "outer":
                    continue
                self.triangulator.triangulate(i["outer_component"])

        self.ax.figure.canvas.draw()

    def reset(self, event=None):
        
        self.ax.clear()
        self.ax.set_title("Draw a polygon")
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        
        self.vertices = []
        self.triangles = []
        self.can_triangulate = False
        self.triangulator = None
        self.DCEL = None
        
        self.selector.disconnect_events()
        self.selector = PolygonSelector(self.ax, self.on_select, useblit=True)
        
        self.ax.figure.canvas.draw()
    def on_select(self, verts):
        self.vertices = verts
        self.can_triangulate = True

    def start_selector(self):
        self.plt, self.ax = plt.subplots()
        self.ax.set_title("Draw a polygon")
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        selector = PolygonSelector(self.ax, self.on_select, useblit=True)
        self.selector = selector

        ax_triangulate_button = plt.axes([0.85, 0.9, 0.1, 0.075])
        triangulate_button = Button(ax_triangulate_button, 'Fast')
        triangulate_button.on_clicked(self.handle_start_triangulation)

        ax_triangulate_button_slow = plt.axes([0.7, 0.9, 0.1, 0.075])
        triangulate_button_slow = Button(ax_triangulate_button_slow, 'Slow')
        triangulate_button_slow.on_clicked(self.handle_start_triangulation_slow)


        ax_delay_slider = plt.axes([0.2, 0.02, 0.4, 0.03])
        self.delay_slider = Slider(ax=ax_delay_slider, label='Delay (seconds)',valmin=0.1,valmax=5.0,valinit=self.delay,valstep=0.1)

        ax_reset_button = plt.axes([0.1, 0.9, 0.1, 0.075])
        reset_button = Button(ax_reset_button, 'Reset')
        reset_button.on_clicked(self.reset)
        plt.show()

if __name__ == "__main__":
    triangulator = Main()
    triangulator.start_selector()
    
