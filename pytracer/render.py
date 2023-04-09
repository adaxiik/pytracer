import taichi as ti
import taichi.math as tm



class Scene:
    def __init__(self):
        self.map : Sphere = []

@ti.dataclass
class Camera:
    position: tm.vec3
    target: tm.vec3
    @ti.func
    def look_at(self, uv: tm.vec2) -> tm.vec3:
        up = tm.vec3(0, 1, 0)
        forward = tm.normalize(self.target - self.position)
        right = tm.normalize(tm.cross(up, forward))
        up_ = tm.cross(forward, right)
        c = self.position + forward  # * self.zoom
        i = c + right * uv.x + up_ * uv.y
        return tm.normalize(i - self.position)
    
@ti.dataclass
class Ray:
    origin: tm.vec3
    direction: tm.vec3

@ti.dataclass
class Material:
    color: tm.vec3

@ti.dataclass
class Sphere:
    position: tm.vec3
    radius : ti.f32
    material: Material

    @ti.func
    def intersect(self, ray: Ray) -> ti.f32: # return distance or negative if no hit
        offsetRayOrigin = ray.origin - self.position
        a: ti.f32 = tm.dot(ray.direction, ray.direction)
        b: ti.f32 = 2 * tm.dot(offsetRayOrigin, ray.direction)
        c: ti.f32 = tm.dot(offsetRayOrigin, offsetRayOrigin) - self.radius * self.radius

        discriminant: ti.f32 = b * b - 4 * a * c
        distance: ti.f32 = -10
        if discriminant >= 0:
            distance: ti.f32 = (-b - tm.sqrt(discriminant)) / (2 * a)
        
        return distance



@ti.data_oriented
class Renderer:
    def __init__(self, buffer: ti.types.vector, resolution: tm.vec2):
        self.buffer = buffer
        self.resolution = resolution
        
    @ti.func
    def ray_cast(self, ray: Ray) -> tm.vec3:
        output_color = tm.vec3(0, 0, 0)
        sphere = Sphere(tm.vec3(5, 1, 0), 1, Material(tm.vec3(1, 0, 0)))

        intersection_distance = sphere.intersect(ray)
        if intersection_distance >= 0:
            output_color = sphere.material.color

        
        return output_color
    


    @ti.kernel
    def render(self, look_at: tm.vec3):
        for i, j in self.buffer:
            uv = (tm.vec2(i, j) - 0.5 * self.resolution) / self.resolution.x # make 0,0 in the center and fix aspect ratio
            uv = tm.vec2(uv.y, uv.x) # flip x and y ... idk, some kind of taichi -> numpy -> imgui thing
        
            # self.buffer[i, j] = tm.vec3(uv, 0)

            # radius = 0.125
            # dist = tm.length(uv - tm.vec2(look_at[0]/4, look_at[2]/4)) - radius
            # if dist < radius:
            #     self.buffer[i, j] = tm.vec3(1, 0, 0)

            cam = Camera(tm.vec3(0,0,0), look_at)
            ray = Ray(cam.position, cam.look_at(uv))
            
            self.buffer[i, j] = self.ray_cast(ray)