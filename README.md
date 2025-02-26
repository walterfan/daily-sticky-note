# Daily Sticky Note

My sticky note app for daily work.

## Prerequisites

* python 3.10+
* brew install upx  (optional)
* brew install pyinstaller (optional)

### install dependencies

```bash
pip install -r requirements.txt
```

## configuration

* change etc/sticky_note.yaml

for the api key of LLM, you can set the environment variables as below

```
export LLM_API_KEY="xxx"
```

## usage

```shell
./app/sticky_note.py [-f <config_file> -t <template_name>]
```
![snapshot](./doc/snapshot.png)

## config
* [sticky_note.yaml](./etc/sticky_note.yaml)
```shell
vi ./etc/sticky_note.yaml
```

* [prompt_template.yaml](./etc/prompt_template.yaml)
```shell
vi ./etc/prompt_template.yaml
```