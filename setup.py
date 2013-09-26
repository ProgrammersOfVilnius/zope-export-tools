from setuptools import setup

setup(
    name='zope-export-tools',
    version='0.2',
    maintainer='Marius Gedminas',
    maintainer_email='marius@pov.lt',
    description='Tools to work with a Zope 2 website',
    license='proprietary',
    py_modules=['unpack', 'z2writer', 'z2loader', 'pack', 'render'],
    zip_safe=False,
    install_requires=['Zope2'],
    entry_points=dict(
        console_scripts="""
        unpack-zexp = unpack:main
        pack-zexp = pack:main
        render = render:main
        """,
    ),
)
