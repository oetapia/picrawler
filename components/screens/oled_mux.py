import os
import board
import busio
import adafruit_ssd1306
import time
from PIL import Image, ImageDraw

# Import multiplexer controller
from components.sensors.pca9548a_mux import PCA9548A

# Define the font path relative to the directory of this file
FONT_PATH = os.path.join(os.path.dirname(__file__), 'font5x8.bin')

# Global variables
display = None
mux = None
oled_channel = None

def initialize_display(use_multiplexer=True, mux_address=0x70, channel=None, oled_address=0x3C):
    """
    Initialize OLED display with optional multiplexer support.
    
    Args:
        use_multiplexer (bool): Whether to use PCA9548A multiplexer
        mux_address (int): Multiplexer I2C address (default 0x70)
        channel (int): Multiplexer channel number (0-7), or None to auto-detect
        oled_address (int): OLED I2C address (default 0x3C)
    
    Returns:
        bool: True if successful, False otherwise
    """
    global display, mux, oled_channel
    
    try:
        if use_multiplexer:
            print(f"Initializing OLED through multiplexer at 0x{mux_address:02X}...")
            
            # Initialize multiplexer
            mux = PCA9548A(bus_number=1, address=mux_address)
            print(f"  [OK] Multiplexer initialized")
            
            # If channel not specified, scan for OLED
            if channel is None:
                print("  Scanning multiplexer channels for OLED...")
                for ch in range(8):
                    devices = mux.scan_channel(ch)
                    if oled_address in devices:
                        channel = ch
                        print(f"  [OK] OLED found on channel {channel}")
                        break
                
                if channel is None:
                    print("  [X] OLED not found on any multiplexer channel!")
                    print(f"      Looking for address 0x{oled_address:02X}")
                    mux.close()
                    mux = None
                    return False
            else:
                print(f"  Using specified channel {channel}")
            
            oled_channel = channel
            
            # Select the channel
            mux.select_channel(oled_channel)
            print(f"  [OK] Selected multiplexer channel {oled_channel}")
            time.sleep(0.05)  # Small delay after channel switch
        
        # Initialize I2C with default pins
        print("  Initializing I2C connection...")
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Scan for I2C devices
        print("  Scanning I2C bus...")
        timeout = time.time() + 2.0
        while not i2c.try_lock() and time.time() < timeout:
            time.sleep(0.01)
        
        if i2c.try_lock():
            try:
                devices = i2c.scan()
                print(f'  I2C devices found: {[hex(d) for d in devices]}')
                
                if oled_address not in devices:
                    print(f"  [X] OLED address 0x{oled_address:02X} not found in scan!")
                    i2c.unlock()
                    if mux:
                        mux.close()
                        mux = None
                    return False
            finally:
                i2c.unlock()
        
        # Try to initialize the OLED display
        print(f"  Initializing OLED at 0x{oled_address:02X}...")
        try:
            # Try 128x64 first (most common)
            display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=oled_address)
            print("  [OK] OLED initialized (128x64)")
        except Exception as e1:
            print(f"  128x64 failed: {e1}")
            # Try 128x32
            try:
                display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=oled_address)
                print("  [OK] OLED initialized (128x32)")
            except Exception as e2:
                print(f"  128x32 failed: {e2}")
                if mux:
                    mux.close()
                    mux = None
                return False
        
        # Clear the display and show test message
        display.fill(0)
        display.text('Screen on', 0, 0, 1, font_name=FONT_PATH)
        display.show()
        
        print("[OK] OLED display initialized successfully!")
        if use_multiplexer:
            print(f"     - Through multiplexer channel {oled_channel}")
        return True
        
    except Exception as e:
        print(f"[X] OLED display initialization failed: {e}")
        import traceback
        traceback.print_exc()
        if mux:
            try:
                mux.close()
            except:
                pass
            mux = None
        return False

def ensure_channel_selected():
    """Ensure the OLED channel is selected before operations"""
    global mux, oled_channel
    if mux and oled_channel is not None:
        mux.select_channel(oled_channel)

def list_display_methods():
    if display is None:
        print("Display not initialized.")
        return

    # List available methods and attributes of the display object
    methods = dir(display)
    print("Available methods and attributes:")
    for method in methods:
        print(method)

def draw_rectangle(x, y, width, height, color):
    """Draw a rectangle (for demonstration purposes)"""
    # Create an empty image buffer (assuming size 128x64, you can adjust this)
    img_width, img_height = 128, 64
    image = Image.new('1', (img_width, img_height), color=0)  # Monochrome, background black
    
    # Create a drawing object
    draw = ImageDraw.Draw(image)
    
    # Draw the rectangle (color can be 0 for black or 1 for white in monochrome mode)
    draw.rectangle([x, y, x + width, y + height], outline=color, fill=None)
    
    print("icon", x, y)
    return image

def update_display(header=None, text=None, y_start=16, line_height=10, icon=None):
    """
    Update the OLED display with text and optional icon.
    
    Args:
        header (str): Header text to display at top
        text (str): Body text (will wrap automatically)
        y_start (int): Starting Y position for body text
        line_height (int): Height between lines
        icon (str): Icon type ('square', 'rectangle', etc.)
    """
    if display is None:
        print("Display not initialized.")
        return

    # Ensure multiplexer channel is selected
    ensure_channel_selected()
    
    # Clear the whole display initially if header or text are provided
    if header or text:
        display.fill(0)
    
    # Display header if provided
    if header:
        display.text(header, 0, 0, 1, font_name=FONT_PATH)  # Specify font path
    
    # Display text if provided
    if text:
        max_line_length = 16  # Adjust based on your font and display width
        lines = [text[i:i + max_line_length] for i in range(0, len(text), max_line_length)]
        y = y_start
        for line in lines:
            display.text(line, 0, y, 1, font_name=FONT_PATH)   # Display each line at the appropriate y position
            y += line_height  # Move to the next line position
            if y + line_height > 64:  # Stop if we exceed the display height
                break
            
    # Draw icon if provided
    if icon == 'square': 
        draw_rectangle(24, 22, 32, 32, color=1)  # Draw a square (32x32) starting at (16,10)
    elif icon == 'rectangle':
        draw_rectangle(16, 10, 60, 30, color=1)  # Draw a rectangle (60x30) starting at (16,10)
        
    display.show()

def close_display():
    """Clean up resources when done"""
    global display, mux, oled_channel
    
    if display:
        try:
            display.fill(0)
            display.show()
        except:
            pass
    
    if mux:
        try:
            mux.select_channel(None)  # Disable all channels
            mux.close()
        except:
            pass
        mux = None
    
    oled_channel = None
    display = None
    print("OLED display closed")

# Example usage
if __name__ == "__main__":
    # Initialize with multiplexer (auto-detect channel)
    if initialize_display(use_multiplexer=True, channel=None):
        update_display(
            header="System",
            text="Starting...",
            icon='rectangle'
        )
        time.sleep(2)
        
        # Clean up
        close_display()
    else:
        print("Failed to initialize the display. Cannot display text.")
