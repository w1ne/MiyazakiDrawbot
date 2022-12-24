import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import potrace
import serial
import time


class Piture:
    def __init__(self, filepath):
        self.img = Image.open(filepath)
        self.img = np.array(self.img)
        self.heights, self.width, self.channels = self.img.shape

    # convert to gray scale
    def gray_scale(self):
        print("RBG to gray scale conversion...")
        PILimage = Image.fromarray(np.uint8(self.img)).convert("RGB")
        PILimage = PILimage.convert("L")
        self.img = np.array(PILimage)
        return self.img


class Gcode:
    def __init__(self, picture, x_max, y_max):
        self.gcode = []
        self.x_max = x_max
        self.y_max = y_max
        # normalize for drawing machine
        self.ratio = self.x_max / max(picture.width, picture.heights)
        self.picture = picture

    # Generate Gcode
    def gen_gcode(self):
        print("Generating gcode...")
        bmp = potrace.Bitmap(self.picture.img)
        path = bmp.trace()
        self.gcode.append(gcode_homing_command)  # go home
        self.gcode.append(gcode_set_feedrate)    # feedrate needs to be set once (modal command)
        self.gcode.append(gcode_pre)
        self.gcode.append(gcode_pen_up)  # make sure pen is up
        for curve in path:
            self.gcode.append(gcode_pen_up)
            self.gcode.append(
                gcode_move_line_no_tool
                + " "
                + gcode_coord
                % (curve.start_point.x * self.ratio, curve.start_point.y * self.ratio)
            )  # Move to the starting point for a curve
            self.gcode.append(gcode_pen_down)
            for segment in curve:
                if segment.is_corner:
                    self.gcode.append(
                        gcode_move_line
                        + " "
                        + gcode_coord
                        % (segment.c.x * self.ratio, segment.c.y * self.ratio)
                    )  # Move to corner start point
                    self.gcode.append(
                        gcode_move_line
                        + " "
                        + gcode_coord
                        % (
                            segment.end_point.x * self.ratio,
                            segment.end_point.y * self.ratio,
                        )
                    )  # Move to corner end point
                else:
                    self.gcode.append(
                        gcode_move_line
                        + " "
                        + gcode_coord
                        % (
                            segment.end_point.x * self.ratio,
                            segment.end_point.y * self.ratio,
                        )
                    )  # segment of bezier curve
        self.gcode.append(gcode_pen_up)
        self.gcode.append(gcode_post)
        return self.gcode

    # Export Gcode
    def save_gcode(self, output_name):
        with open(f"{output_name}_gcode.txt", "w") as f:
            for i in range(len(self.gcode)):
                f.write("%s\n" % self.gcode[i])

    def send_gcode(self, serial_port, speed):
        ser = serial.Serial(serial_port, speed)
        print("Opening Serial Port...")
        ser.write(str.encode("\r\n\r\n"))  # Just in case, wakeup grbl
        time.sleep(2)  # Wait to initialize the HW
        ser.flushInput()  # Flush startup text in serial input
        # Stream g-code
        for line in self.gcode:
            line = line.strip()  # Strip all EOL characters for streaming
            if line.isspace() == False and len(line) > 0:
                print("Sending:" + line)
                ser.write(str.encode(line + "\n"))  # Send g-code block
                grbl_out = ser.readline()  # Wait for response with carriage return
                print("Answer: " + grbl_out.strip().decode("utf-8"))
        ser.close()


if __name__ == "__main__":
    # image to process path and gcode output path
    input_path = "input/download.jpeg"
    output_name = "out/" + input_path.split("/")[1].split(".")[0]
    # gcode parameters
    gcode_homing_command = "$H"
    gcode_pen_up = "M05 S0"
    gcode_pen_down = "M03 S100"
    gcode_pre = "G21"
    gcode_post = gcode_homing_command
    gcode_move_line_no_tool = "G0"
    gcode_move_line = "G1"
    gcode_set_feedrate = "G1 F12000.0"
    gcode_coord = "X%.4f Y%.4f"
    # drawing maachine scaling parameters
    x_max = 200
    y_max = 200

    # image processing
    pic = Piture(input_path)
    pic.gray_scale()
    gcode = Gcode(pic, x_max, y_max)
    gcode.gen_gcode()
    gcode.save_gcode(output_name)
    gcode.send_gcode("/dev/ttyUSB0", 115200)

