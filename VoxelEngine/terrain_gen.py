from noise import noise2, noise3
from random import random
from settings import *
import math
from numba import njit


@njit
def get_height(x, z):
    # island mask
    island = 1 / (pow(0.0025 * math.hypot(x - CENTER_XZ, z - CENTER_XZ), 20) + 0.0001)
    island = min(island, 1)

    # amplitude
    base_amplitude = CENTER_Y
    a1 = base_amplitude
    a2, a4, a8 = a1 * 0.5, a1 * 0.25, a1 * 0.125

    # frequency
    f1 = 0.007
    f2, f4, f8 = f1 * 2, f1 * 4, f1 * 8

    # Terrain type noise (valleys and mountains)
    terrain_noise = noise2(x * 0.002, z * 0.002)
    if terrain_noise < 0:
        terrain_noise = -math.pow(terrain_noise, 2)  # Exaggerate valleys by making them flatter
    else:
        terrain_noise = math.pow(terrain_noise, 4)  # Exaggerate mountains

    # Adjust amplitudes based on terrain type
    a1 *= 1 + terrain_noise * 5  # Increase the impact for mountains
    a2 *= 1 + terrain_noise * 5
    a4 *= 1 + terrain_noise * 5
    a8 *= 1 + terrain_noise * 5

    height = 0
    height += noise2(x * f1, z * f1) * a1 + a1
    height += noise2(x * f2, z * f2) * a2 - a2
    height += noise2(x * f4, z * f4) * a4 + a4
    height += noise2(x * f8, z * f8) * a8 - a8

    height = max(height, noise2(x * f8, z * f8) + 2)
    height *= island

    return int(height)


@njit
def get_index(x, y, z):
    return x + CHUNK_SIZE * z + CHUNK_AREA * y


@njit
def set_voxel_id(voxels, x, y, z, wx, wy, wz, world_height):
    voxel_id = 0

    if wy < world_height - 1:
        # create caves
        if (noise3(wx * 0.09, wy * 0.09, wz * 0.09) > 0 and
                noise2(wx * 0.1, wz * 0.1) * 3 + 3 < wy < world_height - 10):
            voxel_id = 0
        else:
            voxel_id = STONE
    else:
        rng = int(7 * random())
        ry = wy - rng
        if SNOW_LVL <= ry < world_height:
            voxel_id = SNOW
        elif STONE_LVL <= ry < SNOW_LVL:
            voxel_id = STONE
        elif DIRT_LVL <= ry < STONE_LVL:
            voxel_id = DIRT
        elif GRASS_LVL <= ry < DIRT_LVL:
            voxel_id = GRASS
        else:
            voxel_id = SAND

    # setting ID
    voxels[get_index(x, y, z)] = voxel_id

    # place tree
    if wy < DIRT_LVL:
        place_tree(voxels, x, y, z, voxel_id)


@njit
def place_tree(voxels, x, y, z, voxel_id):
    rnd = random()
    if voxel_id != GRASS or rnd > TREE_PROBABILITY:
        return None
    if y + TALL_TREE_HEIGHT >= CHUNK_SIZE:
        return None
    if x - TALL_TREE_H_WIDTH < 0 or x + TALL_TREE_H_WIDTH >= CHUNK_SIZE:
        return None
    if z - TALL_TREE_H_WIDTH < 0 or z + TALL_TREE_H_WIDTH >= CHUNK_SIZE:
        return None

    # dirt under the tree
    voxels[get_index(x, y, z)] = DIRT

    # leaves
    for iy in range(TALL_TREE_H_HEIGHT, TALL_TREE_HEIGHT):
        for ix in range(-TALL_TREE_H_WIDTH, TALL_TREE_H_WIDTH):
            for iz in range(-TALL_TREE_H_WIDTH, TALL_TREE_H_WIDTH):
                if (ix * ix + iz * iz + (iy - TALL_TREE_H_HEIGHT) ** 2) < TALL_TREE_H_WIDTH ** 2:
                    if random() > 0.4:  # Increased randomness for more natural placement
                        if random() > (
                                abs(ix) + abs(iz)) / TALL_TREE_H_WIDTH:  # Vary density based on distance from trunk
                            voxels[get_index(x + ix, y + iy, z + iz)] = LEAVES

    # tree trunk
    for iy in range(1, TALL_TREE_HEIGHT - 2):
        voxels[get_index(x, y + iy, z)] = WOOD

    # top
    voxels[get_index(x, y + TALL_TREE_HEIGHT - 2, z)] = LEAVES


# New constants for taller and larger trees
TALL_TREE_HEIGHT = 12
TALL_TREE_H_WIDTH = 6
TALL_TREE_H_HEIGHT = 6
TREE_PROBABILITY = 0.01  # Adjust the probability as needed
