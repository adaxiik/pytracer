#!/usr/bin/env python3
from pytracer.pytracer import PyTracer, Arch
import typer


def main(arch: Arch = Arch.CPU):
    PyTracer(arch=arch,render_resolution_factor=0.8).run()


if __name__ == "__main__":
    typer.run(main)