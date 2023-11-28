import tkinter as tk
from tkinter import Canvas
from math import pow
import json

# This application generates a Bezier curve for use in arduino motor control with non linear acceleration
# ChatGPT was instrumental in producing this application quickly
class BezierCurveApp:
    def __init__(self, root):

        # Define constant for the frame size
        self.padding_y = 80
        self.padding_x = 80
        self.frame_size_x = 800
        self.frame_size_y = 500
        self.y_lower_bound = 0
        self.x_lower_bound = 0
        self.y_upper_bound = self.frame_size_y - 2 * self.padding_y
        self.x_upper_bound = self.frame_size_x - 2 * self.padding_x

        # Create initial control points
        self.control_points = [(self.y_lower_bound, self.x_lower_bound), (self.x_upper_bound / 2, 1),
                               (self.x_upper_bound / 2, self.y_upper_bound - 1), (self.x_upper_bound, self.y_upper_bound)]

        # Copy of the points which will be scaled and saved to the JSON file
        self.display_control_points = self.control_points.copy()

        #Set Maximum speeds for initialization
        self.initial_max_velocity = 900
        self.initial_max_time = 5

        # Create the control panel
        self.control_panel = tk.Frame(root)
        self.control_panel.pack(pady=10)

        # Add widgets to the control panel
        tk.Label(self.control_panel, text="Total Time (s):").grid(row=0, column=0, padx=10)
        self.last_x_entry = tk.Entry(self.control_panel, width=5)
        self.last_x_entry.grid(row=0, column=1)
        self.last_x_entry.insert(0, self.initial_max_time)

        tk.Label(self.control_panel, text="Final Velocity (step/s):").grid(row=1, column=0, padx=10)
        self.last_y_entry = tk.Entry(self.control_panel, width=5)
        self.last_y_entry.grid(row=1, column=1)
        self.last_y_entry.insert(0, self.initial_max_velocity)

        self.update_button = tk.Button(self.control_panel, text="Update Final Conditions", command=self.update_final_conditions)
        self.update_button.grid(row=2, columnspan=3, pady=10)

        self.canvas = Canvas(root, bg="white", width=self.frame_size_x, height=self.frame_size_y)
        self.canvas.pack(pady=20)

        # Add a row for the maximum slope display
        self.max_slope_label = tk.Label(self.control_panel,font=("Arial", 18, "bold"))
        self.max_slope_label.grid(row=0, column=4, columnspan=3, pady=10)

        # Draw the x and y axes
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_lower_bound), width=4)  # x-axis
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_upper_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_upper_bound), width=4)  # x-axis
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_upper_bound), width=4)  # y-axis
        self.canvas.create_line(self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_upper_bound), width=4)  # y-axis


        # Label the x and y axes
        self.canvas.create_text(self.adjust_x(self.x_upper_bound/2), self.adjust_y(-20),
                                text="Time (ms)", font=("Arial", 20, "bold"))
        self.canvas.create_text(self.adjust_x(-20), self.adjust_y(self.y_upper_bound/2),
                                angle=90, text="Velocity (Step/s)", font=("Arial", 20, "bold"))



        # initialize the control points on the screen
        for idx, point in enumerate(self.control_points):
            # Convert the adjusted y-coordinate to canvas coordinate for drawing
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="blue",
                                    tags=(str(idx), "point"))

        # Draw the initial Bezier curve
        self.draw_curve()

        # Initialize functionality for grabbing and dragging points
        self.canvas.tag_bind("point", "<Button-1>", self.on_point_click)
        self.canvas.tag_bind("point", "<B1-Motion>", self.on_point_drag)

        # Add a StringVar to hold the text for the label
        self.point_position_text = tk.StringVar()
        self.update_point_position_text()

        # Create widgets for saving data to JSON
        self.point_position_label = tk.Label(self.control_panel, textvariable=self.point_position_text, font=("Arial", 16, "bold"))
        self.point_position_label.grid(row=1, column=4,padx=40, pady=10)
        self.save_button = tk.Button(self.control_panel, text="Save Points to JSON", command=self.save_to_json)
        self.save_button.grid(row=2, column=4, columnspan=3, pady=10)

        # Appropriately scale points
        self.update_final_conditions()
        self.update_display_control_points()

    def update_point_position_text(self):
        # Update the StringVar with the current positions of the display_control_points
        positions = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_control_points])
        self.point_position_text.set(f"Control Points: {positions}")

    def update_display_control_points(self):
        # Calculate the scaling factor based on the change in the final point's values
        x_scale_factor = int(self.last_x_entry.get()) / self.x_upper_bound if self.x_upper_bound != 0 else 1
        y_scale_factor = int(self.last_y_entry.get()) / self.y_upper_bound if self.y_upper_bound != 0 else 1

        # Apply the scaling factor to the internal control points
        self.display_control_points = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.control_points]

        # Update the label text to display the new scaled control points
        self.update_point_position_text()

    def update_final_conditions(self):
        # Calculate scaling factors
        x_scale_factor = int(self.last_x_entry.get()) / self.control_points[3][0]
        y_scale_factor = int(self.last_y_entry.get()) / self.control_points[3][1]

        # Update display_control_points using the scaling factors
        self.display_control_points = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.control_points]

        # Update the label text with display_control_points
        self.update_point_position_text()

        self.max_slope_label.config(text=f"Maximum Acceleration : {self.max_slope():.2f} steps/s²")

    def adjust_y(self, v):
        return self.frame_size_y - v - self.padding_y # Assuming canvas height is 600

    def adjust_x(self, t):
        return t+self.padding_x

    def on_point_click(self, event):
        # Get the closest point to the click
        self.selected_point = self.canvas.find_closest(event.x, event.y)

    def on_point_drag(self, event):

        index = int(self.canvas.gettags(self.selected_point)[0])  # Get the index from tags

        self.update_display_control_points()

        # Check if the selected point is the starting or ending point
        if index == 0 or index == 3:
            return

        if (event.x - self.padding_x < self.y_lower_bound or self.adjust_y(event.y) < self.x_lower_bound
                or event.x - self.padding_y > self.x_upper_bound or self.adjust_y(event.y) > self.y_upper_bound):
            return

        # Convert the y-coordinate for internal representation
        adjusted_y = self.adjust_y(event.y)

        # Use raw event.x for moving the control point on the canvas
        self.canvas.coords(self.selected_point, event.x - 10, event.y - 10, event.x + 10, event.y + 10)

        # Update control points list using the raw x and adjusted y coordinates
        self.control_points[index] = (event.x-self.padding_x, adjusted_y)

        # Redraw the curve and control lines
        self.draw_curve()

        # Update the label text after dragging a control point
        self.update_point_position_text()

    def draw_curve(self):
        # Clear existing curve and control lines
        self.canvas.delete("curve")
        self.canvas.delete("line")

        # Draw control lines
        for i in range(len(self.control_points) - 1):
            self.canvas.create_line(self.adjust_x(self.control_points[i][0]), self.adjust_y(self.control_points[i][1]),
                                    self.adjust_x(self.control_points[i + 1][0]),
                                    self.adjust_y(self.control_points[i + 1][1]),
                                    fill="gray", tags="line")

        # Collect all the curve points
        curve_points = []
        for i in range(0, 1001, 5):
            t = i / 1000
            x, y = self.calculate_bezier(t)
            curve_points.extend([self.adjust_x(x), self.adjust_y(y)])

        # Draw the Bezier curve using the collected points
        self.canvas.create_line(*curve_points, fill="red", tags="curve", width=4)

        # Update the displayed maximum slope
        self.max_slope_label.config(text=f"Maximum Acceleration : {self.max_slope():.2f} steps/s²")

    def calculate_bezier(self, t):
        x = 0
        y = 0
        n = len(self.control_points) - 1
        for i, point in enumerate(self.control_points):
            # Bernstein basis
            B = (pow(1 - t, n - i) * pow(t, i)) * self.combination(n, i)
            x += point[0] * B
            y += point[1] * B
        return x, y

    def calculate_bezier_derivative(self, t):
        dx = 0
        dy = 0
        n = len(self.display_control_points) - 1
        for i, point in enumerate(self.display_control_points):
            # Handle special cases
            if t == 0 and i == 0:
                B_prime = n - i
            elif t == 1 and i == n:
                B_prime = i
            else:
                B_prime = self.combination(n, i) * (
                            i * pow(t, i - 1) * pow(1 - t, n - i) - (n - i) * pow(t, i) * pow(1 - t, n - i - 1))
            dx += point[0] * B_prime
            dy += point[1] * B_prime
        return dx, dy

    def max_slope(self):
        max_slope_val = 0
        for i in range(0, 1001, 5):
            t = i / 1000
            dx, dy = self.calculate_bezier_derivative(t)
            slope = dy / dx if dx != 0 else float('inf')
            max_slope_val = max(max_slope_val, abs(slope))
        return max_slope_val

    def combination(self, n, k):
        from math import factorial
        return factorial(n) / (factorial(k) * factorial(n - k))

    def save_to_json(self):
        # Define the data structure to save
        data = {
            "control_points": self.display_control_points
        }

        # Choose a file name (can be changed as desired)
        filename = "bezier_points.json"

        # Save the data to the JSON file
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Control points saved to {filename}")




if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cubic Bezier Curve Editor")
    app = BezierCurveApp(root)
    root.mainloop()
