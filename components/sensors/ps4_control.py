import subprocess
import time
from pyPS4Controller.controller import Controller

# Helper function to check for connected Bluetooth devices
def is_bluetooth_device_connected():
   # Check connected devices with a slight delay
    time.sleep(1)  # Allow some time for the system to register connections
    result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error checking devices: {result.stderr}")
        return False

    print("Connected devices output:\n", result.stdout)  # Debug output

    # Check for the PS4 controller name in the output
    return any("Wireless Controller" in line for line in result.stdout.split('\n'))

def request_bluetooth_pairing():
    print("No Bluetooth device detected. Please connect your PS4 controller.")
    # Optionally, add commands to initiate pairing, like:
    # subprocess.run(['bluetoothctl', 'scan', 'on'])
    # subprocess.run(['bluetoothctl', 'pair', '<controller_mac_address>'])
    # subprocess.run(['bluetoothctl', 'trust', '<controller_mac_address>'])
    # subprocess.run(['bluetoothctl', 'connect', '<controller_mac_address>'])


class MyController(Controller):
    def __init__(self, interface, connecting_using_ds4drv, on_input_change=None):
        # Perform Bluetooth check inside the constructor
        if is_bluetooth_device_connected():
            print("Bluetooth device connected.")
        else:
            request_bluetooth_pairing()
            raise ConnectionError("No Bluetooth device connected. Please pair your PS4 controller.")
        
        # Initialize the controller normally if Bluetooth is connected
        super().__init__(interface=interface, connecting_using_ds4drv=connecting_using_ds4drv)
        self.on_input_change = on_input_change
        self.deadzone = 20000  # Define a deadzone for the sticks (adjust this value as needed)
    
    def on_R3_x_at_rest(self):
        # Overriding to prevent unwanted prints
        if callable(self.on_input_change):
            self.on_input_change('R3_rest')    


    def on_L3_y_at_rest(self):
        # Overriding to prevent unwanted prints
        if callable(self.on_input_change):
            self.on_input_change('L3_rest')    

    def on_up_arrow_press(self):
        print("up arrow pressed")
        if callable(self.on_input_change):
            self.on_input_change('on_up_arrow_press')

    def on_up_arrow_release(self):
        print("up_arrow released")

    def on_down_arrow_press(self):
        print("up arrow pressed")
        if callable(self.on_input_change):
            self.on_input_change('on_down_arrow_press')

    def on_up_down_arrow_release(self):
        print("on_down_arrow released")


    def on_left_arrow_press(self):
        print("left arrow pressed")
        if callable(self.on_input_change):
            self.on_input_change('on_left_arrow_press')

    def on_right_arrow_press(self):
        print("right arrow pressed")
        if callable(self.on_input_change):
            self.on_input_change('on_right_arrow_press')

    def on_left_right_arrow_release(self):
        print("left arrow released")    
                
    def on_x_press(self):
        print("X button pressed")
        if callable(self.on_input_change):
            self.on_input_change('x_press')

    def on_x_release(self):
        print("X button released")
        
    def on_circle_press(self):
        print("Circle button pressed")
        if callable(self.on_input_change):
            self.on_input_change('circle_press')

    def on_circle_release(self):
        print("Circle button released")

    def on_triangle_press(self):
        print("Triangle button pressed")
        if callable(self.on_input_change):
            self.on_input_change('triangle_press')

    def on_triangle_release(self):
        print("Triangle button released")

    def on_square_press(self):
        print("Square button pressed")
        if callable(self.on_input_change):
            self.on_input_change('square_press')
    def on_square_release(self):
        print("Square button released")
        
    
    def on_L1_press(self):
        print(f"L1 pressed")
        if callable(self.on_input_change):
            self.on_input_change('L1_press')

    def on_R1_press(self):
        print(f"R1 pressed")
        if callable(self.on_input_change):
            self.on_input_change('R1_press')    

    def on_L2_press(self, value):
        print(f"L2 pressed with pressure {value}")
        if callable(self.on_input_change):
            self.on_input_change('L2_press', value)

    def on_R2_press(self, value):
        print(f"R2 pressed with pressure {value}")
        if callable(self.on_input_change):
            self.on_input_change('R2_press', value)

    def on_L3_left(self, value):
        if abs(value) > self.deadzone:  # Ignore small movements within the deadzone
            print(f"L3 stick moved left with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('L3_left', value)

    def on_L3_x_at_rest(self):

        if callable(self.on_input_change):
            self.on_input_change('L3_rest')
    
    def on_R3_y_at_rest(self):

        if callable(self.on_input_change):
            self.on_input_change('R3_rest')

            

    def on_L3_right(self, value):
        if abs(value) > self.deadzone:
            print(f"L3 stick moved right with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('L3_right', value)

    def on_L3_up(self, value):
        if abs(value) > self.deadzone:
            print(f"L3 stick moved up with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('L3_up', value)

    def on_L3_down(self, value):
        if abs(value) > self.deadzone:
            print(f"L3 stick moved down with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('L3_down', value)

    def on_R3_left(self, value):
        if abs(value) > self.deadzone:
            print(f"R3 stick moved left with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('R3_left', value)

    def on_R3_right(self, value):
        if abs(value) > self.deadzone:
            print(f"R3 stick moved right with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('R3_right', value)

    def on_R3_up(self, value):
        if abs(value) > self.deadzone:
            print(f"R3 stick moved up with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('R3_up', value)            

    def on_R3_down(self, value):
        if abs(value) > self.deadzone:
            print(f"R3 stick moved down with value {value}")
            if callable(self.on_input_change):
                self.on_input_change('R3_down', value)                 


if __name__ == "__main__":
    controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
    controller.listen()
