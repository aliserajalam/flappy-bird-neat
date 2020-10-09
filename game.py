# Import modules
import pygame
import neat
import time
import os
import random

# Initialise font
pygame.font.init()

# Track generation
GEN = 0

# Set window width and height
WIN_WIDTH = 500
WIN_HEIGHT = 800
# Floor's position from the top of the window
FLOOR = 730
# Pygame font
STAT_FONT = pygame.font.SysFont('comicsans', 50)
# Distance between bird and the next pipe
DRAW_DISTANCE_LINES = False

# pygame.display.set_caption('Flappy Bird')

# Load game assets
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(
    os.path.join('assets', 'bird' + str(x) + '.png'))) for x in range(1, 4)]
PIPE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('assets', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('assets', 'base.png')))
BACKGROUND_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('assets', 'background.png')))


class Bird:
    """
    Represents a bird object 
    """
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25   # Max rotation or tilt of the bird
    ROT_VEL = 20    # Rotation speed each frame
    ANIMATION_TIME = 5  # Duration of animation

    def __init__(self, x, y):
        """
        Initialise the bird object
        :param x: starting horizontal pos (int)
        :param y: starting vertical pos (int)
        :return: None
        """
        # Define the initial starting position of the bird
        self.x = x
        self.y = y
        self.tilt = 0   # Angle of the bird
        self.tick_count = 0  # Bird physics tracking height
        self.vel = 0    # Speed of the bird
        self.height = self.y
        self.img_count = 0  # Track which bird image is shown
        self.img = self.IMGS[0]

    def jump(self):
        """
        Makes the bird jump
        :return: None
        """
        self.vel = -10.5    # Movement up
        self.tick_count = 0  # Reset to 0, Track change in direction or velocity
        self.height = self.y    # Where the bird started it's jump from

    # Called each frame in the game loop
    def move(self):
        """
        Makes the bird move
        :return: None
        """
        self.tick_count += 1  # Track how many frames has passed

        # Calculates displacement, track pixel changes current frame
        displacement = self.vel * self.tick_count + 1.5*self.tick_count**2

        # Terminal velocity
        if displacement >= 16:
            displacement = 16

        # Jump displacement
        if displacement < 0:
            displacement -= 2

        # Change vertical movement based on displacement
        self.y = self.y + displacement

        # Tilting the bird
        # Bird is moving upwards
        if displacement < 0 or self.y < self.height + 50:
            # Tilt the bird up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # Bird is falling
        else:
            # Tilt the bird down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Draw the bird
        :param win: Pygame window
        :return: None
        """
        # Keep track of how many frames the bird has been shown
        self.img_count += 1

        # Animating the bird wing flap based on the current game frame
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If the bird is falling, it shouldn't be flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Tilt the bird with center as it's origin
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    # Collision
    def get_mask(self):
        """
        Pygame mask of the current image of the bird
        :return: pygame.mask
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    Represents a pipe object
    """
    GAP = 200   # Distance between top and bottom pipes
    VEL = 5     # Speed of the pipes moving

    def __init__(self, x):
        """
        Initialise pipe object
        :param x: int
        :return: None
        """
        self.x = x
        self.height = 0

        # Top and bottom of the pipe
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # Tracks if the bird has passed the pipe
        self.passed = False
        # Set random height
        self.set_height()

    def set_height(self):
        """
        Sets the height of the pipe, from the top of the screen
        :return: None
        """
        # Sets the top and bottom pipe height randomly with gap inbetween
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Pipe's movement
        :return: None
        """
        self.x -= self.VEL  # Moves the pipe from right to left based on the velocity defined in class

    def draw(self, win):
        """
        Draws the top and bottom pipe in the game window
        :param win: Pygame window
        :return: None
        """
        # Draw top pipe
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # Draw bottom pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Collision detection
    def collide(self, bird):
        """
        Returns if collision is detected between the bird and pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()  # Retrieve the bird pixels bounding box
        # Get the top pipe's bounding box
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        # Get the bottom pipe's bounding box
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # How far apart the pixels are apart from each other - offset
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Point of collision / overlap
        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # If bird has collided with the top or bottom pipe
        if t_point or b_point:
            return True

        return False


class Base:
    """
    Represents the moving floor of the game    
    """
    VEL = 5  # Same velocity as pipe
    WIDTH = BASE_IMG.get_width()    # Image width
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialise the object
        :param y: int
        :return: None
        """
        self.y = y
        # Initialise two images to shift for an infinite loop visual
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Floor movement with swapping two images, gives the illusion of infinite floor
        :return: None 
        """
        # Move both images at the same velocity
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Cycle image based on the position of the image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor composed of two identical images
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    Draws the window of the game loop
    :param win: Pygame window surface
    :param bird: Bird object
    :param pipes: List of pipes
    :param base: Floor object
    :param score: Score of the game (int)
    :param pipe_ind: Index of closest pipe
    :param gen: Current generation
    :return None:
    """
    win.blit(BACKGROUND_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    # Score text in window
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    # Current generation in window
    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    # Number of alive birds in window
    score_label = STAT_FONT.render(
        "Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50))

    base.draw(win)

    for bird in birds:
        # Draw lines from bird to pipe
        if DRAW_DISTANCE_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height(
                )/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height(
                )/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # Render a bird
        bird.draw(win)

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    Runs the simulation of the current population of birds and sets fitness based on the distance traversed in the game
    :return: None
    """
    global GEN
    GEN += 1

    # Create lists to hold the genome, the neural network associated with the genome and the bird object
    nets = []
    ge = []
    birds = []

    for _, genome in genomes:
        # Setting up neural network for the genome
        genome.fitness = 0  # Start with a fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    clock = pygame.time.Clock()

    score = 0

    run = True
    # Game loop
    while run:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # In any frame, there are atmost two pipes
        pipe_ind = 0    # Consider the first pipe by default
        if len(birds) > 0:
            # If the first pipe has passed consider the next pipe
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            # Increase the fitness of bird for surviving, incentivises the bird to move
            ge[x].fitness += 0.1

            # Send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[x].activate((bird.y, abs(
                bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # Network uses a tanh function, output values are between -1 and 1
            if output[0] > 0.5:
                bird.jump()

        # bird.move()
        add_pipe = False
        rem = []  # Removal array, tracks pipes that have passed the screen
        for pipe in pipes:
            pipe.move()

            # Check for collision
            for x, bird in enumerate(birds):
                # If bird has collided with the pipe
                if pipe.collide(bird):
                    ge[x].fitness -= 1  # Fitness penalty for birds that collided
                    birds.pop(x)    # Remove the bird from the list
                    # Remove the neural network associated with the bird from the list
                    nets.pop(x)
                    # Remove the genome associated with the bird from the list
                    ge.pop(x)

                # Bird has passed the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # If pipe has passed the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        # Add a pipe
        if add_pipe:
            score += 1

            # Increase fitness score of birds that made through the pipe
            for genome in ge:
                genome.fitness += 5

            pipes.append(Pipe(600))

        # Remove pipes in removal array
        for pipe in rem:
            pipes.remove(pipe)

        for x, bird in enumerate(birds):
            # Bird collides with the floor or the ceiling
            if bird.y + bird.img.get_height() >= FLOOR or bird.y < 0:
                ge[x].fitness -= 1
                nets.pop(x)
                ge.pop(x)
                birds.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN, pipe_ind)


def run(config_path):
    # Read the configuration from the config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Create a popualation
    population = neat.Population(config)

    # Detailed statistics about each generation
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # Run for 50 generations
    winner = population.run(eval_genomes, 50)

    # Show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == "__main__":
    # Reference path to configuration file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
