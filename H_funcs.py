import numpy as np
from functools import partial

funcs = {}
default_args = {}


def func_generator(func, name):
    return partial(func, name=name)


def gaussian(t, args, name=""):
    sigma = args[name + "sigma"]
    mu = args[name + "mu"]
    t_on = args[name + "t_on"]
    t_off = args[name + "t_off"]
    return (t >= t_on) * (t < t_off) * np.exp(-((t-mu)/sigma)**2)
    # return np.exp(-(((t - mu) / sigma) ** 2))


funcs["gaussian"] = gaussian
gauss_args = {"sigma": 0.5, "mu": 2, "t_on": 1, "t_off": 3}
default_args["gaussian"] = gauss_args


def switch(t, args, name=""):
    t_on = args[name + "t_on"]
    t_off = args[name + "t_off"]
    return (t >= t_on) * (t < t_off) * 1


funcs["switch"] = switch
switch_args = {"t_on": 1, "t_off": 3}
default_args["switch"] = switch_args

# args = {'bt_on': 1, 'bt_off': 3}

# tlist = np.linspace(0, 5, 100)
# g1 = func_generator(switch, 'b')
# y = g1(tlist, args)
# print(y)
