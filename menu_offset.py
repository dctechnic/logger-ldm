
class MenuOffset:
    def __init__(self, title, num_digits=4, value_callback=None, callback=None):
        self.title = title

        # TODO: implement if we should render a title.. can be done, by adding a noop option to the option list?

        self.lcd = None
        self.options = []
        self.parent_menu = None
        self.callback = callback
        self.value = 0;
        self.value_cb = value_callback;
        self.num_digits = num_digits
        # We start on the first option by default (not 0 to prevent ZeroDivision errors )
        self.focus = num_digits
        self.viewport = None
        self.active = False


    # Starts the menu, used at root level to start the interface.
    # Or when navigating to a submenu or parten
    def start(self, lcd):

        self.lcd = lcd  # Assign the LCD to the menu.
        self.columns = lcd.num_columns  # Get the columns of the LCD
        self.lines = lcd.num_lines  # And the line
        self.active = True  # Set the screen as active
        self.value = self.value_cb()

        self.render()
        return self

    # Renders the menu, also when refreshing (when changing select)
    def render(self):
        # We only render the active screen, not the others

        self.lcd.clear()
        self.lcd.move_to(0, 0)
        
        self.lcd.putstr(self.title[: self.columns - 1])
        self.lcd.move_to(0, 1)
        self.lcd.putstr(("%+0" + str(self.num_digits+1) + "d") % (self.value))
        self.lcd.move_to(self.focus, 2)
        self.lcd.putchar('^')

        #self._render_cursor()
        #self._render_options()

    # Focus on the next option in the menu
    def focus_prev(self):
        
        if (self.focus == 0):
            self.value = self.value * -1
            self.render()
            return
        
        temp = list(("%+0" + str(self.num_digits+1) + "d") % (self.value))
        x = int(temp[self.focus]);
        x = x + 1;
        if (x > 9):
            x = 0
        temp[self.focus] = str(x)
        
        self.value = int("".join(temp))
        
        self.render()

    # Focus on the previous option in the menu
    def focus_next(self):
        if (self.focus == 0):
            self.value = self.value * -1
            self.render()
            return
        temp = list(("%+0" + str(self.num_digits+1) + "d") % (self.value))
        x = int(temp[self.focus]);
        x = x - 1;
        if (x < 0):
            x = 9
        temp[self.focus] = str(x)
        
        self.value = int("".join(temp))
        
        self.render()



    # Focus on the option n in the menu
    def focus_set(self, n):
        self.focus = n
        self.render()

    # Choose the item on which the focus is applied
    def choose(self):
        self.focus -= 1
        # Wrap around
        if (self.focus < 0):
            self.focus = self.num_digits
        self.render();
        
        return self # Start the submenu or parent

    # Navigate to the parent (if the current menu is a submenu)
    def parent(self):
        if self.parent_menu:
            self.active = False
            self.callback(self.value)
            return self.parent_menu.start(self.lcd)

