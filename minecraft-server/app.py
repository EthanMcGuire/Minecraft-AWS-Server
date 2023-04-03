#!/usr/bin/env python3
import os

import aws_cdk as cdk

from minecraft_server.minecraft_server_stack import MinecraftServerStack


app = cdk.App()
MinecraftServerStack(app, "MinecraftServerStack", env=cdk.Environment(account='352387159701', region='us-east-1'))

app.synth()
