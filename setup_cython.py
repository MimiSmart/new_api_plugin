# import multiprocessing
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import setup
from setuptools.extension import Extension

setup(
    name="new_api_plugin",
    version='0.100',
    packages=['new_api_plugin', 'new_api_plugin.items'],
    ext_modules=cythonize(
        [
            Extension("api_models", ["api_models.py"]),

            Extension("blinds", ["items/blinds.py"]),
            Extension("conditioner", ["items/conditioner.py"]),
            Extension("dimmer", ["items/dimmer.py"]),
            Extension("heating", ["items/heating.py"]),
            Extension("lamp", ["items/lamp.py"]),
            Extension("leak", ["items/leak.py"]),
            Extension("rgb", ["items/rgb.py"]),
            Extension("sensor", ["items/sensor.py"]),
            Extension("switch", ["items/switch.py"]),
            Extension("virtual", ["items/virtual.py"]),

            Extension("item", ["item.py"]),
            Extension("logic", ["logic.py"]),
            Extension("rest", ["rest.py"]),
            Extension("shclient", ["shclient.py"]),
            Extension("timeit", ["timeit.py"]),
            Extension("ws", ["ws.py"]),
            Extension("main", ["main.py"]),
        ],
        build_dir="build_cythonize",
        compiler_directives={
            'language_level': "3",
            'always_allow_keywords': True,
        },
        # options={
        #     'build_ext':
        #         {'parallel': multiprocessing.cpu_count()}
        # },
    ),
    cmdclass={'build_ext': build_ext}
)
