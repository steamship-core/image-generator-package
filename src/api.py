"""Description of your app."""
import uuid
from enum import Enum
from typing import Optional, Type, cast, Tuple, Dict, Any
import json
import openai
import urllib.request

import base64

import requests
from steamship import MimeTypes, SteamshipError, TaskState, Steamship
from steamship.data.plugin.prompt_generation_plugin_instance import PromptGenerationPluginInstance
from steamship.invocable import post, PackageService, InvocableResponse, Invocation, Config, InvocationContext


class ImageSize(str, Enum):
    square_256 = '256x256'
    square_1024 = '1024x1024'

class Background(str, Enum):
    woods = 'woods'
    beach = 'beach'

class Mood(str, Enum):
    dark = 'dark'
    light = 'light'

class Style(str, Enum):
     painting = "painting"
     neon = "neon"
     magazine = "magazine"


class ImageGeneratorPackage(PackageService):
    """Illustrates generating a DALL-E image."""

    class ImageGeneratorConfig(Config):
        openai_api_key: Optional[str] = ""

    config: ImageGeneratorConfig
    llm: PromptGenerationPluginInstance

    @classmethod
    def config_cls(cls) -> Type[Config]:
        return cls.ImageGeneratorConfig

    def __init__(
        self,
        client: Steamship = None,
        config: Dict[str, Any] = None,
        context: InvocationContext = None,
    ):
        super().__init__(client, config, context)
        openai.api_key = self.config.openai_api_key

    # Internal method returns the URL of the provided image
    def _generate_dalle_image(self, prompt: str, variables: Optional[dict] == None, size: ImageSize = ImageSize.square_1024) -> str:
        try:
            full_prompt = prompt.format(**(variables or {}))
        except KeyError as e:
            raise SteamshipError(
                message="Some variables in the prompt template were not provided.", error=e
            )

        # These args preserved as a reminder they can be interesting!
        # image=open("sunlit_lounge.png", "rb"),
        # mask=open("mask.png", "rb"),
        response = openai.Image.create(
            prompt=full_prompt,
            n=1,
            size=size.value
        )

        if 'data' not in response or not len(response['data']) or not response['data'][0]['url']:
            raise SteamshipError(
                message="DALL-E returned an empty response."
            )
        image_url = response['data'][0]['url']
        return image_url


    @post("generate")
    def generate(
        self,
        topic: str = "A smiling person", 
        mood: Mood = Mood.light, 
        style: Style = Style.magazine, 
        background: Background = Background.beach
    ) -> dict:

        pieces = [topic]

        if mood == Mood.dark:
            pieces.extend(["dark", "shadowy", "ominous light", "foreboding"])
        elif mood == Mood.light:
            pieces.extend(["light", "golden hour", "crisp"])

        if background == Background.woods:
            pieces.extend(["wooded background", "low depth of field", "trees in distance"])
        elif background == Background.beach:
            pieces.extend(["beach background", "low depth of field", "ocean in distance"])

        if style == Style.painting:
            pieces.extend(["highdef", "oil painting", "oil on canvas", "fine art"])
        elif style == Style.neon:
            pieces.extend(["highdef", "neon art", "dslr", "4k", "neon punk"])
        elif style == Style.neon:
            pieces.extend(["highdef", "4k", "Shot on a DSLR", "professional photo"])

        prompt = str(", ".join(pieces))
        url = self._generate_dalle_image(prompt, {})
        return {"image_url": url}


