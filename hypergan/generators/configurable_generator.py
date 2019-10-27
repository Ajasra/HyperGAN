import tensorflow as tf
import hyperchamber as hc
import inspect
import copy
import os
import operator
from functools import reduce

from hypergan.ops.tensorflow.extended_ops import bicubic_interp_2d
from .base_generator import BaseGenerator
from hypergan.configurable_component import ConfigurableComponent

class ConfigurableGenerator(BaseGenerator, ConfigurableComponent):
    def __init__(self, gan, config, *args, **kw_args):
        ConfigurableComponent.__init__(self, gan, config,*args, **kw_args)
        BaseGenerator.__init__(self, gan, config, *args, **kw_args)
