from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pyjq',
      version='0.4',
      description="Tool used for converting jiffies from iptables xt_recent into timestamps.",
      long_description=readme(),
      classifiers=['Development Status :: 5 - Production/Stable',
                  'License :: OSI Approved :: BSD License',
                  'Programming Language :: Python :: 3'],
      url='https://github.com/peppelinux/pyjq',
      author='Giuseppe De Marco',
      author_email='demarcog83@gmail.com',
      license='BSD',
      scripts=['pyjq'],
      # packages=['iptables_xt_recent_parser'],
      install_requires=['pytz'],
     )