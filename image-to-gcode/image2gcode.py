import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import potrace
import serial
import time
import argparse

class Piture:
    def __init__(self, image):
        self.img = np.array(image)
        self.heights, self.width, self.channels = self.img.shape

    # convert to gray scale
    def gray_scale(self):
        print("RBG to gray scale conversion...")
        PILimage = Image.fromarray(np.uint8(self.img)).convert("RGB")
        PILimage = PILimage.convert("L")
        self.img = np.array(PILimage).astype(bool)
        return self.img


class Gcode:
    def __init__(self, picture, x_max, y_max):
        self.gcode = []
        self.x_max = x_max
        self.y_max = y_max
        # normalize for drawing machine
        self.ratio = self.x_max / max(picture.width, picture.heights)
        self.picture = picture

        # gcode parameters
        self.gcode_homing_command = "$H"
        self.gcode_servo_off = "M05"
        self.gcode_pen_up = "M03 S15"
        self.gcode_pen_down = "M03 S50"
        self.gcode_pre = "G21"
        self.gcode_post = self.gcode_homing_command
        self.gcode_move_line_no_tool = "G0"
        self.gcode_move_line = "G1"
        self.gcode_set_feedrate = "G1 F12000.0"
        self.gcode_coord = "X%.4f Y%.4f"

    # Generate Gcode
    def gen_gcode(self):
        print("Generating gcode...")
        bmp = potrace.Bitmap(self.picture.img)
        path = bmp.trace()
        self.gcode.append(self.gcode_homing_command)  # go home
        self.gcode.append(self.gcode_set_feedrate)    # feedrate needs to be set once (modal command)
        self.gcode.append(self.gcode_pre)
        self.gcode.append(self.gcode_pen_up)  # make sure pen is up
        for curve in path:
            self.gcode.append(self.gcode_pen_up)
            self.gcode.append(
                self.gcode_move_line_no_tool
                + " "
                + self.gcode_coord
                % (curve.start_point[0] * self.ratio, curve.start_point[1] * self.ratio)
            )  # Move to the starting point for a curve
            self.gcode.append(self.gcode_pen_down)
            for segment in curve:
                if segment.is_corner:
                    self.gcode.append(
                        self.gcode_move_line
                        + " "
                        + self.gcode_coord
                        % (segment.c[0] * self.ratio, segment.c[1] * self.ratio)
                    )  # Move to corner start point
                    self.gcode.append(
                        self.gcode_move_line
                        + " "
                        + self.gcode_coord
                        % (
                            segment.end_point[0] * self.ratio,
                            segment.end_point[1] * self.ratio,
                        )
                    )  # Move to corner end point
                else:
                    self.gcode.append(
                        self.gcode_move_line
                        + " "
                        + self.gcode_coord
                        % (
                            segment.end_point[0] * self.ratio,
                            segment.end_point[1] * self.ratio,
                        )
                    )  # segment of bezier curve
        self.gcode.append(self.gcode_pen_up)
        self.gcode.append(self.gcode_servo_off) 
        self.gcode.append(self.gcode_post)
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
    # parse command line arguments, input image path, output gcode path, UART port, baud rate
    parser = argparse.ArgumentParser()

    parser.add_argument(# input image path  
        "-i",
        "--input",
        help="input image path",    
        default="input/download.jpeg",  # default input image path  
    )
    parser.add_argument(    # output gcode path
        "-o",
        "--output",
        help="output gcode path", 
        default="out/output_gcode.txt",   # default output gcode path
    )
    parser.add_argument(    # UART port
        "-p",
        "--port",   
        help="serial port",
        default="/dev/ttyUSB0",   # default UART port
    )  
    parser.add_argument(    # baud rate
        "-b",
        "--baud",   
        help="baud rate",   
        default=115200,   # default baud rate
    )   
    args = parser.parse_args()

    # input
    input_path = args.input
    output_name = args.output
    serial_port = args.port
    baud_rate = args.baud

    # drawing machine scaling parameters
    x_max = 200
    y_max = 200

    # image processing
    image = Image.open(input_path)
    pic = Piture(image)
    pic.gray_scale()
    gcode = Gcode(pic, x_max, y_max)
    gcode.gen_gcode()
    gcode.save_gcode(output_name)
    gcode.send_gcode(serial_port, baud_rate)

