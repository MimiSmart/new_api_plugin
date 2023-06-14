from distutils.core import setup, Extension

sniffer = Extension('sniffer', sources=['sniffer.c'])
setup(name='Sniffer', version='1.0', description='Sniffer UDP packets', ext_modules=[sniffer])
