#!/usr/bin/env python3
"""
Asteroids Game - Versione classica con grafica raster
Controlli: 
- Frecce per ruotare e accelerare
- Spazio per sparare
- ESC per uscire
"""

import pygame
import math
import random
import sys

# Inizializzazione pygame
pygame.init()

# Costanti del gioco
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colori (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

class Vector2D:
    """Classe per gestire vettori 2D"""
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector2D(self.x / mag, self.y / mag)
        return Vector2D(0, 0)

class GameObject:
    """Classe base per tutti gli oggetti del gioco"""
    def __init__(self, x, y):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(0, 0)
        self.angle = 0
        self.radius = 10
        self.active = True
    
    def update(self, dt):
        # Aggiorna posizione
        self.position = self.position + self.velocity * dt
        
        # Wrap around screen (effetto tunnel)
        self.position.x = self.position.x % SCREEN_WIDTH
        self.position.y = self.position.y % SCREEN_HEIGHT
    
    def draw(self, screen):
        pass
    
    def check_collision(self, other):
        distance = math.sqrt((self.position.x - other.position.x)**2 + 
                           (self.position.y - other.position.y)**2)
        return distance < (self.radius + other.radius)

class Ship(GameObject):
    """Classe per la navicella del giocatore"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = 8
        self.thrust = 0
        self.rotation_speed = 0
        self.max_speed = 300
        self.thrust_power = 200
        self.friction = 0.98
        
        # Punti per disegnare la navicella (triangolo)
        self.ship_points = [
            (0, -10),   # Punta
            (-6, 8),    # Base sinistra
            (6, 8)      # Base destra
        ]
    
    def update(self, dt):
        # Rotazione
        self.angle += self.rotation_speed * dt
        
        # Thrust (accelerazione)
        if self.thrust > 0:
            thrust_x = math.cos(math.radians(self.angle - 90)) * self.thrust_power * dt
            thrust_y = math.sin(math.radians(self.angle - 90)) * self.thrust_power * dt
            self.velocity.x += thrust_x
            self.velocity.y += thrust_y
        
        # Limita velocità massima
        speed = self.velocity.magnitude()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        
        # Attrito
        self.velocity = self.velocity * self.friction
        
        super().update(dt)
    
    def draw(self, screen):
        # Calcola i punti ruotati della navicella
        rotated_points = []
        for point in self.ship_points:
            # Ruota il punto
            cos_a = math.cos(math.radians(self.angle))
            sin_a = math.sin(math.radians(self.angle))
            
            rotated_x = point[0] * cos_a - point[1] * sin_a
            rotated_y = point[0] * sin_a + point[1] * cos_a
            
            # Trasla alla posizione della navicella
            final_x = rotated_x + self.position.x
            final_y = rotated_y + self.position.y
            
            rotated_points.append((final_x, final_y))
        
        # Disegna la navicella
        pygame.draw.polygon(screen, WHITE, rotated_points)
        
        # Disegna il thrust se attivo
        if self.thrust > 0:
            thrust_length = 15
            thrust_x = self.position.x - math.cos(math.radians(self.angle - 90)) * thrust_length
            thrust_y = self.position.y - math.sin(math.radians(self.angle - 90)) * thrust_length
            pygame.draw.line(screen, YELLOW, (self.position.x, self.position.y), 
                           (thrust_x, thrust_y), 2)

class Bullet(GameObject):
    """Classe per i proiettili"""
    def __init__(self, x, y, angle):
        super().__init__(x, y)
        self.radius = 2
        self.speed = 400
        self.lifetime = 2.0  # secondi
        self.age = 0
        
        # Imposta velocità basata sull'angolo
        self.velocity.x = math.cos(math.radians(angle - 90)) * self.speed
        self.velocity.y = math.sin(math.radians(angle - 90)) * self.speed
    
    def update(self, dt):
        super().update(dt)
        self.age += dt
        if self.age > self.lifetime:
            self.active = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, 
                         (int(self.position.x), int(self.position.y)), 
                         self.radius)

class Asteroid(GameObject):
    """Classe per gli asteroidi"""
    def __init__(self, x, y, size=3):
        super().__init__(x, y)
        self.size = size  # 1=piccolo, 2=medio, 3=grande
        self.radius = 10 + size * 15
        self.rotation_speed = random.uniform(-180, 180)
        
        # Velocità casuale
        speed = random.uniform(20, 80)
        direction = random.uniform(0, 360)
        self.velocity.x = math.cos(math.radians(direction)) * speed
        self.velocity.y = math.sin(math.radians(direction)) * speed
        
        # Genera forma irregolare dell'asteroide
        self.points = []
        num_points = 8
        for i in range(num_points):
            angle = (360 / num_points) * i
            # Varia il raggio per forma irregolare
            radius_variation = random.uniform(0.7, 1.3)
            point_radius = self.radius * radius_variation
            
            x = math.cos(math.radians(angle)) * point_radius
            y = math.sin(math.radians(angle)) * point_radius
            self.points.append((x, y))
    
    def update(self, dt):
        super().update(dt)
        self.angle += self.rotation_speed * dt
    
    def draw(self, screen):
        # Calcola i punti ruotati dell'asteroide
        rotated_points = []
        for point in self.points:
            cos_a = math.cos(math.radians(self.angle))
            sin_a = math.sin(math.radians(self.angle))
            
            rotated_x = point[0] * cos_a - point[1] * sin_a
            rotated_y = point[0] * sin_a + point[1] * cos_a
            
            final_x = rotated_x + self.position.x
            final_y = rotated_y + self.position.y
            
            rotated_points.append((final_x, final_y))
        
        pygame.draw.polygon(screen, WHITE, rotated_points, 2)
    
    def split(self):
        """Divide l'asteroide in pezzi più piccoli"""
        if self.size > 1:
            fragments = []
            for _ in range(2):
                fragment = Asteroid(self.position.x, self.position.y, self.size - 1)
                # Aggiungi velocità casuale ai frammenti
                fragment.velocity.x += random.uniform(-50, 50)
                fragment.velocity.y += random.uniform(-50, 50)
                fragments.append(fragment)
            return fragments
        return []

class Game:
    """Classe principale del gioco"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Asteroids")
        self.clock = pygame.time.Clock()
        
        # Oggetti del gioco
        self.ship = Ship(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.bullets = []
        self.asteroids = []
        
        # Stato del gioco
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        
        # Genera asteroidi iniziali
        self.spawn_asteroids(5)
    
    def spawn_asteroids(self, count):
        """Genera asteroidi casuali"""
        for _ in range(count):
            # Posiziona lontano dalla navicella
            while True:
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                distance = math.sqrt((x - self.ship.position.x)**2 + 
                                   (y - self.ship.position.y)**2)
                if distance > 100:  # Distanza minima dalla navicella
                    break
            
            asteroid = Asteroid(x, y, 3)
            self.asteroids.append(asteroid)
    
    def handle_input(self):
        """Gestisce input da tastiera"""
        keys = pygame.key.get_pressed()
        
        # Reset controlli
        self.ship.thrust = 0
        self.ship.rotation_speed = 0
        
        # Rotazione
        if keys[pygame.K_LEFT]:
            self.ship.rotation_speed = -180
        if keys[pygame.K_RIGHT]:
            self.ship.rotation_speed = 180
        
        # Thrust
        if keys[pygame.K_UP]:
            self.ship.thrust = 1
        
        # Sparo (gestito negli eventi per evitare sparo continuo)
    
    def update(self, dt):
        """Aggiorna logica del gioco"""
        if self.game_over:
            return
        
        # Aggiorna oggetti
        self.ship.update(dt)
        
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not bullet.active:
                self.bullets.remove(bullet)
        
        for asteroid in self.asteroids[:]:
            asteroid.update(dt)
        
        # Collisioni proiettili-asteroidi
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                if bullet.check_collision(asteroid):
                    # Rimuovi proiettile e asteroide
                    self.bullets.remove(bullet)
                    self.asteroids.remove(asteroid)
                    
                    # Aggiungi punti
                    self.score += (4 - asteroid.size) * 20
                    
                    # Dividi asteroide
                    fragments = asteroid.split()
                    self.asteroids.extend(fragments)
                    break
        
        # Collisioni navicella-asteroidi
        for asteroid in self.asteroids:
            if self.ship.check_collision(asteroid):
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    # Respawn navicella al centro
                    self.ship.position = Vector2D(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    self.ship.velocity = Vector2D(0, 0)
                break
        
        # Controlla se tutti gli asteroidi sono distrutti
        if not self.asteroids:
            self.spawn_asteroids(5 + self.score // 1000)  # Più asteroidi con il punteggio
    
    def draw(self):
        """Disegna tutto sullo schermo"""
        self.screen.fill(BLACK)
        
        # Disegna oggetti
        if not self.game_over:
            self.ship.draw(self.screen)
        
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        
        # UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (10, 50))
        
        if self.game_over:
            game_over_text = self.font.render("GAME OVER - Press R to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()
    
    def restart(self):
        """Riavvia il gioco"""
        self.ship = Ship(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.bullets = []
        self.asteroids = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.spawn_asteroids(5)
    
    def run(self):
        """Loop principale del gioco"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in secondi
            
            # Eventi
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and not self.game_over:
                        # Spara
                        bullet = Bullet(self.ship.position.x, self.ship.position.y, self.ship.angle)
                        self.bullets.append(bullet)
                    elif event.key == pygame.K_r and self.game_over:
                        self.restart()
            
            # Input continuo
            self.handle_input()
            
            # Aggiorna e disegna
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
