import taichi as ti
import taichi.math as tm
from .rng import Rng


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
    emissive_color: tm.vec3 
    emissive_strength: ti.f32

@ti.dataclass
class Hit:
    position: tm.vec3 
    normal: tm.vec3 
    distance: ti.f32
    material: Material
    hit : ti.i8 


# @ti.func
# def random_u32(seed: ti.u32) -> ti.u32:
#     new_seed = seed + (seed << 10)
#     new_seed = new_seed ^ (new_seed >> 6)
#     new_seed = new_seed + (new_seed << 3)
#     new_seed = new_seed ^ (new_seed >> 11)
#     new_seed = new_seed + (new_seed << 15)
#     return new_seed




@ti.dataclass
class Sphere:
    position: tm.vec3
    radius : ti.f32
    material: Material

    @ti.func
    def intersect(self, ray: Ray) -> Hit: # return distance or negative if no hit
        offsetRayOrigin = ray.origin - self.position
        a: ti.f32 = tm.dot(ray.direction, ray.direction)
        b: ti.f32 = 2 * tm.dot(offsetRayOrigin, ray.direction)
        c: ti.f32 = tm.dot(offsetRayOrigin, offsetRayOrigin) - self.radius * self.radius

        discriminant: ti.f32 = b * b - 4 * a * c
        hit_info= Hit(tm.vec3(0,0,0), tm.vec3(0,0,0), -1.0, self.material,0)

        if discriminant >= 0:
            hit_info.distance = (-b - tm.sqrt(discriminant)) / (2 * a)
            hit_info.position = ray.origin + ray.direction * hit_info.distance
            hit_info.normal = tm.normalize(self.position - hit_info.position)
            hit_info.hit = ti.cast(1, ti.i8)

        return hit_info

@ti.data_oriented
class Scene:
    def __init__(self):
        self.map : Sphere = []


@ti.data_oriented
class Renderer:
    def __init__(self, buffer: ti.types.vector
                 , resolution: tm.vec2
                 , scene: Scene
                 , bounce_limit: ti.i32 = 2
                 , samples: ti.i32 = 4):
        self.buffer = buffer
        self.resolution = resolution
        self.scene = scene
        self.bounce_limit = bounce_limit
        self.samples = samples
        
    @ti.func
    def trace_ray(self, ray: Ray) -> Hit:

        hit_info = Hit()
        hit_info.distance = 1000000.0
        
        for i in ti.static(range(len(self.scene.map))):
            sphere = self.scene.map[i]
            hit_info_new = sphere.intersect(ray)
            if hit_info_new.hit == 1 and (hit_info_new.distance < hit_info.distance):
                hit_info = hit_info_new

        return hit_info
    
    @ti.func
    def calculate_color(self, ray: Ray, rng) -> tm.vec3:
        ray_color = tm.vec3(1, 1, 1)
        accumulated_light = tm.vec3(0, 0, 0)

        for _ in range(self.bounce_limit):
            hit_info = self.trace_ray(ray)
            if hit_info.hit == 0:
                break

            ray.origin = hit_info.position
            ray.direction = tm.normalize(hit_info.normal + rng.random_direction())

            light = hit_info.material.emissive_color * hit_info.material.emissive_strength
            accumulated_light += ray_color * light
            ray_color *= hit_info.material.color
        
        return accumulated_light

    @ti.kernel
    def render(self,frame_count: ti.u64 , oscilating: tm.vec3):
        for i, j in self.buffer:
            uv = (tm.vec2(i, j) - 0.5 * self.resolution) / self.resolution.x # make 0,0 in the center and fix aspect ratio
            uv = tm.vec2(uv.y, uv.x) # flip x and y ... idk, some kind of taichi -> numpy -> imgui thing

            random_seed : ti.u32 = i * 420420 * j * 696969 + 696969 + frame_count * 42069
            rng = Rng(random_seed)

            campos = oscilating
            cam = Camera(campos, tm.vec3(0,0,0))
            ray = Ray(cam.position, cam.look_at(uv))

            final_color = tm.vec3(0,0,0)
            for _ in range(self.samples):
                final_color += self.calculate_color(ray, rng)
                rng.next()

            final_color /= self.samples

            # progressive rendering
            color_weight: ti.f32 = 1.0 / (frame_count + 1)
            self.buffer[i, j] = self.buffer[i, j] * (1.0 - color_weight) + final_color * color_weight
            