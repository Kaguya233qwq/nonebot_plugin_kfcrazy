import setuptools

with open("README.md", "r", encoding="utf-8", errors="ignore") as f:
    long_description = f.read()
setuptools.setup(
    name='nonebot-plugin-kfcrazy',
    version='2.0.4',
    author='Kaguya233qwq',
    author_email='1435608435@qq.com',
    keywords=["pip", "nonebot2", "nonebot", "KFC", "v我50", "疯狂星期四", "肯德基"],
    url='https://github.com/Kaguya233qwq/nonebot_plugin_kfcrazy',
    description='''nonebot2 plugin kfcrazy''',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: Chinese (Simplified)"
    ],
    include_package_data=True,
    platforms="any",
    install_requires=[
        'httpx', 'nonebot2>=2.0.0-beta.1', 'nonebot-adapter-onebot>=2.0.0-beta.1'
    ])
