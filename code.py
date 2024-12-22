from mta import get_arrivals
from time import sleep
from board import NEOPIXEL
from adafruit_matrixportal.network import Network
from adafruit_datetime import datetime, timedelta
import config
import displayio
from adafruit_matrixportal.matrix import Matrix
import adafruit_display_text.label
import terminalio

# Split the 64 x 32 matrix into a top and bottom bitmap
# and define the WxH of each bitmap
BITMAP_TOP_WIDTH = 64
BITMAP_TOP_HEIGHT = 16
BITMAP_BOTTOM_WIDTH = 64
BITMAP_BOTTOM_HEIGHT = 16
PALETTE_DEPTH = 4

# Create the matrix and display
MATRIX = Matrix()
display = MATRIX.display

# Define a top and bottom line
# Temporarily place it while we make the initial API calls
line_top = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xC84500,
    text="Connecting",
    x=2,
    y=7
)

line_bottom = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xC84500,
    text="",
    x=24,
    y=20
)

# Define the bitmaps
bitmap_top = displayio.Bitmap(BITMAP_TOP_WIDTH, BITMAP_TOP_HEIGHT, 3)
bitmap_bottom = displayio.Bitmap(BITMAP_BOTTOM_WIDTH, BITMAP_BOTTOM_HEIGHT, 3)

# Define the palettes
palette = displayio.Palette(PALETTE_DEPTH)
palette[0] = 0x000000 # off
palette[1] = 0xC84500 # yellowish
palette[2] = 0x51b0cf # blueish
palette[3] = 0xFC371E # redish

# Create a TileGrid to hold the bitmaps
top_grid = displayio.TileGrid(bitmap_top, pixel_shader=palette, width=BITMAP_TOP_WIDTH, height=BITMAP_TOP_HEIGHT)
bottom_grid = displayio.TileGrid(bitmap_bottom, pixel_shader=palette, width=BITMAP_BOTTOM_WIDTH, height=BITMAP_BOTTOM_HEIGHT)

# Place the TileGrids on top of each other
top_grid.x = 1
top_grid.y = 0
bottom_grid.x = 1
bottom_grid.y = 16

# Create a Group to hold the TileGrid
group = displayio.Group()

# Add the TileGrids and Text Lines to the Group
group.append(top_grid)
group.append(bottom_grid)
group.append(line_top)
group.append(line_bottom)

# Add the Group to the Display
display.root_group = group

# Define function to clear a bitmap
def clear_bitmap(bitmap, width, height):
    for w in range(width):
        for h in range(height):
            bitmap[w,h] = 0

# Define function to draw an icon
def draw_characters(bitmap, characters, palette_num=1, left_padding=0, left_between=6, top_padding=0):
    for c, character in enumerate(characters):
        for i in character:
            bitmap[i[0] + left_padding + (left_between * c), i[1] + top_padding] = palette_num

# Draw a heart while connecting to network
draw_characters(bitmap_bottom, [config.heart], palette_num=3, left_padding=25, top_padding=2)

# Connect to internet
network = Network(status_neopixel=NEOPIXEL, debug=False)
network.connect()
while not network.is_connected:
    sleep(5)
    network.connect()

print(f'Network connection status: {network.is_connected}')

# Draw a second heart loading message
#clear_bitmap(bitmap_bottom, BITMAP_BOTTOM_WIDTH, BITMAP_BOTTOM_HEIGHT)
draw_characters(bitmap_bottom, [config.bigger_heart], palette_num=3, left_padding=24, left_between=12, top_padding=1)

# Get the current local time
current_time = network.get_local_time()

# Reposition text to prepare to display info
line_top.text = ''
line_bottom.text = ''
line_top.x = 25
line_top.y = 8
line_bottom.x = 25
line_bottom.y = 24

# Loop through stops to display info
#while False:

while True:

    for stop in config.stops:

        # make call to MTA
        try:
            buses = get_arrivals(network=network, stop_id=stop['stop_id'], line_id=stop['line_id'])
        except Exception as e:
            print(f'Error: {e}')
            buses = {}

        # Clear the bitmaps
        clear_bitmap(bitmap=bitmap_top, width=BITMAP_TOP_WIDTH, height=BITMAP_TOP_HEIGHT)
        clear_bitmap(bitmap=bitmap_bottom, width=BITMAP_BOTTOM_WIDTH, height=BITMAP_BOTTOM_HEIGHT)

        # Show Select bus lines in blue
        palette_num = 2 if stop['is_select'] else 1

        # Draw the bus stop icons
        draw_characters(bitmap=bitmap_top, characters=stop['icon'], palette_num=palette_num, left_padding=0, left_between=7)
        draw_characters(bitmap=bitmap_bottom, characters=stop['icon'], palette_num=palette_num, left_padding=0, left_between=7)

        # Loop through metrics to display
        for metric in ['eta_minutes', 'stops_away'] * 3:
            try:
                line_top.text = str(buses[0][metric])
            except (IndexError, KeyError):
                line_top.text = '  ?'
            try:
                line_bottom.text = str(buses[1][metric])
            except (IndexError, KeyError):
                line_bottom.text = '  ?'

            # Wait 2 seconds in between each metric
            sleep(2)
        # Wait 1 second in between each bus stop
        sleep(1)
    # Wait 1 second after all bus stops have been presented
    sleep(1)
    # Refresh the local time
    current_time = network.get_local_time()




