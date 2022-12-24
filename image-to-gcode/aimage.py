# A script to interact with stability_sdk.client, it sends a request to the dreamstudio server with szie of the image and prompt and returns generated image

import stability_sdk.client as client
import os
import sys
import argparse
import json
import requests
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import io
import os
import warnings
from PIL import Image

class Aimage:
    def __init__(self, prompt, W, H, key):
        self.prompt = prompt
        self.W = W
        self.H = H
        self.key = key

    def get_image(self):
        stability_api = client.StabilityInference(
            key=self.key,
            verbose=True,
        )
        answers = stability_api.generate(
            prompt=self.prompt + "Line Drawing",
        )

        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again."
                    )
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(io.BytesIO(artifact.binary))
                    return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", type=str, default="Hello World!", help="prompt for the image"
    )
    parser.add_argument("--W", type=int, default=256, help="Width of the image")
    parser.add_argument("--H", type=int, default=256, help="Height of the image")
    parser.add_argument(
        "--output", type=str, default="output.png", help="output file name"
    )
    parser.add_argument("--key", type   =str, default="YOUR_KEY_HERE", help="API key")
    
    args = parser.parse_args()
    prompt = args.prompt
    W = args.W
    H = args.H
    key = args.key
    output = args.output

    aimage = Aimage(prompt, W, H, key)
    imagePIL = aimage.get_image()
    # save the image with PIL   
    imagePIL.save(output)

if __name__ == "__main__":
    main()
