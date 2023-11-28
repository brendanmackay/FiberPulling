import tkinter as tk
from tkinter import Canvas
from math import pow
import json
import math

# This application generates a Bezier curve for use in arduino motor control with non linear acceleration
# ChatGPT was instrumental in producing this application quickly
class BezierCurveApp:
    def __init__(self, root):

        # Define constant for the frame size
        self.padding_y = 80
        self.padding_x = 80
        self.frame_size_x = 1200
        self.frame_size_y = 500
        self.y_lower_bound = 0
        self.x_lower_bound = 0
        self.y_upper_bound = self.frame_size_y - 2 * self.padding_y
        self.x_upper_bound = self.frame_size_x - 2 * self.padding_x

        # Create initial control points
        self.accel_points_1 = [(self.x_lower_bound, self.y_lower_bound), (self.x_lower_bound, self.y_upper_bound/6),
                               (self.x_upper_bound*4/10,  self.y_lower_bound/4), (self.x_upper_bound*9/20, self.y_upper_bound)]
        self.decel_points_1 = [(self.x_upper_bound * 11 / 20, self.y_upper_bound), (self.x_upper_bound*6/10,  self.y_lower_bound/4),
                               (self.x_upper_bound, self.y_upper_bound/6), (self.x_upper_bound, self.y_lower_bound)]

        # Copy of the points which will be scaled and saved to the JSON file
        self.display_accel_points_1 = self.accel_points_1.copy()
        self.display_decel_points_1 = self.decel_points_1.copy()

        self.accel_points_2 = [(self.x_lower_bound, self.y_upper_bound*0.1), (self.x_upper_bound / 8, self.y_lower_bound),
                               (self.x_upper_bound / 4,  self.y_lower_bound), (self.x_upper_bound*9/20, self.y_lower_bound)]
        self.decel_points_2 = [(self.x_upper_bound * 11 / 20, self.y_lower_bound), (self.x_upper_bound * 3 / 4, self.y_lower_bound),
                               (self.x_upper_bound*5/6, self.y_lower_bound), (self.x_upper_bound, self.y_upper_bound*0.1)]

        # Copy of the points which will be scaled and saved to the JSON file
        self.display_accel_points_2 = self.accel_points_2.copy()
        self.display_decel_points_2 = self.decel_points_2.copy()

        #Set Maximum speeds for initialization
        self.initial_max_velocity = 900
        self.initial_max_time = 5000


        # Create the control panel
        self.control_panel = tk.Frame(root)
        self.control_panel.pack(pady=10)

        # Add widgets to the control panel
        tk.Label(self.control_panel, text="Max Time (ms):").grid(row=0, column=0, padx=10)
        self.last_x_entry = tk.Entry(self.control_panel, width=5)
        self.last_x_entry.grid(row=0, column=1)
        self.last_x_entry.insert(0, str(self.initial_max_time))

        tk.Label(self.control_panel, text="Max Velocity (step/s):").grid(row=1, column=0, padx=10)
        self.last_y_entry = tk.Entry(self.control_panel, width=5)
        self.last_y_entry.grid(row=1, column=1)
        self.last_y_entry.insert(0, str(self.initial_max_velocity))

        self.update_button = tk.Button(self.control_panel, text="Update Final Conditions", command=self.update_display_control_points)
        self.update_button.grid(row=2, columnspan=3, pady=10)

        self.canvas = Canvas(root, bg="white", width=self.frame_size_x, height=self.frame_size_y)
        self.canvas.pack(pady=20)

        self.draw_grid()

        # Initialize control points on the screen with distinct tags
        self.init_control_points()

        # Initialize functionality for grabbing and dragging points
        self.canvas.tag_bind("point", "<Button-1>", self.on_point_click)
        self.canvas.tag_bind("point", "<B1-Motion>", self.on_point_drag)

        # Add a StringVar to hold the text for the label
        self.accel_points_1_text = tk.StringVar()
        self.decel_points_1_text = tk.StringVar()
        self.accel_points_2_text = tk.StringVar()
        self.decel_points_2_text = tk.StringVar()
        self.update_point_position_text()

        # Create labels for displaying acceleration points
        self.accel_points_label_1 = tk.Label(self.control_panel, textvariable=self.accel_points_1_text,
                                             font=("Arial", 16, "bold"))
        self.accel_points_label_2 = tk.Label(self.control_panel, textvariable=self.accel_points_2_text,
                                             font=("Arial", 16, "bold"))


        # Create labels for displaying deceleration points
        self.decel_points_label_1 = tk.Label(self.control_panel, textvariable=self.decel_points_1_text,
                                             font=("Arial", 16, "bold"))
        self.decel_points_label_2 = tk.Label(self.control_panel, textvariable=self.decel_points_2_text,
                                             font=("Arial", 16, "bold"))
        self.accel_points_label_1.grid(row=0, column=4, padx=40, pady=10)
        self.decel_points_label_1.grid(row=1, column=4, padx=40, pady=10)
        self.accel_points_label_2.grid(row=2, column=4, padx=40, pady=10)
        self.decel_points_label_2.grid(row=3, column=4, padx=40, pady=10)

        # Appropriately scale points
        self.update_display_control_points()
        self.update_display_control_points()

        # Draw the initial Bezier curves
        self.draw_curve(self.accel_points_1, "acc_curve1", "blue")

        # Draw the deceleration curve 1
        self.draw_curve(self.decel_points_1, "dec_curve1", "blue")

        # Draw the acceleration curve 2
        self.draw_curve(self.accel_points_2, "acc_curve2", "purple")

        # Draw the deceleration curve 2
        self.draw_curve(self.decel_points_2, "dec_curve2", "purple")

        # Add this in the __init__ method
        self.line_between_curves_1 = self.canvas.create_line(0, 0, 0, 0, fill="blue", width=4)

        # Add this in the __init__ method
        self.line_between_curves_2 = self.canvas.create_line(0, 0, 0, 0, fill="purple", width=4)

        # Usage example for draw_line_between_curves_1
        self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)

        # Usage example for draw_line_between_curves_2
        self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)

    def init_control_points(self):
        # Initialize control points for acceleration curve (curve1)
        for idx, point in enumerate(self.accel_points_1):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="blue",
                                    tags=(f"acc_curve1_{idx}", "point"))

        # Initialize control points for deceleration curve (curve2)
        for idx, point in enumerate(self.decel_points_1):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="blue",
                                    tags=(f"dec_curve1_{idx}", "point"))

        for idx, point in enumerate(self.accel_points_2):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="purple",
                                    tags=(f"acc_curve2_{idx}", "point"))

        # Initialize control points for deceleration curve (curve2)
        for idx, point in enumerate(self.decel_points_2):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="purple",
                                    tags=(f"dec_curve2_{idx}", "point"))

    def update_point_position_text(self):
        # Update the StringVar with the current positions of the display_accel_points
        accel_positions_1 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_accel_points_1])
        self.accel_points_1_text.set(f"Accel Points Blue: {accel_positions_1}")

        # Update the StringVar with the current positions of the display_decel_points
        decel_positions_1 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_decel_points_1])
        self.decel_points_1_text.set(f"Decel Points Blue: {decel_positions_1}")

        # Update the StringVar with the current positions of the display_accel_points
        accel_positions_2 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_accel_points_2])
        self.accel_points_2_text.set(f"Accel Points Purple: {accel_positions_2}")

        # Update the StringVar with the current positions of the display_decel_points
        decel_positions_2 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_decel_points_2])
        self.decel_points_2_text.set(f"Decel Points Purple: {decel_positions_2}")

    def update_display_control_points(self):
        # Calculate the scaling factor based on the change in the final point's values
        x_scale_factor = int(self.last_x_entry.get()) / self.x_upper_bound if self.x_upper_bound != 0 else 1
        y_scale_factor = int(self.last_y_entry.get()) / self.y_upper_bound if self.y_upper_bound != 0 else 1

        # Apply the scaling factor to the internal control points
        self.display_accel_points_1 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.accel_points_1]
        self.display_decel_points_1 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.decel_points_1]
        self.display_accel_points_2 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.accel_points_2]
        self.display_decel_points_2 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.decel_points_2]


        # Update the label text to display the new scaled control points
        self.update_point_position_text()

    def adjust_y(self, v):
        return self.frame_size_y - v - self.padding_y # Assuming canvas height is 600

    def adjust_x(self, t):
        return t+self.padding_x

    def on_point_click(self, event):
        # Get the closest point to the click
        self.selected_point = self.canvas.find_closest(event.x, event.y)
        # Determine which curve the point belongs to based on tags
        tags = self.canvas.gettags(self.selected_point)
        if "acc_curve1" in tags:
            self.selected_curve = "acc_curve1"
        elif "dec_curve1" in tags:
            self.selected_curve = "dec_curve1"
        if "acc_curve2" in tags:
            self.selected_curve = "acc_curve2"
        elif "dec_curve2" in tags:
            self.selected_curve = "dec_curve2"
        else:
            self.selected_curve = None

    def on_point_drag(self, event):
        # Get the tags for the selected point
        tags = self.canvas.gettags(self.selected_point)

        # Check if any of the tags indicate which curve the point belongs to
        selected_curve = None
        for tag in tags:
            if tag.startswith("acc_curve1_"):
                selected_curve = "acc_curve1"
                break
            elif tag.startswith("dec_curve1_"):
                selected_curve = "dec_curve1"
                break
            elif tag.startswith("acc_curve2_"):
                selected_curve = "acc_curve2"
                break
            elif tag.startswith("dec_curve2_"):
                selected_curve = "dec_curve2"
                break

        # If selected_curve is still None, exit the method
        if selected_curve is None:
            return

        # Extract the index from the tag
        index = int(tags[0].split('_')[2])

        if index == 0 or index == 3:
            if (event.x - self.padding_x < self.y_lower_bound or self.adjust_y(event.y) < self.x_lower_bound
                    or event.x - self.padding_y > self.x_upper_bound or self.adjust_y(event.y) > self.y_upper_bound):
                return

        # Handle dragging for the specific curve
        if selected_curve == "acc_curve1":
            # Logic for updating acceleration points
            self.update_points(event, index, self.accel_points_1, "acc_curve1", "blue", self.draw_line_between_curves_1)
            self.draw_curve(self.accel_points_1, "acc_curve1", "blue")
            self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)
            self.update_display_control_points()
        elif selected_curve == "dec_curve1":
            # Logic for updating deceleration points
            self.update_points(event, index, self.decel_points_1, "dec_curve1", "blue", self.draw_line_between_curves_1)
            self.draw_curve(self.decel_points_1, "dec_curve1", "blue")
            self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)
            self.update_display_control_points()
        elif selected_curve == "acc_curve2":
            # Logic for updating deceleration points
            self.update_points(event, index, self.accel_points_2, "acc_curve2", "purple",
                               self.draw_line_between_curves_2)
            self.draw_curve(self.accel_points_2, "acc_curve2", "purple")
            self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)
            self.update_display_control_points()
        elif selected_curve == "dec_curve2":
            # Logic for updating deceleration points
            self.update_points(event, index, self.decel_points_2, "dec_curve2", "purple",
                               self.draw_line_between_curves_2)
            self.draw_curve(self.decel_points_2, "dec_curve2", "purple")
            self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)
            self.update_display_control_points()

    def draw_line_between_curves(self, accel_points, decel_points, line_between):
        # Get the last point of the acceleration curve
        last_accel_point = accel_points[-1]
        # Get the first point of the deceleration curve
        first_decel_point = decel_points[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(line_between, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def draw_line_between_curves_1(self):
        # Get the last point of the acceleration curve (curve1)
        last_accel_point = self.accel_points_1[-1]
        # Get the first point of the deceleration curve (curve2)
        first_decel_point = self.decel_points_1[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(self.line_between_curves_1, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def draw_line_between_curves_2(self):
        # Get the last point of the acceleration curve (curve1)
        last_accel_point = self.accel_points_2[-1]
        # Get the first point of the deceleration curve (curve2)
        first_decel_point = self.decel_points_2[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(self.line_between_curves_2, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def update_points(self, event, index, points, curve_tag, color, line_between_func):
        if 0 <= index < len(points):
            adjusted_y = self.adjust_y(event.y)
            points[index] = (event.x - self.padding_x, adjusted_y)
            # Update the visual representation of the control point
            self.canvas.coords(f"{curve_tag}_{index}", event.x - 10, event.y - 10, event.x + 10, event.y + 10)
        self.draw_curve(points, curve_tag, color)
        line_between_func()

    def draw_curve(self, points, curve_tag, color):
        self.canvas.delete(curve_tag)  # Delete the old curve

        # Drawing logic for the curve
        curve_points = []
        for i in range(0, 1001, 5):
            t = i / 1000
            x, y = self.calculate_bezier(t, points)  # Pass points
            curve_points.extend([self.adjust_x(x), self.adjust_y(y)])

        # Draw the new Bezier curve with the specified tag and color
        self.canvas.create_line(*curve_points, fill=color, tags=curve_tag, width=4)

    def calculate_bezier_points(self, control_points):
        curve_points = []
        for t in self.frange(0, 1, 0.01):
            x, y = self.calculate_bezier_point(t, control_points)
            curve_points.append((self.adjust_x(x), self.adjust_y(y)))
        return curve_points


    def binomial_coefficient(self, n, k):
        # Calculate the binomial coefficient
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

    def calculate_bezier(self, t, points):
        # points is either self.accel_points or self.decel_points
        x = 0
        y = 0
        n = len(points) - 1
        for i, point in enumerate(points):
            B = (pow(1 - t, n - i) * pow(t, i)) * self.combination(n, i)
            x += point[0] * B
            y += point[1] * B
        return x, y

    def combination(self, n, k):
        from math import factorial
        return factorial(n) / (factorial(k) * factorial(n - k))

    def draw_grid(self, spacing=50):
        # Draw horizontal grid lines
        for i in range(0, self.frame_size_y, spacing):
            self.canvas.create_line(self.padding_x, i, self.frame_size_x - self.padding_x, i, fill="#ddd")

        # Draw vertical grid lines
        for i in range(0, self.frame_size_x, spacing):
            self.canvas.create_line(i, self.padding_y, i, self.frame_size_y - self.padding_y, fill="#ddd")

        # Draw horizontal grid lines at the upper and lower bounds
        self.canvas.create_line(self.padding_x, self.padding_y, self.frame_size_x - self.padding_x, self.padding_y, fill="#ddd")
        self.canvas.create_line(self.padding_x, self.frame_size_y - self.padding_y, self.frame_size_x - self.padding_x, self.frame_size_y - self.padding_y, fill="#ddd")

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


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cubic Bezier Curve Editor")
    app = BezierCurveApp(root)
    root.mainloop()
