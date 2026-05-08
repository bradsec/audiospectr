from __future__ import annotations
import math
import random
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    age: float = 0.0


class ParticlesLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self.particles: list[Particle] = []

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        flow_mode     = self.config.get("flow_mode", "radial")
        spawn_rate    = float(self.config.get("spawn_rate", 18))
        vel_mult      = float(self.config.get("velocity_multiplier", 7.0))
        lifetime      = float(self.config.get("lifetime", 95))
        size          = int(self.config.get("particle_size", 5))
        color         = self.config.get("color", "#ffffff")
        direction     = float(self.config.get("direction", 270.0))
        max_particles = int(self.config.get("max_particles", 3500))
        spread        = float(self.config.get("spawn_spread", 0.22))

        volume  = float(np.clip(frame_data.rms, 0.0, 1.0))
        n_spawn = max(0, int(spawn_rate * volume * 2.0)) if volume > 0.01 else 0
        cx, cy  = self.width // 2, self.height // 2
        r_color, g_color, b_color = ImageColor.getrgb(color)

        self.particles = self.particles[-max_particles:]

        for _ in range(n_spawn):
            speed = volume * vel_mult
            if flow_mode == "radial":
                angle = random.uniform(0, 2 * math.pi)
                jitter = random.uniform(0.65, 1.25)
                vx    = math.cos(angle) * speed * jitter
                vy    = math.sin(angle) * speed * jitter
                spawn_radius = random.uniform(0, min(self.width, self.height) * spread)
                spawn_angle = random.uniform(0, 2 * math.pi)
                px = cx + math.cos(spawn_angle) * spawn_radius
                py = cy + math.sin(spawn_angle) * spawn_radius
            else:
                rad = math.radians(direction)
                vx  = math.cos(rad) * speed + random.uniform(-0.3, 0.3)
                vy  = math.sin(rad) * speed + random.uniform(-0.3, 0.3)
                if abs(math.cos(rad)) >= abs(math.sin(rad)):
                    # Primarily horizontal: spawn from left (dir=0) or right (dir=180) edge
                    px = 0.0 if math.cos(rad) > 0 else float(self.width)
                    py = random.uniform(0, self.height)
                else:
                    # Primarily vertical: spawn from top (dir=90) or bottom (dir=270) edge
                    px = random.uniform(0, self.width)
                    py = 0.0 if math.sin(rad) > 0 else float(self.height)
            self.particles.append(Particle(px, py, vx, vy, lifetime))

        alive: list[Particle] = []
        for p in self.particles:
            p.x   += p.vx
            p.y   += p.vy
            p.age += 1.0
            if p.age >= p.lifetime:
                continue
            if not (0 <= p.x < self.width and 0 <= p.y < self.height):
                continue
            alpha = int(255 * (1.0 - p.age / p.lifetime))
            half  = max(1, size // 2)
            draw.ellipse(
                [p.x - half, p.y - half, p.x + half, p.y + half],
                fill=(r_color, g_color, b_color, alpha),
            )
            alive.append(p)

        self.particles = alive
        return surface
