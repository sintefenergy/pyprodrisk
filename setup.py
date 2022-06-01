from distutils.core import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')


setup(name='pyprodrisk',
      version='1.0.0',
      author='SINTEF Energy Research',
      description='Python interface to ProdRisk',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=['pyprodrisk',
                'pyprodrisk.helpers',
                'pyprodrisk.prodrisk_core'],
      package_dir={'pyprodrisk': 'pyprodrisk',
                   'pyprodrisk.helpers': 'pyprodrisk/helpers',
                   'pyprodrisk.prodrisk_core': 'pyprodrisk/prodrisk_core'},
      url='http://www.sintef.no/programvare/ProdRisk',
      project_urls={
          'Documentation': 'https://prodrisk.sintef.energy/documentation/tutorials/pyprodrisk/',
          'Source': 'https://github.com/sintef-energy/pyprodrisk',
          'Tracker': 'https://prodrisk.sintef.energy/tickets',
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows',
      ],
      author_email='support.energy@sintef.no',
      license='MIT',
      python_requires='>=3.7',
      install_requires=['pandas', 'numpy', 'pybind11'])



