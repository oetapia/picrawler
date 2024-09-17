from pyPS4Controller.controller import Controller

class MyController(Controller):
    def __init__(self, interface, connecting_using_ds4drv, on_input_change=None):
        super().__init__(interface=interface, connecting_using_ds4drv=connecting_using_ds4drv)
        self.on_input_change = on_input_change
        self.deadzone = 10000  # Define a deadzone for the sticks (adjust this value as needed)

    
    
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
