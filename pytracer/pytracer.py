from enum import Enum
class Arch(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    CUDA = "cuda"
    METAL = "metal"
    OPENGL = "opengl"
    VULKAN = "vulkan"

import taichi as ti
import dearpygui.dearpygui as dpg
import numpy as np

class PyTracer:
    PRIMARY_WINDOW_TAG = "primary"
    SCREEN_BUFFER_TAG = "buffer"
    IMAGE_WIDGET_TAG = "image_widget"
    FPS_LABEL_TAG = "fps_label"
    RESOLUTION_LABEL_TAG = "resolution_label"
    RENDER_RESOLUTION_LABEL_TAG = "render_resolution_label"
    LOOK_AT_LABEL_TAG = "look_at_label"

    def __init__(self, resolution: tuple[int,int]=(1280,720), arch: Arch=Arch.CPU, render_resolution_factor: float=1.0):
        self.resolution = resolution
        self.arch : ti.types.arch = self._get_arch(arch)
        self.arch_param = arch
        ti.init(arch=self.arch)

        window_width, window_height = resolution
        render_width, render_height = int(window_width * render_resolution_factor), int(window_height * render_resolution_factor)

        self.width, self.height = window_width, window_height
        self.render_width, self.render_height = render_width, render_height

        self.screen_buffer: ti.types.vector = ti.Vector.field(3, ti.f32, shape=(render_height, render_width))

    def _on_resize_callback(self, sender, app_data):
        width, height, _, _ = app_data
        dpg.configure_item(self.IMAGE_WIDGET_TAG, width=width, height=height)
        dpg.configure_item(self.RESOLUTION_LABEL_TAG, default_value=f"Resolution: {width}x{height}")

    @staticmethod
    def _get_arch(arch: Arch):
        if arch == Arch.CPU:
            return ti.cpu
        elif arch == Arch.GPU:
            return ti.gpu
        elif arch == Arch.CUDA:
            return ti.cuda
        elif arch == Arch.METAL:
            return ti.metal
        elif arch == Arch.OPENGL:
            return ti.opengl
        elif arch == Arch.VULKAN:
            return ti.vulkan
        else:
            raise ValueError("Invalid architecture")
        
    def _init_dpg(self):
        dpg.create_context()
        dpg.create_viewport(title='Py-Tracer', width=self.width, height=self.height)
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(width=self.render_width
                                , height=self.render_height
                                , default_value = self.screen_buffer.to_numpy()
                                , format=dpg.mvFormat_Float_rgb
                                , tag=self.SCREEN_BUFFER_TAG)
            
        with dpg.window(tag=self.PRIMARY_WINDOW_TAG):
            dpg.add_image(self.SCREEN_BUFFER_TAG
                          , tag=self.IMAGE_WIDGET_TAG
                          , width=self.width
                          , height=self.height
                          , uv_min=(0,1), uv_max=(1,0))
            
            with dpg.theme() as no_border_th:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0,0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 0,0, category=dpg.mvThemeCat_Core)

            dpg.bind_item_theme(self.PRIMARY_WINDOW_TAG, no_border_th)


        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_viewport_vsync(False)
        dpg.set_primary_window(self.PRIMARY_WINDOW_TAG, True)

        dpg.set_viewport_resize_callback(self._on_resize_callback)

    def _create_info_window(self):
        with dpg.window(label="Info"):
            dpg.add_text(f"FPS: {dpg.get_frame_rate()}", tag=self.FPS_LABEL_TAG)
            dpg.add_text(f"Resolution: {self.width}x{self.height}" , tag=self.RESOLUTION_LABEL_TAG)
            dpg.add_text(f"Render Resolution: {self.render_width}x{self.render_height}" , tag=self.RENDER_RESOLUTION_LABEL_TAG)
            dpg.add_text(f"Arch: {self.arch_param}")
            dpg.add_text(f"Loot at: 0, 0, 0", tag=self.LOOK_AT_LABEL_TAG)
    
    def _update_info_window(self):
        dpg.set_value(self.FPS_LABEL_TAG, f"FPS: {dpg.get_frame_rate()}")
        # dpg.set_value(self.RESOLUTION_LABEL_TAG, f"Resolution: {self.width}x{self.height}")
        dpg.set_value(self.RENDER_RESOLUTION_LABEL_TAG, f"Render Resolution: {self.render_width}x{self.render_height}")
    def run(self):
        self._init_dpg()
        self._create_info_window()

        from .render import Renderer, Scene, Sphere, Material
        import taichi.math as tm

        scene = Scene()
        scene.map.append(Sphere(tm.vec3(0, 0, 0), 1, Material(tm.vec3(1, 0, 0), tm.vec3(0, 0, 0), 0)))
        scene.map.append(Sphere(tm.vec3(2, 0, 0), 1, Material(tm.vec3(0, 1, 0), tm.vec3(0, 0, 0), 0)))
        scene.map.append(Sphere(tm.vec3(0, 5, 5), 4, Material(tm.vec3(0,0,0), tm.vec3(1,1,1), 1.0)))
        scene.map.append(Sphere(tm.vec3(0, -101, 0), 100, Material(tm.vec3(0,0,1), tm.vec3(0,0,0), 0.0)))

        renderer = Renderer(self.screen_buffer, tm.vec2(self.render_height, self.render_width), scene, 4)
        look_at = tm.vec3(1, 0, 0)
        while dpg.is_dearpygui_running():
            
            dpg.set_value(self.LOOK_AT_LABEL_TAG, f"Loot at: {look_at.x:.2f}, {look_at.y:.2f}, {look_at.z:.2f}")
            
            look_at = tm.vec3(ti.sin(dpg.get_total_time()), 0, ti.cos(dpg.get_total_time()))
            renderer.render(look_at)

            dpg.set_value(self.SCREEN_BUFFER_TAG, self.screen_buffer.to_numpy())
            self._update_info_window()
            dpg.render_dearpygui_frame()    
            

        dpg.destroy_context()
        