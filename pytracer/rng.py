import taichi as ti
import taichi.math as tm
@ti.dataclass
class Rng:
    state: ti.u32 = 0

    # https://stackoverflow.com/questions/4200224/random-noise-functions-for-glsl
    @ti.func
    def random_u32(self) -> ti.u32:
        new_seed = self.state + (self.state << 10)
        new_seed = new_seed ^ (new_seed >> 6)
        new_seed = new_seed + (new_seed << 3)
        new_seed = new_seed ^ (new_seed >> 11)
        new_seed = new_seed + (new_seed << 15)
        self.state = new_seed
        return new_seed
    
    @ti.func
    def random_f32(self) -> ti.f32:
        return ti.cast(self.random_u32(), ti.f32) / 4294967295.0
    
    @ti.func
    def random_uniform_f32(self) -> ti.f32:
        theta = 2 * 3.1415926535 * self.random_f32()
        rho = tm.sqrt(-2 * tm.log(1 - self.random_f32()))
        return rho * tm.cos(theta)
    
    @ti.func
    def random_direction(self) -> tm.vec3:
        return tm.normalize(tm.vec3(self.random_uniform_f32()
                          , self.random_uniform_f32()
                          , self.random_uniform_f32()))
    
    @ti.func
    def random_direction_in_hemisphere(self, normal: tm.vec3) -> tm.vec3:
        direction = self.random_direction()
        return direction * tm.sign(tm.dot(normal, direction))
