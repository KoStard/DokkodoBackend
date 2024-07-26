import os
from anthropic import Anthropic
import configparser

config = configparser.ConfigParser()
config_path = "/Users/kostard/.config/multillmchat/config.ini"
config.read(config_path)

def get_anthropic_client():
    api_key=config["ANTHROPIC"]["api_key"]
    return Anthropic(api_key=api_key)