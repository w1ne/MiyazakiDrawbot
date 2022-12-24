import image2gcode
import aimage

def main():
    aimagePica = aimage.Aimage("Pikachu dancing on the snow", 256, 256, "YOUR_KEY_HERE")
    # get the image from aimage
    image = aimagePica.get_image()
    image.save("output_test.png")
    # image processing
    pic = image2gcode.Piture(image)
    pic.gray_scale()
    gcode = image2gcode.Gcode(pic, 200, 200)
    # generate gcode
    gcode.gen_gcode()
    # send gcode to the drawing machine
    gcode.send_gcode("/dev/ttyUSB0", 115200)

if __name__ == "__main__":
    main()