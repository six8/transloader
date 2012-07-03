try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def main():

    setup(
        name = 'transloader',
        packages=['transloader'],
        package_dir = {'transloader':'transloader'},
        version = open('VERSION.txt').read().strip(),
        author='Mike Thornton',
        author_email='six8@devdetails.com',
        url='http://github.com/six8/transloader',
        download_url='http://github.com/six8/transloader',
        keywords=['transloadit'],
        license='MIT',
        description='A transloadit client',
        classifiers = [
            "Programming Language :: Python",
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        long_description=open('README.rst').read(),
    )

if __name__ == '__main__':
    main()