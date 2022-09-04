from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='remotesyn',
    version='0.2',
    description='Remote FPGA synthesis abstraction tool',
    long_description=long_description,
    author='Joppe Blondel',
    author_email='joppe@blondel.nl',
    download_url='',
    url='https://git.joppeb.nl/joppe/remotesyn',
    keywords = ['FPGA', 'Synthesis', 'Xilinx', 'ISE', 'Vivado',],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
  ],
    packages=['remotesyn'],
    licence='BSD Licence',
    install_requires=['paramiko'],
    scripts=['scripts/rbuild', 'scripts/rmbuild', 'scripts/rmserver']
)